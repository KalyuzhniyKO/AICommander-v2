# macOS AICommander backend integration (minimal patch)

This guide gives **paste-ready Swift integration** for wiring the macOS app to these backend CLI hooks:

- `python -m backend.cli --run-post-judge-transition`
- `python -m backend.cli --read-post-judge-route`
- `python -m backend.cli --gui-health-status`

It keeps app structure intact (no redesign, no backend rewrite) and only adds the integration layer.

## 1) Exact app call points in current flow

Use these call sites in the existing macOS app repository:

1. `AICommander/AppFlow/OrchestrationController.swift`
   - Right after judge stage is marked complete, call:
     - `runPostJudgeTransition(runFolder:)`
     - then `readPostJudgeRoute(runFolder:)`
   - Feed `next_route` into route resolution.

2. `AICommander/AppFlow/RouteResolver.swift`
   - Replace/augment hardcoded judge-outcome logic with backend route payload (`done`, `revision_loop`, `stakeholder_reject`).

3. `AICommander/ViewModels/StatusViewModel.swift`
   - Replace machine-status polling source with:
     - `guiHealthStatus(runFolder:)`
   - Map returned payload keys to current UI state.

4. `AICommander/Services/BackendBridgeService.swift`
   - Add a small Process-based Python bridge that executes backend CLI + decodes JSON.

---

## 2) Paste-ready file: `AICommander/Services/BackendBridgeService.swift`

```swift
import Foundation

enum BackendBridgeError: Error, LocalizedError {
    case pythonNotFound
    case commandFailed(exitCode: Int32, stderr: String)
    case invalidJSON(String)

    var errorDescription: String? {
        switch self {
        case .pythonNotFound:
            return "python executable not found in PATH"
        case let .commandFailed(exitCode, stderr):
            return "Backend CLI failed with exit code \(exitCode): \(stderr)"
        case let .invalidJSON(raw):
            return "Backend CLI returned invalid JSON: \(raw.prefix(500))"
        }
    }
}

struct PostJudgeRoutePayload: Decodable {
    let status: String
    let final_verdict: String
    let next_route: String
    let final_audit_path: String
}

struct GuiHealthStatusPayload: Decodable {
    let provider_status: [String: String]
    let director_role: [String: String]
    let coder_role: [String: String]
    let reviewer_role: [String: String]
    let qa_role: [String: String]
    let judge_role: [String: String]
    let final_auditor_role: [String: String]
    let workspace_status: [String: String]
    let orchestration_status: [String: String]
}

final class BackendBridgeService {
    private let pythonExecutable: String
    private let backendWorkingDirectory: URL

    /// - Parameters:
    ///   - pythonExecutable: usually "python" or "python3"
    ///   - backendWorkingDirectory: folder where `backend/` package is importable
    init(
        pythonExecutable: String = "python",
        backendWorkingDirectory: URL
    ) {
        self.pythonExecutable = pythonExecutable
        self.backendWorkingDirectory = backendWorkingDirectory
    }

    func runPostJudgeTransition(runFolder: URL, executionMode: String? = nil) throws {
        var args = ["-m", "backend.cli", "--run-post-judge-transition", "--run-folder", runFolder.path]
        if let executionMode {
            args += ["--execution-mode", executionMode]
        }
        _ = try runJSONCommand(arguments: args)
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

    // MARK: - Process + JSON

    private func runDecodable<T: Decodable>(arguments: [String], as type: T.Type) throws -> T {
        let json = try runJSONCommand(arguments: arguments)
        do {
            let data = try JSONSerialization.data(withJSONObject: json, options: [])
            return try JSONDecoder().decode(T.self, from: data)
        } catch {
            throw BackendBridgeError.invalidJSON(String(describing: json))
        }
    }

    @discardableResult
    private func runJSONCommand(arguments: [String]) throws -> [String: Any] {
        let process = Process()
        process.currentDirectoryURL = backendWorkingDirectory
        process.executableURL = URL(fileURLWithPath: "/usr/bin/env")
        process.arguments = [pythonExecutable] + arguments

        let stdoutPipe = Pipe()
        let stderrPipe = Pipe()
        process.standardOutput = stdoutPipe
        process.standardError = stderrPipe

        do {
            try process.run()
        } catch {
            throw BackendBridgeError.pythonNotFound
        }

        process.waitUntilExit()

        let stdoutData = stdoutPipe.fileHandleForReading.readDataToEndOfFile()
        let stderrData = stderrPipe.fileHandleForReading.readDataToEndOfFile()

        let stdoutString = String(data: stdoutData, encoding: .utf8) ?? ""
        let stderrString = String(data: stderrData, encoding: .utf8) ?? ""

        guard process.terminationStatus == 0 else {
            throw BackendBridgeError.commandFailed(exitCode: process.terminationStatus, stderr: stderrString)
        }

        guard
            let jsonData = stdoutString.data(using: .utf8),
            let jsonObject = try JSONSerialization.jsonObject(with: jsonData, options: []) as? [String: Any]
        else {
            throw BackendBridgeError.invalidJSON(stdoutString)
        }

        return jsonObject
    }
}
```

