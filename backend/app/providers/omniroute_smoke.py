"""Explicit opt-in live probe. Never imported or run by application startup."""
from dataclasses import replace
import json
import os

from .base import ChatMessage
from .omniroute import OmniRouteConfig, OmniRouteError, OmniRouteProvider


def main() -> int:
    if os.environ.get("OMNIROUTE_RUN_LIVE_SMOKE") != "true":
        print(json.dumps({"status": "skipped", "reason": "explicit_live_opt_in_required"}))
        return 2
    try:
        config = replace(OmniRouteConfig.from_env(), max_get_attempts=1,
                         max_output_tokens=64, timeout_seconds=45)
        provider = OmniRouteProvider(config)
        health = provider.health()
        models = provider.models()
        print(json.dumps({"check": "health_and_models", "status": health["status"], "model_count": len(models)}))
        if os.environ.get("OMNIROUTE_SMOKE_INFERENCE") == "true":
            model = os.environ.get("OMNIROUTE_SMOKE_MODEL", "")
            if model not in models:
                raise OmniRouteError("smoke_model_not_in_inventory")
            result = provider.chat(model, [ChatMessage("user", "Reply with the word OK and nothing else.")], 45)
            print(json.dumps({"check": "inference", "nonempty_response": bool(result.content.strip()),
                              "reply_ok": result.content.strip() == "OK", "response_time_ms": result.response_time_ms}))
        return 0
    except OmniRouteError as exc:
        print(json.dumps({"status": "failed", "category": exc.category, "http_status": exc.status_code}))
        return 1
    except Exception:
        print(json.dumps({"status": "failed", "category": "unexpected_probe_error"}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
