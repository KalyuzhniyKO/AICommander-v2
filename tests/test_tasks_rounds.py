def test_task_round_flow_without_keys_saves_fallbacks_and_errors(client):
    task_response = client.post("/tasks", json={"description": "Сделать web-приложение для заметок"})
    assert task_response.status_code == 200
    task = task_response.json()
    assert task["id"]

    round_response = client.post(f"/tasks/{task['id']}/rounds", json={"user_comment": "первый раунд"})
    assert round_response.status_code == 200
    round_payload = round_response.json()
    assert round_payload["task_id"] == task["id"]
    assert round_payload["role_outputs"]
    assert any(output["status"] == "failed" for output in round_payload["role_outputs"])

    fetched_response = client.get(f"/tasks/{task['id']}")
    assert fetched_response.status_code == 200
    fetched_task = fetched_response.json()
    assert fetched_task["id"] == task["id"]
    assert fetched_task["rounds"]
    assert fetched_task["rounds"][0]["role_outputs"]
    assert any(
        output["model_errors"]
        for output in fetched_task["rounds"][0]["role_outputs"]
    )