---

## 3) Paste-ready update: `AICommander/AppFlow/RouteResolver.swift`

```swift
import Foundation

enum AppRoute {
    case done
    case revisionLoop
    case stakeholderReject
}

extension RouteResolver {
    func resolvePostJudgeRoute(from backendRoute: String) -> AppRoute {
        switch backendRoute {
        case "done":
            return .done
        case "stakeholder_reject":
            return .stakeholderReject
        case "revision_loop":
            fallthrough
        default:
            return .revisionLoop
        }
    }
}
```

---

## 4) Paste-ready update: `AICommander/ViewModels/StatusViewModel.swift`

```swift
import Foundation
import Combine

@MainActor
final class StatusViewModel: ObservableObject {
    @Published private(set) var providerStatus: [String: String] = [:]
    @Published private(set) var orchestrationStatus: [String: String] = [:]
    @Published private(set) var workspaceStatus: [String: String] = [:]

    private let backendBridge: BackendBridgeService

    init(backendBridge: BackendBridgeService) {
        self.backendBridge = backendBridge
    }

    func refresh(runFolder: URL, executionMode: String? = nil) {
        Task {
            do {
                let health = try backendBridge.guiHealthStatus(runFolder: runFolder, executionMode: executionMode)
                providerStatus = health.provider_status
                orchestrationStatus = health.orchestration_status
                workspaceStatus = health.workspace_status
            } catch {
                // keep existing UI behavior; optionally publish error state
                NSLog("Failed to refresh gui health status: \(error.localizedDescription)")
            }
        }
    }
}
```

---

## 5) Minimal end-to-end flow in `OrchestrationController.swift`

```swift
func handleJudgeCompleted(runFolder: URL) {
    do {
        // 1) Persist transition side effects (writes execution.json/final_audit.json)
        try backendBridge.runPostJudgeTransition(runFolder: runFolder)

        // 2) Read explicit route for UI navigation
        let routePayload = try backendBridge.readPostJudgeRoute(runFolder: runFolder)
        let nextRoute = routeResolver.resolvePostJudgeRoute(from: routePayload.next_route)

        // 3) Navigate exactly once using resolved route
        navigate(to: nextRoute)

        // 4) Refresh status panel from backend health payload
        statusViewModel.refresh(runFolder: runFolder)
    } catch {
        // fallback remains minimal: keep existing revision loop behavior
        navigate(to: .revisionLoop)
        NSLog("Post-judge backend integration failed: \(error.localizedDescription)")
    }
}
```

This is the minimal integration sequence:

1. Judge completes.
2. Call `--run-post-judge-transition`.
3. Call `--read-post-judge-route` and map `next_route`.
4. Navigate with `RouteResolver`.
5. Refresh `StatusViewModel` using `--gui-health-status`.

No app redesign is required.
