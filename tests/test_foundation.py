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
