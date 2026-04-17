# macOS AICommander backend integration (PR #4 continuation)

This keeps the real architecture exactly as-is (CLI via `Process`), with no HTTP/URLSession redesign:

- `python -m backend.cli --run-post-judge-transition`
- `python -m backend.cli --read-post-judge-route`
- `python -m backend.cli --gui-health-status`

## Minimal integration instructions (existing app)

1. In `OrchestrationController.swift` (after judge completes):
   - call `runPostJudgeTransition(runFolder:)`
   - call `readPostJudgeRoute(runFolder:)`
   - map `next_route` with `RouteResolver`
2. In `StatusViewModel.swift`:
   - call `guiHealthStatus(runFolder:)`
   - bind key health sections to current UI
3. In `RunArtifacts.swift`:
   - include `final_audit.json` path (optional artifact)

---

## Exact backend JSON contracts

### A) `--read-post-judge-route`

```json
{
  "status": "ok",
  "final_verdict": "approve",
  "next_route": "done",
  "final_audit_path": "/abs/path/to/final_audit.json"
}
```

Possible values:
- `status`: `ok` | `missing_final_audit`
- `final_verdict`: typically `approve` | `revise` | `reject`
- `next_route`: `done` | `revision_loop` | `stakeholder_reject`

### B) `--gui-health-status`

```json
{
  "provider_status": {
    "status": "ok",
    "provider": "openai_compatible",
    "base_url": "https://...",
    "api_key_present": true,
    "endpoint_reachable": true,
    "auth_ok": true,
    "http_status": 200,
    "error": null,
    "errors": []
  },
  "director_role": {
    "status": "ok",
    "provider": "openai_compatible",
    "model": "...",
    "base_url": "https://...",
    "mode": "balanced",
    "config_valid": true,
    "errors": []
  },
  "coder_role": { "...": "same shape as director_role" },
  "reviewer_role": { "...": "same shape as director_role" },
  "qa_role": { "...": "same shape as director_role" },
  "judge_role": { "...": "same shape as director_role" },
  "final_auditor_role": { "...": "same shape as director_role" },
  "workspace_status": {
    "status": "ok",
    "writable": true,
    "path": "/abs/path",
    "error": null
  },
  "orchestration_status": {
    "status": "ok",
    "required": ["director_response.json", "execution.json", "manual_review.json", "team_summary.json"],
    "found": ["director_response.json", "execution.json", "manual_review.json", "team_summary.json"]
  },
  "execution_mode": "balanced",
  "legacy_aliases": {
    "coder_node_lenovo": "deprecated",
    "reviewer_node_home_pc": "deprecated",
    "qa_node_home_pc": "deprecated"
  },
  "role_config_valid": true,
  "final_auditor_config_valid": true
}
```

---

## 1) `BackendBridgeService.swift` (paste-ready)

```swift
import Foundation

enum BackendBridgeError: Error, LocalizedError {
    case commandFailed(exitCode: Int32, stderr: String)

    var errorDescription: String? {
        switch self {
        case let .commandFailed(code, stderr):
            return "Backend CLI failed with exit code \(code): \(stderr)"
        }
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

struct ProviderStatus: Decodable {
    let status: String
    let provider: String?
    let baseURL: String?
    let apiKeyPresent: Bool?
    let endpointReachable: Bool?
    let authOK: Bool?
    let httpStatus: Int?
    let error: String?
    let errors: [String]?

    enum CodingKeys: String, CodingKey {
        case status
        case provider
        case baseURL = "base_url"
        case apiKeyPresent = "api_key_present"
        case endpointReachable = "endpoint_reachable"
        case authOK = "auth_ok"
        case httpStatus = "http_status"
        case error
        case errors
    }
}

struct RoleStatus: Decodable {
    let status: String
    let provider: String?
    let model: String?
    let baseURL: String?
    let mode: String?
    let configValid: Bool
    let errors: [String]

    enum CodingKeys: String, CodingKey {
        case status
        case provider
        case model
        case baseURL = "base_url"
        case mode
        case configValid = "config_valid"
        case errors
    }
}

struct WorkspaceStatus: Decodable {
    let status: String
    let writable: Bool
    let path: String
    let error: String?
}

struct OrchestrationStatus: Decodable {
    let status: String
    let required: [String]
    let found: [String]
}

struct GuiHealthStatusPayload: Decodable {
    let providerStatus: ProviderStatus
    let directorRole: RoleStatus
    let coderRole: RoleStatus
    let reviewerRole: RoleStatus
    let qaRole: RoleStatus
    let judgeRole: RoleStatus
    let finalAuditorRole: RoleStatus
    let workspaceStatus: WorkspaceStatus
    let orchestrationStatus: OrchestrationStatus
    let executionMode: String
    let legacyAliases: [String: String]
    let roleConfigValid: Bool
    let finalAuditorConfigValid: Bool

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
        case executionMode = "execution_mode"
        case legacyAliases = "legacy_aliases"
        case roleConfigValid = "role_config_valid"
        case finalAuditorConfigValid = "final_auditor_config_valid"
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

        return stdoutData
    }
}
```

---

## 2) `GuiHealthStatus.swift` (paste-ready)

```swift
import Foundation

struct GuiHealthStatus {
    let providerStatus: String
    let workspaceStatus: String
    let orchestrationStatus: String
    let roleConfigValid: Bool
    let finalAuditorConfigValid: Bool

    static func fromPayload(_ payload: GuiHealthStatusPayload) -> GuiHealthStatus {
        GuiHealthStatus(
            providerStatus: payload.providerStatus.status,
            workspaceStatus: payload.workspaceStatus.status,
            orchestrationStatus: payload.orchestrationStatus.status,
            roleConfigValid: payload.roleConfigValid,
            finalAuditorConfigValid: payload.finalAuditorConfigValid
        )
    }
}
```

---

## 3) `StatusViewModel.swift` (minimal update)

```swift
import Foundation
import Combine

@MainActor
final class StatusViewModel: ObservableObject {
    @Published private(set) var guiHealth: GuiHealthStatus?
    @Published private(set) var lastError: String?

    private let backendBridge: BackendBridgeService

    init(backendBridge: BackendBridgeService) {
        self.backendBridge = backendBridge
    }

    func refresh(runFolder: URL, executionMode: String? = nil) {
        do {
            let payload = try backendBridge.guiHealthStatus(runFolder: runFolder, executionMode: executionMode)
            guiHealth = GuiHealthStatus.fromPayload(payload)
            lastError = nil
        } catch {
            lastError = error.localizedDescription
        }
    }
}
```

---

## 4) `RouteResolver.swift` (minimal update)

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

## 5) `OrchestrationController.swift` (minimal update)

```swift
import Foundation

extension OrchestrationController {
    func handleJudgeCompleted(runFolder: URL) {
        do {
            try backendBridge.runPostJudgeTransition(runFolder: runFolder)
            let routePayload = try backendBridge.readPostJudgeRoute(runFolder: runFolder)
            let appRoute = routeResolver.resolvePostJudgeRoute(routePayload.nextRoute)
            navigate(to: appRoute)

            statusViewModel.refresh(runFolder: runFolder)
        } catch {
            // Preserve existing fallback behavior.
            navigate(to: .revisionLoop)
        }
    }
}
```

---

## 6) `RunArtifacts.swift` (minimal update)

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
