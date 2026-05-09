def test_models_status_works_without_models_json(client):
    response = client.get("/models/status")

    assert response.status_code == 200
    payload = response.json()
    assert payload["config_file_exists"] is False
    assert "models" in payload
    assert payload["config_error"] is None
