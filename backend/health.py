"""Health check for provider-based architecture."""

from __future__ import annotations

import json
import tempfile
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict

from .config import AppConfig, RoleConfig


def _check_provider_status(config: AppConfig, timeout: int = 6) -> Dict[str, Any]:
    config_valid = bool(config.provider and config.provider_base_url and config.provider_api_key) and not config.config_errors
    if not config_valid:
        return {
            "status": "config_invalid",
            "provider": config.provider,
            "base_url": config.provider_base_url,
            "api_key_present": bool(config.provider_api_key),
            "endpoint_reachable": False,
            "auth_ok": False,
            "errors": config.config_errors,
        }

    req = urllib.request.Request(
        f"{config.provider_base_url.rstrip('/')}/models",
        method="GET",
        headers={
            "Authorization": f"Bearer {config.provider_api_key}",
            "Content-Type": "application/json",
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            code = response.status
            return {
                "status": "ok",
                "provider": config.provider,
                "base_url": config.provider_base_url,
                "api_key_present": True,
                "endpoint_reachable": True,
                "auth_ok": 200 <= code < 300,
                "http_status": code,
            }
    except urllib.error.HTTPError as exc:
        status = "auth_failed" if exc.code in {401, 403} else "endpoint_reachable"
        return {
            "status": status,
            "provider": config.provider,
            "base_url": config.provider_base_url,
            "api_key_present": True,
            "endpoint_reachable": True,
            "auth_ok": False,
            "http_status": exc.code,
            "error": exc.reason,
        }
    except urllib.error.URLError as exc:
        return {
            "status": "endpoint_unreachable",
            "provider": config.provider,
            "base_url": config.provider_base_url,
            "api_key_present": True,
            "endpoint_reachable": False,
            "auth_ok": False,
            "error": str(exc.reason),
        }


def _role_status(role: RoleConfig) -> Dict[str, Any]:
    return {
        "status": "ok" if role.is_valid else "role_config_invalid",
        "provider": role.provider,
        "model": role.model,
        "base_url": role.base_url,
        "mode": role.mode,
        "config_valid": role.is_valid,
        "errors": role.errors,
    }


def _check_workspace(run_folder: Path) -> Dict[str, Any]:
    try:
        run_folder.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(prefix="health_", suffix=".tmp", dir=run_folder, delete=True) as tmp:
            tmp.write(b"ok")
            tmp.flush()
        return {"status": "ok", "writable": True, "path": str(run_folder.resolve())}
    except Exception as exc:  # noqa: BLE001
        return {"status": "error", "writable": False, "error": str(exc), "path": str(run_folder)}


def _check_orchestration_state(run_folder: Path) -> Dict[str, Any]:
    required = ["director_response.json", "execution.json", "manual_review.json", "team_summary.json"]
    found = [name for name in required if (run_folder / name).exists()]
    return {
        "status": "ok" if len(found) == len(required) else "missing",
        "required": required,
        "found": found,
    }


def health_check(config: AppConfig, run_folder: Path) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "provider_status": _check_provider_status(config),
        "director_role": _role_status(config.roles["director"]),
        "coder_role": _role_status(config.roles["coder"]),
        "reviewer_role": _role_status(config.roles["reviewer"]),
        "qa_role": _role_status(config.roles["qa"]),
        "judge_role": _role_status(config.roles["judge"]),
        "final_auditor_role": _role_status(config.roles["final_auditor"]),
        "workspace_status": _check_workspace(run_folder),
        "orchestration_status": _check_orchestration_state(run_folder),
        "execution_mode": config.execution_mode,
        "legacy_aliases": {
            "coder_node_lenovo": "deprecated",
            "reviewer_node_home_pc": "deprecated",
            "qa_node_home_pc": "deprecated",
        },
    }

    role_payloads = [
        payload["director_role"],
        payload["coder_role"],
        payload["reviewer_role"],
        payload["qa_role"],
        payload["judge_role"],
        payload["final_auditor_role"],
    ]

    payload["role_config_valid"] = all(role["config_valid"] for role in role_payloads)
    payload["final_auditor_config_valid"] = payload["final_auditor_role"]["config_valid"]
    return payload


def print_health_json(config: AppConfig, run_folder: Path) -> None:
    print(json.dumps(health_check(config, run_folder), ensure_ascii=False, indent=2))
