# Roadmap: Universal AI Team Orchestrator

This is a future architecture plan. It is **not implemented** in the cleanup branch.

## Goal

Build a universal AI team orchestrator that can coordinate multiple specialized AI roles through OpenRouter, keep the default workflow free/low-cost, and optionally add Premium Review when budget and tokens are available.

## Provider strategy

OpenRouter should be the primary provider for the free/default workflow because it offers a single OpenAI-compatible API surface and access to multiple model families.

Planned provider behavior:

1. Use OpenRouter as the default provider.
2. Prefer free or low-cost models for the main workflow.
3. Keep provider/model selection configurable through environment variables or config files.
4. Treat paid/Premium Review as optional and isolated from the main free workflow.

## Planned roles

The planned orchestrator team roles are:

- `manager` — decomposes the user request, coordinates rounds, and decides when to stop.
- `architect` — designs the technical approach and validates boundaries.
- `designer` — prepares UX/product structure, user-facing behavior, and documentation direction.
- `coder` — implements the approved plan.
- `reviewer` — checks correctness, risks, regressions, and acceptance criteria.

The existing `final_auditor` remains the current backend final audit stage until this future orchestrator replaces or incorporates it.

## Fallback model policy

Each role should support an ordered fallback list:

```text
role primary model -> role fallback model -> shared fallback model -> skip/degrade gracefully
```

Fallback rules:

- If a role model is unavailable, try the next configured fallback.
- If OpenRouter reports rate limits, token exhaustion, or transient provider failure, retry only within safe limits.
- If the role cannot run after fallbacks, return a structured degraded result instead of crashing the whole workflow.
- The `manager` decides whether a degraded role result is acceptable or whether a human should intervene.

## Human-in-the-loop rounds

The orchestrator should support explicit human checkpoints:

1. Planning checkpoint after `manager` + `architect` produce the plan.
2. Design checkpoint when UX/product decisions are material.
3. Implementation checkpoint after `coder` produces changes.
4. Review checkpoint after `reviewer` flags issues or approves.

Rounds should be bounded by configuration, for example:

```text
AICOMMANDER_MAX_HITL_ROUNDS=3
AICOMMANDER_REQUIRE_HUMAN_APPROVAL=true
```

## Optional Premium Review

Premium Review is a separate optional stage, not part of the required free workflow.

Expected behavior:

- The main free workflow must complete without Premium Review.
- Premium Review may use a stronger paid model when the user explicitly enables it.
- Premium Review produces an additional artifact, for example `premium_review.json`.
- Premium Review can recommend follow-up work but must not block the base workflow from producing its normal result.

## Token/limit exhaustion behavior

If tokens, quota, or paid-model limits are exhausted:

1. Skip Premium Review automatically.
2. Mark the skip reason in the run artifacts.
3. Preserve the free workflow result.
4. Allow Premium Review to be manually run later against the same artifacts.

Example state:

```json
{
  "premium_review": {
    "status": "skipped",
    "reason": "quota_or_token_limit",
    "manual_retry_available": true
  }
}
```

## Future branch

Implement this roadmap in `feature/free-ai-team-orchestrator` after `chore/cleanup-repo-structure` is reviewed and merged, or directly from the cleanup branch if the team chooses to continue before merge.
