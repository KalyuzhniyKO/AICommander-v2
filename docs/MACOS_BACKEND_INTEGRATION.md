# macOS AICommander backend integration (minimal, paste-ready)

This guide provides **paste-ready Swift code** for integrating the existing backend CLI into the macOS app without backend redesign.

Backend commands used:

- `python -m backend.cli --run-post-judge-transition --run-folder <path>`
- `python -m backend.cli --read-post-judge-route --run-folder <path>`
- `python -m backend.cli --gui-health-status --run-folder <path>`

## Integration call points (exact app flow)

1. `OrchestrationController.swift`
   - after judge completion: call `runPostJudgeTransition(...)`
   - then call `readPostJudgeRoute(...)`
   - resolve and navigate route via `RouteResolver`
2. `StatusViewModel.swift`
   - refresh from `guiHealthStatus(...)`
3. `RunArtifacts.swift`
   - keep existing artifacts + optional `final_audit.json`

---

## 1) `BackendBridgeService.swift` (full file)

```swift
import Foundation

enum BackendBridgeError: Error, LocalizedError {
    case commandFailed(exitCode: Int32, stderr: String)
    case invalidUTF8

    var errorDescription: String? {
        switch self {
        case let .commandFailed(code, stderr):
            return "Backend CLI failed with exit code \(code): \(stderr)"
        case .invalidUTF8:
            return "Backend CLI returned non-UTF8 output"
        }
    }
}

/// Typed JSON value wrapper for payload sections with flexible shapes.
enum JSONValue: Decodable, Equatable {
    case string(String)
    case number(Double)
    case bool(Bool)
    case object([String: JSONValue])
    case array([JSONValue])
    case null

    init(from decoder: Decoder) throws {
        let container = try decoder.singleValueContainer()
        if container.decodeNil() {
            self = .null
        } else if let value = try? container.decode(Bool.self) {
            self = .bool(value)
        } else if let value = try? container.decode(Double.self) {
            self = .number(value)
        } else if let value = try? container.decode(String.self) {
            self = .string(value)
        } else if let value = try? container.decode([String: JSONValue].self) {
            self = .object(value)
        } else if let value = try? container.decode([JSONValue].self) {
            self = .array(value)
        } else {
            throw DecodingError.dataCorruptedError(in: container, debugDescription: "Unsupported JSON value")
        }
    }

    var stringValue: String? {
        if case let .string(value) = self { return value }
        return nil
    }
}

struct PostJudgeRoutePayload: Decodable {
    let status: String
    let finalVerdict: String
    let nextRoute: String
    let finalAuditPath: String

    enum CodingKeys: String, CodingKey {
        case status
        case finalVerdict = "final_verdict"
        case nextRoute = "next_route"
        case finalAuditPath = "final_audit_path"
    }
}

struct GuiHealthStatusPayload: Decodable {
    let providerStatus: [String: JSONValue]
    let directorRole: [String: JSONValue]
    let coderRole: [String: JSONValue]
    let reviewerRole: [String: JSONValue]
    let qaRole: [String: JSONValue]
    let judgeRole: [String: JSONValue]
    let finalAuditorRole: [String: JSONValue]
    let workspaceStatus: [String: JSONValue]
    let orchestrationStatus: [String: JSONValue]

    enum CodingKeys: String, CodingKey {
        case providerStatus = "provider_status"
        case directorRole = "director_role"
        case coderRole = "coder_role"
        case reviewerRole = "reviewer_role"
        case qaRole = "qa_role"
        case judgeRole = "judge_role"
        case finalAuditorRole = "final_auditor_role"
        case workspaceStatus = "workspace_status"
        case orchestrationStatus = "orchestration_status"
    }
}

final class BackendBridgeService {
    private let pythonExecutable: String
    private let backendWorkingDirectory: URL
    private let decoder = JSONDecoder()

    init(pythonExecutable: String = "python", backendWorkingDirectory: URL) {
        self.pythonExecutable = pythonExecutable
        self.backendWorkingDirectory = backendWorkingDirectory
    }

    func runPostJudgeTransition(runFolder: URL, executionMode: String? = nil) throws {
        var args = ["-m", "backend.cli", "--run-post-judge-transition", "--run-folder", runFolder.path]
        if let executionMode {
            args += ["--execution-mode", executionMode]
        }
        _ = try runRaw(arguments: args)
    }

    func readPostJudgeRoute(runFolder: URL) throws -> PostJudgeRoutePayload {
        let args = ["-m", "backend.cli", "--read-post-judge-route", "--run-folder", runFolder.path]
        return try runDecodable(arguments: args, as: PostJudgeRoutePayload.self)
    }

    func guiHealthStatus(runFolder: URL, executionMode: String? = nil) throws -> GuiHealthStatusPayload {
        var args = ["-m", "backend.cli", "--gui-health-status", "--run-folder", runFolder.path]
        if let executionMode {
            args += ["--execution-mode", executionMode]
        }
        return try runDecodable(arguments: args, as: GuiHealthStatusPayload.self)
    }

    private func runDecodable<T: Decodable>(arguments: [String], as type: T.Type) throws -> T {
        let data = try runRaw(arguments: arguments)
        return try decoder.decode(T.self, from: data)
    }

    private func runRaw(arguments: [String]) throws -> Data {
        let process = Process()
        process.currentDirectoryURL = backendWorkingDirectory
        process.executableURL = URL(fileURLWithPath: "/usr/bin/env")
        process.arguments = [pythonExecutable] + arguments

        let stdoutPipe = Pipe()
        let stderrPipe = Pipe()
        process.standardOutput = stdoutPipe
        process.standardError = stderrPipe

        try process.run()
        process.waitUntilExit()

        let stdoutData = stdoutPipe.fileHandleForReading.readDataToEndOfFile()
        let stderrData = stderrPipe.fileHandleForReading.readDataToEndOfFile()
        let stderrString = String(data: stderrData, encoding: .utf8) ?? ""

        guard process.terminationStatus == 0 else {
            throw BackendBridgeError.commandFailed(exitCode: process.terminationStatus, stderr: stderrString)
        }

        guard String(data: stdoutData, encoding: .utf8) != nil else {
            throw BackendBridgeError.invalidUTF8
        }

        return stdoutData
    }
}
```

