"""Configuration helpers for the AI team orchestrator."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

ROOT_DIR = Path(__file__).resolve().parents[2]
CONFIG_DIR = ROOT_DIR / "config"
DEFAULT_MODELS_PATH = CONFIG_DIR / "models.json"
EXAMPLE_MODELS_PATH = CONFIG_DIR / "models.example.json"


@dataclass(frozen=True)
class Settings:
    openrouter_api_key: str = ""
    openai_api_key: str = ""
    enable_premium_review: bool = False
    default_timeout_seconds: int = 60
    max_model_retries: int = 1
    database_url: str = "sqlite:///./aicommander.db"
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openai_base_url: str = "https://api.openai.com/v1"

    @property
    def database_path(self) -> Path:
        prefix = "sqlite:///"
        if self.database_url.startswith(prefix):
            raw = self.database_url[len(prefix) :]
            path = Path(raw)
            if not path.is_absolute():
                return ROOT_DIR / path
            return path
        return ROOT_DIR / "aicommander.db"


def _bool_env(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _int_env(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except ValueError:
        return default


def load_dotenv(path: Path | None = None) -> None:
    """Tiny .env loader so the MVP does not require python-dotenv."""
    env_path = path or (ROOT_DIR / ".env")
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


def get_settings() -> Settings:
    load_dotenv()
    return Settings(
        openrouter_api_key=os.getenv("OPENROUTER_API_KEY", ""),
        openai_api_key=os.getenv("OPENAI_API_KEY", ""),
        enable_premium_review=_bool_env("ENABLE_PREMIUM_REVIEW", False),
        default_timeout_seconds=_int_env("DEFAULT_TIMEOUT_SECONDS", 60),
        max_model_retries=max(1, _int_env("MAX_MODEL_RETRIES", 1)),
        database_url=os.getenv("DATABASE_URL", "sqlite:///./aicommander.db"),
        openrouter_base_url=os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
        openai_base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
    )


def load_model_config(path: Path | None = None) -> Dict[str, List[str]]:
    model_path = path or DEFAULT_MODELS_PATH
    if not model_path.exists():
        model_path = EXAMPLE_MODELS_PATH
    if not model_path.exists():
        return {}
    data = json.loads(model_path.read_text(encoding="utf-8"))
    return {str(role): [str(model) for model in models] for role, models in data.items() if isinstance(models, list)}
