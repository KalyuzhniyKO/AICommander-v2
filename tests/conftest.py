from __future__ import annotations

import json
import sys
import threading
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app import config as app_config
from backend.app.config import get_settings
from backend.app import main as app_main


class ApiClient:
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")

    def get(self, path: str):
        return self._request("GET", path)

    def post(self, path: str, json: dict | None = None):
        return self._request("POST", path, json)

    def _request(self, method: str, path: str, payload: dict | None = None):
        data = None
        headers = {}
        if payload is not None:
            data = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json"
        request = urllib.request.Request(f"{self.base_url}{path}", data=data, method=method, headers=headers)
        try:
            with urllib.request.urlopen(request, timeout=10) as response:
                return ApiResponse(response.status, response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            return ApiResponse(exc.code, exc.read().decode("utf-8"))


class ApiResponse:
    def __init__(self, status_code: int, body: str) -> None:
        self.status_code = status_code
        self._body = body

    def json(self):
        return json.loads(self._body or "{}")


@pytest.fixture(autouse=True)
def isolated_app(tmp_path, monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("ENABLE_PREMIUM_REVIEW", raising=False)
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'test.db'}")
    app_main.settings = get_settings()

    models_path = app_config.DEFAULT_MODELS_PATH
    backup = models_path.read_text(encoding="utf-8") if models_path.exists() else None
    if models_path.exists():
        models_path.unlink()
    yield
    if models_path.exists():
        models_path.unlink()
    if backup is not None:
        models_path.write_text(backup, encoding="utf-8")


@pytest.fixture
def client():
    server = ThreadingHTTPServer(("127.0.0.1", 0), app_main.Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        host, port = server.server_address
        yield ApiClient(f"http://{host}:{port}")
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


@pytest.fixture
def write_models_config():
    def _write(payload):
        app_config.CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        if isinstance(payload, str):
            app_config.DEFAULT_MODELS_PATH.write_text(payload, encoding="utf-8")
        else:
            app_config.DEFAULT_MODELS_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return app_config.DEFAULT_MODELS_PATH

    return _write


@pytest.fixture
def minimal_models_config():
    return {
        "manager": ["openrouter/test-manager"],
        "architect": ["openrouter/test-architect"],
        "designer": ["openrouter/test-designer"],
        "coder": ["openrouter/test-coder"],
        "reviewer": ["openrouter/test-reviewer"],
        "premium_reviewer": ["openai/test-premium"],
    }
