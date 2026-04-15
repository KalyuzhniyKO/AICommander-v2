"""Provider-based role configuration for AICommander v2."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Dict, Optional

DEFAULT_PROVIDER = "openrouter"
DEFAULT_PROVIDER_BASE_URL = "https://openrouter.ai/api/v1"


@dataclass(frozen=True)
class RoleConfig:
    role: str
    provider: str
    model: str
    base_url: str
    api_key: str

    @property
    def is_valid(self) -> bool:
        return bool(self.provider and self.model and self.base_url and self.api_key)


@dataclass(frozen=True)
class AppConfig:
    provider: str
    provider_base_url: str
    provider_api_key: str
    roles: Dict[str, RoleConfig]


def _required(name: str, default: Optional[str] = None) -> str:
    value = os.getenv(name, default)
    if not value:
        raise ValueError(f"Missing required environment variable: {name}")
    return value


def _role_model_env(role: str) -> str:
    return f"AICOMMANDER_{role.upper()}_MODEL"


def load_config() -> AppConfig:
    provider = os.getenv("AICOMMANDER_PROVIDER", DEFAULT_PROVIDER)
    provider_base_url = os.getenv("AICOMMANDER_PROVIDER_BASE_URL", DEFAULT_PROVIDER_BASE_URL)
    provider_api_key = _required("OPENROUTER_API_KEY") if provider == "openrouter" else _required("AICOMMANDER_PROVIDER_API_KEY")

    role_names = ["director", "coder", "reviewer", "qa", "judge"]
    roles: Dict[str, RoleConfig] = {}

    for role in role_names:
        roles[role] = RoleConfig(
            role=role,
            provider=provider,
            model=_required(_role_model_env(role)),
            base_url=provider_base_url,
            api_key=provider_api_key,
        )

    final_provider = os.getenv("AICOMMANDER_FINAL_AUDITOR_PROVIDER", provider)
    final_base_url = os.getenv("AICOMMANDER_FINAL_AUDITOR_BASE_URL", provider_base_url)
    final_api_key = os.getenv("AICOMMANDER_FINAL_AUDITOR_API_KEY", provider_api_key)

    roles["final_auditor"] = RoleConfig(
        role="final_auditor",
        provider=final_provider,
        model=_required("AICOMMANDER_FINAL_AUDITOR_MODEL"),
        base_url=final_base_url,
        api_key=final_api_key,
    )

    return AppConfig(
        provider=provider,
        provider_base_url=provider_base_url,
        provider_api_key=provider_api_key,
        roles=roles,
    )
