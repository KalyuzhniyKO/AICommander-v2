[Русская версия](OPEN_SOURCE_REVIEW.md)

# Open-source reuse review (2026-10-14)

**Policy:** do not reinvent solved problems, but avoid installing redundant multi-agent engines atop existing Hermes + OmniRouter. **No third-party source code has been copied into this v3 foundation.** Below are references, ideas and licensing notes (licence must be rechecked at exact revision before any code is adopted).

| Project | Authors / canonical source | Licence at review | Potential reuse | Decision |
|---|---|---|---|---|
| CrewAI | CrewAI Inc. https://github.com/crewAIInc/crewAI | MIT | role/crew/task contract, flows | pattern/reference, adapter only if needed |
| MetaGPT | FoundationAgents https://github.com/FoundationAgents/MetaGPT | MIT | SOP, analyst -> architect -> engineer handoff | study ideas, not copy framework |
| LangGraph | LangChain https://github.com/langchain-ai/langgraph | MIT for core; verify package | durable checkpointed state machines, human approval | optional library after ADR |
| OpenHands Software Agent SDK | OpenHands contributors https://github.com/OpenHands/software-agent-sdk | MIT | isolated code execution, agent tooling | evaluate as coding executor alternative to Codex CLI |
| Microsoft Agent Framework | Microsoft https://github.com/microsoft/agent-framework | MIT | typed multi-agent orchestration and durable state | reference, potentially overlapping Hermes |
| SWE-agent | SWE-agent authors https://github.com/SWE-agent/SWE-agent | MIT | issue -> code -> test workflow | inspiration for GitHub integration |

**Avoid:** microsoft/autogen for new work; its README marks the project in maintenance mode and recommends Microsoft Agent Framework: https://github.com/microsoft/autogen .

## Follow-up after Zorin audit — 2026-10-15

[ADR-001 English summary](ADR-001-ORCHESTRATION.en.md) connects the retained
2026-10-14 pinned upstream evidence to current local facts. OmniRoute health and
SSH access are verified; Hermes custom backend/delegation are source contracts,
not demonstrated runtime integration. Authenticated inventory remains unverified
by the owner's choice. Existing mock taskflow, owner panel and trusted-fixture
executor do not justify adding another orchestration framework or an OS sandbox claim.
No framework was added, no upstream source copied, and #13 remains gated by #11/#12.

## Required actions before integrating copied code
1. Choose exact source file + commit SHA and record URL, upstream owner and purpose in this document.
2. Check file-level licence and dependencies; some repositories have separately licensed enterprise subdirectories. Do not copy those without permission.
3. For MIT, preserve full copyright and licence notice with substantial copied code; add `THIRD_PARTY_NOTICES.md` and required licence text.
4. Prefer importing an upstream package where appropriate, pin versions, document changes, add tests and update notices.
5. Confirm compatibility with Hermes/OmniRouter's actual public interfaces; no invented API.
