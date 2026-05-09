from backend.app import main as app_main
from backend.app.config import get_settings


def test_models_check_without_models_json_returns_config_missing(client):
    response = client.post("/models/check")

    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is False
    assert payload["status"] == "config_missing"
    assert "config/models.json" in payload["error"]


def test_models_check_without_openrouter_key_returns_clear_error(client, write_models_config, minimal_models_config):
    write_models_config(minimal_models_config)

    response = client.post("/models/check")

    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is False
    assert payload["status"] == "openrouter_key_missing"
    assert "OPENROUTER_API_KEY" in payload["error"]
    assert payload["results"]


def test_models_check_rejects_empty_config(client, write_models_config):
    write_models_config("")

    response = client.post("/models/check")

    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is False
    assert payload["status"] == "config_empty"


def test_models_check_rejects_empty_role_models(client, write_models_config, minimal_models_config):
    minimal_models_config["manager"] = []
    write_models_config(minimal_models_config)

    response = client.post("/models/check")

    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is False
    assert payload["status"] == "role_models_empty"


def test_models_check_rejects_model_without_provider_prefix(client, write_models_config, minimal_models_config):
    minimal_models_config["manager"] = ["model-without-provider"]
    write_models_config(minimal_models_config)

    response = client.post("/models/check")

    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is False
    assert payload["status"] == "provider_prefix_missing"


def test_models_check_rejects_unknown_provider(client, write_models_config, minimal_models_config):
    minimal_models_config["manager"] = ["unknown/model"]
    write_models_config(minimal_models_config)

    response = client.post("/models/check")

    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is False
    assert payload["status"] == "provider_unknown"


def test_models_check_uses_current_openrouter_key_setting(client, monkeypatch, write_models_config, minimal_models_config):
    write_models_config(minimal_models_config)
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    app_main.settings = get_settings()

    response = client.post("/models/check")

    assert response.json()["status"] == "openrouter_key_missing"
