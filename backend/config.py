"""Provider-based role configuration for AICommander v2."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Dict, List

DEFAULT_PROVIDER = "openrouter"
DEFAULT_PROVIDER_BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_EXECUTION_MODE = "balanced"
EXECUTION_MODES = {"cheap", "balanced", "premium"}


@dataclass(frozen=True)
class RoleConfig:
    role: str
    provider: str
    model: str
    base_url: str
    api_key: str
    mode: str
    errors: List[str] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return bool(self.provider and self.model and self.base_url and self.api_key) and not self.errors


@dataclass(frozen=True)
class AppConfig:
    provider: str
    provider_base_url: str
    provider_api_key: str
    execution_mode: str
    roles: Dict[str, RoleConfig]
    config_errors: List[str] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return not self.config_errors and all(role.is_valid for role in self.roles.values())


def _env(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


def _resolve_mode(mode_override: str | None = None) -> tuple[str, List[str]]:
    mode = (mode_override or _env("AICOMMANDER_EXECUTION_MODE", DEFAULT_EXECUTION_MODE)).lower()
    if mode in EXECUTION_MODES:
        return mode, []
    return DEFAULT_EXECUTION_MODE, [
        f"Invalid execution mode '{mode}'. Allowed: cheap|balanced|premium. Fallback: {DEFAULT_EXECUTION_MODE}."
    ]


def _resolve_model(role: str, mode: str) -> tuple[str, str]:
    by_mode_env = f"AICOMMANDER_{role.upper()}_MODEL_{mode.upper()}"
    by_role_env = f"AICOMMANDER_{role.upper()}_MODEL"

    model = _env(by_mode_env)
    if model:
        return model, by_mode_env

    model = _env(by_role_env)
    if model:
        return model, by_role_env

    return "", f"{by_mode_env}|{by_role_env}"


def _build_role_config(role: str, provider: str, base_url: str, api_key: str, mode: str) -> RoleConfig:
    model, source = _resolve_model(role, mode)
    errors: List[str] = []

    if not model:
        errors.append(f"Model is not configured for role='{role}', mode='{mode}' (expected {source}).")
    if not provider:
        errors.append(f"Provider is empty for role='{role}'.")
    if not base_url:
        errors.append(f"Base URL is empty for role='{role}'.")
    if not api_key:
        errors.append(f"API key is empty for role='{role}'.")

    return RoleConfig(
        role=role,
        provider=provider,
        model=model,
        base_url=base_url,
        api_key=api_key,
        mode=mode,
        errors=errors,
    )


def load_config(strict: bool = True, mode_override: str | None = None) -> AppConfig:
    mode, mode_errors = _resolve_mode(mode_override=mode_override)

    provider = _env("AICOMMANDER_PROVIDER", DEFAULT_PROVIDER)
    provider_base_url = _env("AICOMMANDER_PROVIDER_BASE_URL", DEFAULT_PROVIDER_BASE_URL)

    if provider == "openrouter":
        provider_api_key = _env("OPENROUTER_API_KEY")
        provider_key_source = "OPENROUTER_API_KEY"
    else:
        provider_api_key = _env("AICOMMANDER_PROVIDER_API_KEY")
        provider_key_source = "AICOMMANDER_PROVIDER_API_KEY"

    config_errors: List[str] = []
    if not provider:
        config_errors.append("AICOMMANDER_PROVIDER is empty.")
    if not provider_base_url:
        config_errors.append("AICOMMANDER_PROVIDER_BASE_URL is empty.")
    if not provider_api_key:
        config_errors.append(f"Provider API key is empty ({provider_key_source}).")
    config_errors.extend(mode_errors)

    role_names = ["director", "coder", "reviewer", "qa", "judge"]
    roles: Dict[str, RoleConfig] = {
        role: _build_role_config(
            role=role,
            provider=provider,
            base_url=provider_base_url,
            api_key=provider_api_key,
            mode=mode,
        )
        for role in role_names
    }

    final_provider = _env("AICOMMANDER_FINAL_AUDITOR_PROVIDER", provider)
    final_base_url = _env("AICOMMANDER_FINAL_AUDITOR_BASE_URL", provider_base_url)
    final_api_key = _env("AICOMMANDER_FINAL_AUDITOR_API_KEY", provider_api_key)

    roles["final_auditor"] = _build_role_config(
        role="final_auditor",
        provider=final_provider,
        base_url=final_base_url,
        api_key=final_api_key,
        mode=mode,
    )

    app = AppConfig(
        provider=provider,
        provider_base_url=provider_base_url,
        provider_api_key=provider_api_key,
        execution_mode=mode,
        roles=roles,
        config_errors=config_errors,
    )

    if strict and not app.is_valid:
        errors = app.config_errors + [err for role in app.roles.values() for err in role.errors]
        raise ValueError("Invalid AICommander config: " + "; ".join(errors))

    return app
