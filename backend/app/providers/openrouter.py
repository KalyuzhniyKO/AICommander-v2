"""OpenRouter chat-completion provider."""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request

from .base import ChatMessage, ChatProvider, ChatResult, ProviderError, messages_to_dicts


class OpenRouterProvider(ChatProvider):
    provider_name = "openrouter"

    def __init__(self, api_key: str, base_url: str = "https://openrouter.ai/api/v1") -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")

    def chat(self, model_id: str, messages: list[ChatMessage], timeout_seconds: int) -> ChatResult:
        if not self.api_key:
            raise ProviderError("OPENROUTER_API_KEY is not configured", "not_configured")
        start = time.monotonic()
        payload = json.dumps({"model": model_id, "messages": messages_to_dicts(messages)}).encode("utf-8")
        request = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=payload,
            method="POST",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://github.com/KalyuzhniyKO/AICommander-v2",
                "X-Title": "AICommander-v2",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
                body = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            category = "quota_or_tokens" if exc.code in {402, 403, 429} else "api_error"
            detail = exc.read().decode("utf-8", errors="replace")[:1000]
            raise ProviderError(f"OpenRouter HTTP {exc.code}: {detail}", category) from exc
        except TimeoutError as exc:
            raise ProviderError("OpenRouter request timed out", "timeout") from exc
        except Exception as exc:
            raise ProviderError(f"OpenRouter request failed: {exc}", "api_error") from exc
        elapsed = int((time.monotonic() - start) * 1000)
        try:
            parsed = json.loads(body)
            content = parsed["choices"][0]["message"]["content"]
        except Exception as exc:
            raise ProviderError(f"OpenRouter returned a bad response: {exc}", "bad_response") from exc
        if not content or not str(content).strip():
            raise ProviderError("OpenRouter returned an empty response", "bad_response")
        return ChatResult(provider=self.provider_name, model_id=model_id, content=str(content), response_time_ms=elapsed, raw=parsed)
