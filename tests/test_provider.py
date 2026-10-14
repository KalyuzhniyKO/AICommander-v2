import io
import json
import urllib.error
import urllib.request

import pytest

from backend.app.providers.base import ChatMessage, ProviderError
from backend.app.providers.openrouter import OpenRouterProvider


def chat():
    return OpenRouterProvider("test-key", "https://models.invalid/api/v1/").chat(
        "test-model", [ChatMessage("user", "test prompt")], 3,
    )


def test_request_payload_and_response_are_closed(monkeypatch):
    response = io.BytesIO(json.dumps({"choices": [{"message": {"content": "OK"}}]}).encode())

    def urlopen(request, timeout):
        assert request.full_url == "https://models.invalid/api/v1/chat/completions"
        assert request.method == "POST" and timeout == 3
        assert request.get_header("Authorization") == "Bearer test-key"
        assert json.loads(request.data) == {"model": "test-model", "messages": [{"role": "user", "content": "test prompt"}]}
        return response

    monkeypatch.setattr(urllib.request, "urlopen", urlopen)
    result = chat()
    assert result.content == "OK" and result.model_id == "test-model"
    assert response.closed


@pytest.mark.parametrize("code,category", [(402, "quota_or_tokens"), (403, "quota_or_tokens"), (429, "quota_or_tokens"), (500, "api_error")])
def test_http_error_is_closed_and_body_not_exposed(monkeypatch, code, category):
    body = io.BytesIO(b"private prompt and test-key")
    error = urllib.error.HTTPError("https://models.invalid", code, "error", {}, body)

    def fail(*args, **kwargs):
        raise error

    monkeypatch.setattr(urllib.request, "urlopen", fail)
    with pytest.raises(ProviderError) as exc:
        chat()
    assert exc.value.category == category
    assert str(exc.value) == f"OpenRouter HTTP {code}"
    assert body.closed


@pytest.mark.parametrize("error,category", [
    (TimeoutError(), "timeout"),
    (urllib.error.URLError(TimeoutError()), "timeout"),
    (urllib.error.URLError("private details test-key"), "api_error"),
])
def test_transport_failure_categories(monkeypatch, error, category):
    def fail(*args, **kwargs):
        raise error

    monkeypatch.setattr(urllib.request, "urlopen", fail)
    with pytest.raises(ProviderError) as exc:
        chat()
    assert exc.value.category == category
    assert "test-key" not in str(exc.value)


@pytest.mark.parametrize("body", [b"not json", b"{}", b'{"choices": []}', b'{"choices": [{"message": {"content": " "}}]}'])
def test_bad_response_is_closed(monkeypatch, body):
    response = io.BytesIO(body)
    monkeypatch.setattr(urllib.request, "urlopen", lambda *a, **kw: response)
    with pytest.raises(ProviderError, match="response") as exc:
        chat()
    assert exc.value.category == "bad_response"
    assert response.closed


def test_missing_key_does_not_use_network():
    with pytest.raises(ProviderError) as exc:
        OpenRouterProvider("").chat("model", [], 1)
    assert exc.value.category == "not_configured"
