"""Final auditor role execution."""

from __future__ import annotations

import json
import urllib.request
from dataclasses import asdict
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


def run_final_auditor(role: RoleConfig, payload: Dict[str, Any], timeout: int = 30) -> Dict[str, Any]:
    req_body = {
        "model": role.model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": _build_prompt(payload)},
        ],
        "response_format": {"type": "json_object"},
    }

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
        raw = json.loads(response.read().decode("utf-8"))

    content = raw["choices"][0]["message"]["content"]
    parsed = json.loads(content)

    return {
        "status": "ok",
        "final_verdict": parsed.get("final_verdict", "revise"),
        "stakeholder_summary": parsed.get("stakeholder_summary", ""),
        "critical_issues": parsed.get("critical_issues", []),
        "recommendation": parsed.get("recommendation", ""),
        "requires_revision": bool(parsed.get("requires_revision", False)),
        "role": asdict(role),
    }
