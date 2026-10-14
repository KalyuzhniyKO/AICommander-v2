# Recommended Codex model and reasoning effort by task

[Русская версия](MODEL_SELECTION.md)

| Task class | Model (if available in Codex) | Effort | Rationale |
|---|---|---|---|
| Mechanical change or documentation | GPT-6 Luna | Low | Cheapest adequate model for routine changes |
| Standard implementation / integration | **GPT-6.1 Sol** | **Medium** | Good balance for most tasks |
| Multi-step design and debugging | GPT-6.1 Sol | High | More careful architectural analysis |
| Security, orchestration and complex E2E | **GPT-6 Astra** | **High** | Favor correctness when failure is costly |

See [OpenAI model selection](https://developers.openai.com/api/docs/guides/model-selection), [reasoning](https://developers.openai.com/api/docs/guides/reasoning), and [Codex programming](https://developers.openai.com/api/docs/guides/code-generation).

This table selects the **Codex worker used to implement the GitHub issue**, not the models that future AI roles will route via OmniRouter. Available model names vary by Codex environment and entitlements; use the closest currently offered alternative when necessary and document the substitution in the PR. ChatGPT web is a manual human escalation, not an API. Start at Medium and increase only when warranted.
