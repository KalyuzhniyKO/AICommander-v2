from backend.app import main as app_main
from backend.app.config import get_settings


def test_premium_review_without_openai_key_is_skipped(client, monkeypatch, write_models_config, minimal_models_config):
    write_models_config(minimal_models_config)
    monkeypatch.setenv("ENABLE_PREMIUM_REVIEW", "true")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    app_main.settings = get_settings()

    task = client.post("/tasks", json={"description": "Сделать лендинг"}).json()
    round_payload = client.post(f"/tasks/{task['id']}/rounds", json={}).json()

    response = client.post(f"/rounds/{round_payload['id']}/premium-review")

    assert response.status_code == 200
    payload = response.json()
    assert payload["premium_review_status"] in {"skipped_disabled", "skipped_not_configured"}
    assert "OPENAI_API_KEY" in payload["premium_review_output"] or payload["premium_review_status"] == "skipped_disabled"
