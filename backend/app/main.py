"""REST API for the universal AI team orchestrator MVP.

The module exposes a FastAPI `app` when FastAPI is installed and also includes a
stdlib HTTP server fallback so smoke checks can run without third-party packages.
"""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import urlparse

from backend.app.config import DEFAULT_MODELS_PATH, get_settings, load_model_config
from backend.app.orchestration.model_check import check_models
from backend.app.orchestration.premium_review import run_premium_review
from backend.app.orchestration.round_runner import rerun_role, run_round
from backend.app.storage.db import connect, init_db
from backend.app.storage.repositories import Repository

settings = get_settings()


def get_repository() -> Repository:
    conn = connect(settings.database_path)
    init_db(conn)
    return Repository(conn)


def api_health() -> dict[str, Any]:
    return {"status": "ok", "premium_review_enabled": settings.enable_premium_review, "database": str(settings.database_path)}


def api_create_task(payload: dict[str, Any]) -> dict[str, Any]:
    description = str(payload.get("description") or payload.get("task") or "").strip()
    if not description:
        raise ValueError("description is required")
    return get_repository().create_task(description)


def api_get_task(task_id: int) -> dict[str, Any]:
    task = get_repository().get_task(task_id)
    if not task:
        raise ValueError(f"Task {task_id} not found")
    return task


def api_create_round(task_id: int, payload: dict[str, Any]) -> dict[str, Any]:
    return run_round(task_id, str(payload.get("user_comment") or ""), settings, load_model_config(), get_repository())


def api_rerun_role(round_id: int, role: str) -> dict[str, Any]:
    return rerun_role(round_id, role, settings, load_model_config(), get_repository())


def api_premium_review(round_id: int) -> dict[str, Any]:
    return run_premium_review(round_id, settings, load_model_config(), get_repository())


def api_model_check() -> dict[str, Any]:
    return check_models(settings, get_repository())


def api_model_status() -> dict[str, Any]:
    repo = get_repository()
    statuses = repo.list_model_status()
    known = {(item["role"], f"{item['provider']}/{item['model_id']}") for item in statuses}
    for role, models in load_model_config().items():
        for ref in models:
            if "/" in ref and (role, ref) not in known:
                provider, model_id = ref.split("/", 1)
                statuses.append({
                    "provider": provider,
                    "model_id": model_id,
                    "role": role,
                    "status": "unknown",
                    "last_error": "",
                    "last_success_at": None,
                    "last_failure_at": None,
                    "response_time_ms": None,
                })
    return {"models": statuses, "config_file_exists": DEFAULT_MODELS_PATH.exists()}


try:
    from fastapi import FastAPI, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.staticfiles import StaticFiles

    app = FastAPI(title="AICommander AI Team Orchestrator", version="0.1.0")
    app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

    @app.get("/health")
    def health() -> dict[str, Any]:
        return api_health()

    @app.post("/tasks")
    def create_task(payload: dict[str, Any]) -> dict[str, Any]:
        try:
            return api_create_task(payload)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/tasks/{task_id}")
    def get_task(task_id: int) -> dict[str, Any]:
        try:
            return api_get_task(task_id)
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.post("/tasks/{task_id}/rounds")
    def create_round(task_id: int, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        try:
            return api_create_round(task_id, payload or {})
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.post("/rounds/{round_id}/roles/{role}/rerun")
    def rerun(round_id: int, role: str) -> dict[str, Any]:
        try:
            return api_rerun_role(round_id, role)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/rounds/{round_id}/premium-review")
    def premium_review(round_id: int) -> dict[str, Any]:
        try:
            return api_premium_review(round_id)
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.get("/models/status")
    def model_status() -> dict[str, Any]:
        return api_model_status()

    @app.post("/models/check")
    def model_check() -> dict[str, Any]:
        return api_model_check()

    try:
        app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
    except RuntimeError:
        pass
except Exception:
    class StdlibFallbackApp:
        """Placeholder app object when FastAPI is not installed; use run_dev_server() to serve."""

        framework = "stdlib"

    app = StdlibFallbackApp()


class Handler(BaseHTTPRequestHandler):
    def _read_json(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0") or "0")
        if length <= 0:
            return {}
        return json.loads(self.rfile.read(length).decode("utf-8") or "{}")

    def _send(self, status: int, payload: Any) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self) -> None:
        self._send(204, {})

    def do_GET(self) -> None:
        try:
            path = urlparse(self.path).path.strip("/").split("/")
            if self.path == "/health":
                self._send(200, api_health())
            elif self.path == "/models/status":
                self._send(200, api_model_status())
            elif len(path) == 2 and path[0] == "tasks":
                self._send(200, api_get_task(int(path[1])))
            else:
                self._send(404, {"detail": "Not found"})
        except Exception as exc:
            self._send(400, {"detail": str(exc)})

    def do_POST(self) -> None:
        try:
            path = urlparse(self.path).path.strip("/").split("/")
            payload = self._read_json()
            if self.path == "/tasks":
                self._send(200, api_create_task(payload))
            elif len(path) == 3 and path[0] == "tasks" and path[2] == "rounds":
                self._send(200, api_create_round(int(path[1]), payload))
            elif len(path) == 5 and path[0] == "rounds" and path[2] == "roles" and path[4] == "rerun":
                self._send(200, api_rerun_role(int(path[1]), path[3]))
            elif len(path) == 3 and path[0] == "rounds" and path[2] == "premium-review":
                self._send(200, api_premium_review(int(path[1])))
            elif self.path == "/models/check":
                self._send(200, api_model_check())
            else:
                self._send(404, {"detail": "Not found"})
        except Exception as exc:
            self._send(400, {"detail": str(exc)})


def run_dev_server(host: str = "127.0.0.1", port: int = 8000) -> None:
    ThreadingHTTPServer((host, port), Handler).serve_forever()


if __name__ == "__main__":
    run_dev_server()
