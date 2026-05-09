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

KNOWN_MODEL_ROLES = {"manager", "architect", "designer", "coder", "reviewer", "premium_reviewer"}
REQUIRED_MODEL_ROLES = {"manager", "architect", "designer", "coder", "reviewer"}
KNOWN_PROVIDERS = {"openrouter", "openai"}


@dataclass(frozen=True)
class ModelConfigIssue:
    status: str
    error: str
    hint: str = ""


class ModelConfigError(ValueError):
    """Raised when model config exists but cannot be safely used."""

    def __init__(self, issue: ModelConfigIssue) -> None:
        super().__init__(issue.error)
        self.status = issue.status
        self.error = issue.error
        self.hint = issue.hint

    def to_dict(self) -> dict[str, str]:
        payload = {"status": self.status, "error": self.error}
        if self.hint:
            payload["hint"] = self.hint
        return payload


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


def models_config_missing_payload() -> dict[str, object]:
    return {
        "ok": False,
        "status": "config_missing",
        "error": (
            "Файл config/models.json не найден. Скопируйте config/models.example.json в config/models.json "
            "и при необходимости отредактируйте список моделей."
        ),
        "hint": f"cp {EXAMPLE_MODELS_PATH.relative_to(ROOT_DIR)} {DEFAULT_MODELS_PATH.relative_to(ROOT_DIR)}",
        "results": [],
    }


def _read_model_config(path: Path) -> object:
    try:
        raw = path.read_text(encoding="utf-8").strip()
    except OSError as exc:
        raise ModelConfigError(ModelConfigIssue("config_unreadable", f"Не удалось прочитать {path}: {exc}")) from exc
    if not raw:
        raise ModelConfigError(ModelConfigIssue("config_empty", f"Файл {path.relative_to(ROOT_DIR)} пустой.", "Заполните JSON-объект ролями и fallback-списками моделей."))
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ModelConfigError(ModelConfigIssue("config_invalid", f"Не удалось разобрать JSON в {path.relative_to(ROOT_DIR)}: {exc}", "Проверьте синтаксис или заново скопируйте config/models.example.json.")) from exc


def validate_model_config(data: object, path: Path | None = None) -> Dict[str, List[str]]:
    """Validate model fallback chains and return normalized role -> refs mapping."""
    display_path = path.relative_to(ROOT_DIR) if path and path.is_relative_to(ROOT_DIR) else path or DEFAULT_MODELS_PATH
    if not isinstance(data, dict):
        raise ModelConfigError(ModelConfigIssue("config_invalid", f"{display_path} должен содержать JSON-объект: роль -> список моделей."))
    if not data:
        raise ModelConfigError(ModelConfigIssue("config_empty", f"{display_path} не содержит ни одной роли.", "Добавьте роли manager, architect, designer, coder и reviewer."))

    normalized: Dict[str, List[str]] = {}
    for role, models in data.items():
        role_name = str(role).strip()
        if role_name not in KNOWN_MODEL_ROLES:
            raise ModelConfigError(ModelConfigIssue("role_unknown", f"Неизвестная роль в конфигурации моделей: {role_name}.", f"Допустимые роли: {', '.join(sorted(KNOWN_MODEL_ROLES))}."))
        if not isinstance(models, list):
            raise ModelConfigError(ModelConfigIssue("role_models_invalid", f"Для роли {role_name} должен быть список model refs."))
        if not models:
            raise ModelConfigError(ModelConfigIssue("role_models_empty", f"Для роли {role_name} список моделей пустой.", "Добавьте хотя бы одну модель в формате provider/model_id."))
        normalized_refs: list[str] = []
        for model in models:
            ref = str(model).strip()
            if not ref:
                raise ModelConfigError(ModelConfigIssue("model_ref_empty", f"Для роли {role_name} указан пустой model ref."))
            if "/" not in ref:
                raise ModelConfigError(ModelConfigIssue("provider_prefix_missing", f"Для роли {role_name} модель '{ref}' указана без provider prefix.", "Используйте формат openrouter/<model_id> или openai/<model_id> для optional Premium Review."))
            provider, model_id = ref.split("/", 1)
            if provider not in KNOWN_PROVIDERS:
                raise ModelConfigError(ModelConfigIssue("provider_unknown", f"Неизвестный provider '{provider}' для модели '{ref}'.", f"Поддерживаются providers: {', '.join(sorted(KNOWN_PROVIDERS))}."))
            if not model_id.strip():
                raise ModelConfigError(ModelConfigIssue("model_id_empty", f"Для роли {role_name} в ref '{ref}' отсутствует model_id."))
            normalized_refs.append(f"{provider}/{model_id.strip()}")
        normalized[role_name] = normalized_refs
    return normalized


def load_model_config(path: Path | None = None, *, allow_example: bool = True, validate: bool = True) -> Dict[str, List[str]]:
    model_path = path or DEFAULT_MODELS_PATH
    if not model_path.exists():
        if allow_example and path is None and EXAMPLE_MODELS_PATH.exists():
            model_path = EXAMPLE_MODELS_PATH
        else:
            return {}
    data = _read_model_config(model_path)
    if validate:
        return validate_model_config(data, model_path)
    if not isinstance(data, dict):
        return {}
    return {str(role): [str(model) for model in models] for role, models in data.items() if isinstance(models, list)}
