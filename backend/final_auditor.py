"""Final auditor role execution."""

from __future__ import annotations

import json
import re
import urllib.error
import urllib.request
from typing import Any, Dict

from .config import RoleConfig


SYSTEM_PROMPT = (
    "You are final_auditor in AICommander v2. Return strict JSON with keys: "
    "final_verdict, stakeholder_summary, critical_issues, recommendation, requires_revision."
)


def _build_prompt(payload: Dict[str, Any]) -> str:
    return (
        "Audit this orchestration result and return strict JSON only. "
        "Use final_verdict in {approve, revise, reject}.\n\n"
        f"INPUT:\n{json.dumps(payload, ensure_ascii=False, indent=2)}"
    )


def _public_role_descriptor(role: RoleConfig) -> Dict[str, str]:
    """Return non-secret role descriptor for logs/artifacts."""
    return {
        "role": role.role,
        "provider": role.provider,
        "model": role.model,
        "base_url": role.base_url,
        "mode": role.mode,
    }


def _error_payload(role: RoleConfig, error_type: str, message: str, details: Dict[str, Any] | None = None) -> Dict[str, Any]:
    return {
        "status": "error",
        "error_type": error_type,
        "error_message": message,
        "error_details": details or {},
        "final_verdict": "revise",
        "stakeholder_summary": "Final audit failed. Manual revision required.",
        "critical_issues": [message],
        "recommendation": "Retry final audit after fixing provider/config/runtime issue.",
        "requires_revision": True,
        "role": _public_role_descriptor(role),
    }


def _extract_json_text(text: str) -> str:
    stripped = text.strip()
    if stripped.startswith("{") and stripped.endswith("}"):
        return stripped

    fenced = re.search(r"```(?:json)?\s*(\{.*\})\s*```", stripped, flags=re.DOTALL)
    if fenced:
        return fenced.group(1)

    first = stripped.find("{")
    last = stripped.rfind("}")
    if first != -1 and last != -1 and last > first:
        return stripped[first : last + 1]

    return stripped


def _normalize_result(role: RoleConfig, parsed: Dict[str, Any]) -> Dict[str, Any]:
    verdict = str(parsed.get("final_verdict", "revise")).strip().lower()
    if verdict not in {"approve", "revise", "reject"}:
        verdict = "revise"

    critical_issues = parsed.get("critical_issues", [])
    if not isinstance(critical_issues, list):
        critical_issues = [str(critical_issues)] if critical_issues else []

    return {
        "status": "ok",
        "final_verdict": verdict,
        "stakeholder_summary": str(parsed.get("stakeholder_summary", "")).strip(),
        "critical_issues": [str(item) for item in critical_issues],
        "recommendation": str(parsed.get("recommendation", "")).strip(),
        "requires_revision": bool(parsed.get("requires_revision", verdict != "approve")),
        "role": _public_role_descriptor(role),
    }


def _request_chat(role: RoleConfig, req_body: Dict[str, Any], timeout: int) -> Dict[str, Any]:
    request = urllib.request.Request(
        url=f"{role.base_url.rstrip('/')}/chat/completions",
        data=json.dumps(req_body).encode("utf-8"),
        method="POST",
        headers={
            "Authorization": f"Bearer {role.api_key}",
            "Content-Type": "application/json",
        },
    )

    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def run_final_auditor(role: RoleConfig, payload: Dict[str, Any], timeout: int = 30) -> Dict[str, Any]:
    if not role.is_valid:
        return _error_payload(role, "role_config_invalid", "Final auditor role config is invalid.", {"errors": role.errors})

    req_body = {
        "model": role.model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": _build_prompt(payload)},
        ],
        "response_format": {"type": "json_object"},
    }

    try:
        try:
            raw = _request_chat(role=role, req_body=req_body, timeout=timeout)
        except urllib.error.HTTPError as exc:
            if exc.code == 400:
                fallback_req = dict(req_body)
                fallback_req.pop("response_format", None)
                raw = _request_chat(role=role, req_body=fallback_req, timeout=timeout)
            else:
                body = exc.read().decode("utf-8", errors="replace")
                return _error_payload(role, "http_error", f"HTTP error: {exc.code}", {"body": body})

        content = raw.get("choices", [{}])[0].get("message", {}).get("content", "")

        if not content and raw.get("choices"):
            # openai-compatible providers may return tool/data blocks; keep fallback deterministic.
            content = json.dumps(raw["choices"][0], ensure_ascii=False)

        extracted = _extract_json_text(content)
        parsed = json.loads(extracted)
        if not isinstance(parsed, dict):
            return _error_payload(role, "invalid_model_payload", "Model returned non-object JSON.", {"content": content})

        return _normalize_result(role, parsed)

    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        return _error_payload(role, "http_error", f"HTTP error: {exc.code}", {"body": body})
    except urllib.error.URLError as exc:
        return _error_payload(role, "network_error", f"Network error: {exc.reason}")
    except json.JSONDecodeError as exc:
        return _error_payload(role, "json_parse_error", "Failed to parse model JSON payload.", {"error": str(exc)})
    except Exception as exc:  # noqa: BLE001
        return _error_payload(role, "unexpected_error", str(exc))
