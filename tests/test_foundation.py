def test_health(client):
    data=client.get("/health")
    assert data.status_code==200
    assert data.json()["foundation"] is True

def test_status_empty(client):
    r=client.get("/models/status")
    assert r.status_code==200
    assert r.json()["config_file_exists"] is False

def test_task_round_without_api_key(client):
    task=client.post("/tasks",json={"description":"Сделать складской API"}).json()
    result=client.post(f"/tasks/{task['id']}/rounds",json={"user_comment":"Начни с требований"})
    assert result.status_code==200
    outputs=result.json()["role_outputs"]
    assert outputs and all(x["status"]=="failed" for x in outputs)
    saved=client.get(f"/tasks/{task['id']}").json()
    assert saved["rounds"][0]["role_outputs"]

def test_missing_model_config(client):
    r=client.post("/models/check")
    assert r.status_code==200
    assert r.json()["status"]=="config_missing"

def test_validation_missing_provider(client,write_models_config,minimal_models_config):
    minimal_models_config["manager"]=["wrong"]
    write_models_config(minimal_models_config)
    r=client.post("/models/check")
    assert r.status_code==200
    assert r.json()["status"]=="provider_prefix_missing"

def test_unauthorized_model_status_without_key(client,write_models_config,minimal_models_config):
    write_models_config(minimal_models_config)
    r=client.post("/models/check")
    assert r.status_code==200
    assert r.json()["status"]=="openrouter_key_missing"
from unittest.mock import Mock

import pytest

from backend.app.providers.base import ChatResult, ProviderError



def test_frontend_is_served(client):
    assert client.get("/").status_code == 200
    assert client.get("/app.js").status_code == 200


@pytest.mark.parametrize("data,status", [
    ("", "config_empty"), ("{", "config_invalid"),
    ({"unknown": ["openrouter/test"]}, "role_unknown"),
    ({"coder": []}, "role_models_empty"),
    ({"coder": ["other/test"]}, "provider_unknown"),
    ({"coder": ["openrouter/"]}, "model_id_empty"),
])
def test_invalid_model_config(client, write_models_config, data, status):
    write_models_config(data)
    checked = client.post("/models/check").json()
    assert checked["status"] == status and checked["ok"] is False
    assert client.get("/models/status").json()["config_error"]["status"] == status


def test_model_check_mixed_results_persist(client, write_models_config, monkeypatch):
    from backend.app import main
    from backend.app.config import Settings
    from backend.app.orchestration import model_check
    write_models_config({"coder": ["openrouter/good", "openrouter/bad"]})
    monkeypatch.setattr(main, "settings", Settings(openrouter_api_key="test-key", database_url=main.settings.database_url))
    provider = Mock()
    provider.chat.side_effect = [ChatResult("openrouter", "good", "OK", 1), ProviderError("timeout", "timeout")]
    monkeypatch.setattr(model_check, "OpenRouterProvider", lambda *args: provider)
    checked = client.post("/models/check").json()
    assert checked["status"] == "completed" and checked["ok"] is False
    assert [r["status"] for r in checked["results"]] == ["available", "failed"]
    stored = {m["model_id"]: m["status"] for m in client.get("/models/status").json()["models"]}
    assert stored == {"good": "available", "bad": "failed"}


def test_successful_round_and_rerun_update_history(client, write_models_config, monkeypatch):
    from backend.app.orchestration import round_runner
    write_models_config({"manager": ["openrouter/manager"], "reviewer": ["openrouter/reviewer"]})
    provider = Mock()
    provider.chat.side_effect = [
        ChatResult("openrouter", "manager", "plan", 1),
        ProviderError("timeout", "timeout"),
        ChatResult("openrouter", "reviewer", "review fixed", 2),
    ]
    monkeypatch.setattr(round_runner, "OpenRouterProvider", lambda *args: provider)
    task = client.post("/tasks", json={"description": "Write docs"}).json()
    rnd = client.post(f"/tasks/{task['id']}/rounds", json={"user_comment": "check it"}).json()
    assert [o["status"] for o in rnd["role_outputs"]] == ["completed", "failed"]
    retried = client.post(f"/rounds/{rnd['id']}/roles/reviewer/rerun").json()
    assert [o["status"] for o in retried["role_outputs"]] == ["completed", "completed"]
    assert retried["summary"] == "manager: plan\nreviewer: review fixed"
    history = client.get(f"/tasks/{task['id']}").json()["rounds"]
    assert len(history) == 1 and len(history[0]["role_outputs"]) == 2
    assert history[0]["role_outputs"][1]["model_errors"]
    assert provider.chat.call_count == 3
