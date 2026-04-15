"""Health check for provider-based architecture."""

from __future__ import annotations

import json
import os
import tempfile
import urllib.request
from pathlib import Path
from typing import Any, Dict

from .config import AppConfig


def _check_provider_reachable(base_url: str, timeout: int = 5) -> Dict[str, Any]:
    try:
        request = urllib.request.Request(f"{base_url.rstrip('/')}/models", method="GET")
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return {"ok": 200 <= response.status < 500, "status_code": response.status}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": str(exc)}


def _check_workspace(run_folder: Path) -> Dict[str, Any]:
    try:
        run_folder.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(prefix="health_", suffix=".tmp", dir=run_folder, delete=True) as tmp:
            tmp.write(b"ok")
            tmp.flush()
        return {"ok": True, "path": str(run_folder.resolve())}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": str(exc), "path": str(run_folder)}


def _check_orchestration_state(run_folder: Path) -> Dict[str, Any]:
    required = ["director_response.json", "execution.json", "manual_review.json", "team_summary.json"]
    found = [name for name in required if (run_folder / name).exists()]
    return {"ok": len(found) >= 1, "required": required, "found": found}


def health_check(config: AppConfig, run_folder: Path) -> Dict[str, Any]:
    role_status = {
        f"{role_name}_role": {
            "provider": role.provider,
            "model": role.model,
            "base_url": role.base_url,
            "valid": role.is_valid,
        }
        for role_name, role in config.roles.items()
    }

    payload: Dict[str, Any] = {
        "provider_status": {
            "provider": config.provider,
            "api_key_present": bool(config.provider_api_key),
            "reachable": _check_provider_reachable(config.provider_base_url),
        },
        **role_status,
        "workspace_status": _check_workspace(run_folder),
        "orchestration_status": _check_orchestration_state(run_folder),
        "legacy_aliases": {
            "coder_node_lenovo": "deprecated",
            "reviewer_node_home_pc": "deprecated",
            "qa_node_home_pc": "deprecated",
        },
    }

    payload["role_config_valid"] = all(v.get("valid") for k, v in payload.items() if k.endswith("_role"))
    payload["final_auditor_config_valid"] = payload["final_auditor_role"]["valid"]
    return payload


def print_health_json(config: AppConfig, run_folder: Path) -> None:
    print(json.dumps(health_check(config, run_folder), ensure_ascii=False, indent=2))
