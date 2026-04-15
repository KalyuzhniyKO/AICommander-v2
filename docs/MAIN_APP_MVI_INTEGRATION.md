# AICommander main app integration (migration pack #2, MVI)

This document defines **minimal viable integration** of AICommander-v2 backend into the existing main app.

## Exact files to change in existing AICommander app

> These file paths are for the existing main app repository.

1. `AICommander/AppFlow/OrchestrationController.swift`
   - after judge stage completion, invoke backend hook (`--run-post-judge-transition`) or Python bridge API.
2. `AICommander/AppFlow/RouteResolver.swift`
   - read route mapping payload after judge:
     - `approve -> done`
     - `revise -> revision_loop`
     - `reject -> stakeholder_reject`
3. `AICommander/Models/RunArtifacts.swift`
   - add optional `final_audit.json` support while preserving existing artifacts.
4. `AICommander/ViewModels/StatusViewModel.swift`
   - replace machine-based status source with provider-based status payload keys:
     - `provider_status`, `director_role`, `coder_role`, `reviewer_role`, `qa_role`, `judge_role`, `final_auditor_role`, `workspace_status`, `orchestration_status`
5. `AICommander/Services/BackendBridgeService.swift`
   - wire to `python -m backend.cli --run-post-judge-transition`, `--read-post-judge-route`, `--gui-health-status`.

## MVI integration approach

1. Keep existing flow unchanged up to and including judge stage.
2. After judge, call one of:
   - CLI (recommended): `python -m backend.cli --run-post-judge-mvi --run-folder <run_folder>`
   - CLI (split flow): `python -m backend.cli --run-post-judge-transition --run-folder <run_folder>`
   - Python API: `run_after_judge_and_resolve_next_step(...)`
3. Read route:
   - CLI: `python -m backend.cli --read-post-judge-route --run-folder <run_folder>`
   - Use `next_route` for app routing.
4. Replace status payload source with:
   - CLI: `python -m backend.cli --gui-health-status --run-folder <run_folder>`
   - Python API: `get_gui_status_model_for_app(...)`
5. Preserve run-folder backward compatibility and existing artifacts.

## Key pseudo-diff snippets (existing app)

```diff
--- a/AICommander/AppFlow/OrchestrationController.swift
+++ b/AICommander/AppFlow/OrchestrationController.swift
@@
- if stage == .judgeDone { route = .done }
+ if stage == .judgeDone {
+   let transition = backendBridge.runPostJudgeTransition(runFolder)
+   route = mapRoute(transition.integration.next_route)
+ }
```

```diff
--- a/AICommander/ViewModels/StatusViewModel.swift
+++ b/AICommander/ViewModels/StatusViewModel.swift
@@
- status = machineStatusProvider.current()
+ status = backendBridge.guiHealthStatus(runFolder)
```

```diff
--- a/AICommander/Models/RunArtifacts.swift
+++ b/AICommander/Models/RunArtifacts.swift
@@
+ let finalAudit = runFolder.appendingPathComponent("final_audit.json")
```