---

## 2) `GuiHealthStatus.swift` (shared model file)

```swift
import Foundation

struct GuiHealthStatus {
    let providerSummary: String
    let workspaceSummary: String
    let orchestrationSummary: String

    static func fromPayload(_ payload: GuiHealthStatusPayload) -> GuiHealthStatus {
        let provider = payload.providerStatus["status"]?.stringValue ?? "unknown"
        let workspace = payload.workspaceStatus["status"]?.stringValue ?? "unknown"
        let orchestration = payload.orchestrationStatus["status"]?.stringValue ?? "unknown"

        return GuiHealthStatus(
            providerSummary: provider,
            workspaceSummary: workspace,
            orchestrationSummary: orchestration
        )
    }
}
```

---

## 3) `StatusViewModel.swift` update

```swift
import Foundation
import Combine

@MainActor
final class StatusViewModel: ObservableObject {
    @Published private(set) var guiHealthStatus: GuiHealthStatus?
    @Published private(set) var lastError: String?

    private let backendBridge: BackendBridgeService

    init(backendBridge: BackendBridgeService) {
        self.backendBridge = backendBridge
    }

    func refresh(runFolder: URL, executionMode: String? = nil) {
        do {
            let payload = try backendBridge.guiHealthStatus(runFolder: runFolder, executionMode: executionMode)
            guiHealthStatus = GuiHealthStatus.fromPayload(payload)
            lastError = nil
        } catch {
            lastError = error.localizedDescription
        }
    }
}
```

---

## 4) `RouteResolver.swift` update

```swift
import Foundation

enum AppRoute {
    case done
    case revisionLoop
    case stakeholderReject
}

extension RouteResolver {
    func resolvePostJudgeRoute(_ route: String) -> AppRoute {
        switch route {
        case "done":
            return .done
        case "stakeholder_reject":
            return .stakeholderReject
        default:
            return .revisionLoop
        }
    }
}
```

---

## 5) `OrchestrationController.swift` update

```swift
import Foundation

extension OrchestrationController {
    func handleJudgeCompleted(runFolder: URL) {
        do {
            try backendBridge.runPostJudgeTransition(runFolder: runFolder)
            let routePayload = try backendBridge.readPostJudgeRoute(runFolder: runFolder)
            let nextRoute = routeResolver.resolvePostJudgeRoute(routePayload.nextRoute)
            navigate(to: nextRoute)

            statusViewModel.refresh(runFolder: runFolder)
        } catch {
            // Minimal fallback behavior: keep existing safe route.
            navigate(to: .revisionLoop)
        }
    }
}
```

---

## 6) `RunArtifacts.swift` update

```swift
import Foundation

struct RunArtifacts {
    let runFolder: URL

    var executionJSON: URL {
        runFolder.appendingPathComponent("execution.json")
    }

    var finalAuditJSON: URL {
        runFolder.appendingPathComponent("final_audit.json")
    }
}
```

---

## Minimal end-to-end sequence

1. Judge stage completes in `OrchestrationController`.
2. `BackendBridgeService.runPostJudgeTransition(...)` persists backend post-judge artifacts.
3. `BackendBridgeService.readPostJudgeRoute(...)` returns `next_route`.
4. `RouteResolver` maps backend route string to existing app route enum.
5. `StatusViewModel.refresh(...)` pulls `gui-health-status` and updates UI status.

No backend redesign and no branch workflow changes are required.
