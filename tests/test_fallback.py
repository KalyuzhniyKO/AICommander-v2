from unittest.mock import Mock

import pytest

from backend.app.orchestration.fallback import run_with_fallback
from backend.app.providers.base import ChatMessage, ChatResult, ProviderError


def run(repository, provider, refs=None, attempts=2, provider_filter=None):
    return run_with_fallback(
        role="coder", model_refs=refs if refs is not None else ["openrouter/first", "openrouter/second"],
        messages=[ChatMessage("user", "test")], timeout_seconds=3,
        max_attempts_per_model=attempts, repository=repository, round_id=None,
        openrouter=provider, provider_filter=provider_filter,
    )


def test_retry_then_fallback_preserves_order_and_errors(repository):
    provider = Mock()
    provider.chat.side_effect = [
        ProviderError("timeout", "timeout"), ProviderError("429", "quota_or_tokens"),
        ChatResult("openrouter", "second", "answer", 12),
    ]
    outcome = run(repository, provider)
    assert outcome.success and outcome.output == "answer"
    assert outcome.model_id == "second" and outcome.response_time_ms == 12
    assert [c.kwargs["model_id"] for c in provider.chat.call_args_list] == ["first", "first", "second"]
    assert all(c.kwargs["timeout_seconds"] == 3 for c in provider.chat.call_args_list)
    assert len(outcome.errors) == 2
    assert repository.conn.execute("SELECT COUNT(*) FROM model_errors").fetchone()[0] == 2
    statuses = {r["model_id"]: r for r in repository.list_model_status()}
    assert statuses["first"]["status"] == "failed"
    assert statuses["second"]["status"] == "available"


def test_success_on_retry_clears_last_error_and_stops(repository):
    provider = Mock()
    provider.chat.side_effect = [ProviderError("timeout", "timeout"), ChatResult("openrouter", "first", "OK", 5)]
    outcome = run(repository, provider)
    assert outcome.success and len(outcome.errors) == 1
    assert provider.chat.call_count == 2
    status = repository.list_model_status()[0]
    assert status["status"] == "available" and status["last_error"] == ""
    assert status["last_failure_at"] and status["last_success_at"]


@pytest.mark.parametrize("attempts,expected", [(0, 2), (1, 2), (3, 6)])
def test_all_failures_have_bounded_attempts(repository, attempts, expected):
    provider = Mock()
    provider.chat.side_effect = ProviderError("unavailable")
    outcome = run(repository, provider, attempts=attempts)
    assert not outcome.success
    assert provider.chat.call_count == expected == len(outcome.errors)


def test_unexpected_provider_failure_can_fall_back(repository):
    provider = Mock()
    provider.chat.side_effect = [RuntimeError("broken transport"), ChatResult("openrouter", "second", "OK", 1)]
    assert run(repository, provider, attempts=1).success


@pytest.mark.parametrize("refs", [[], ["unsupported/test"]])
def test_empty_or_filtered_models_never_call_transport(repository, refs):
    provider = Mock()
    assert not run(repository, provider, refs=refs, provider_filter=lambda p: p == "openrouter").success
    provider.chat.assert_not_called()
