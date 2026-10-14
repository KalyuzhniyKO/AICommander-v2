"""AICommander v3 local foundation. No Hermes/Codex integration yet."""
from __future__ import annotations
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from backend.app.config import get_settings, load_model_config, ModelConfigError, DEFAULT_MODELS_PATH
from backend.app.orchestration.round_runner import run_round, rerun_role
from backend.app.orchestration.model_check import check_models
from backend.app.storage.db import connect, init_db
from backend.app.storage.repositories import Repository

app=FastAPI(title="AICommander v3 Foundation", version="3.0.0-dev")
settings=get_settings()

def repository():
    conn=connect(settings.database_path)
    init_db(conn)
    return Repository(conn)

@app.get("/health")
def health():
    return {"status":"ok","foundation":True,"hermes_connected":False,"omnirouter_connected":False}

@app.post("/tasks")
def create_task(payload:dict):
    description=str(payload.get("description") or "").strip()
    if not description:
        raise HTTPException(status_code=400, detail="description required")
    return repository().create_task(description)

@app.get("/tasks/{task_id}")
def get_task(task_id:int):
    task=repository().get_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@app.post("/tasks/{task_id}/rounds")
def create_round(task_id:int,payload:dict|None=None):
    try:
        models=load_model_config()
    except ModelConfigError:
        models={}
    try:
        return run_round(task_id,str((payload or {}).get("user_comment") or ""),settings,models,repository())
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.post("/rounds/{round_id}/roles/{role}/rerun")
def rerun(round_id:int,role:str):
    try:
        return rerun_role(round_id,role,settings,load_model_config(),repository())
    except (ValueError,ModelConfigError) as e:
        raise HTTPException(status_code=400,detail=str(e))

@app.get("/models/status")
def model_status():
    stored=repository().list_model_status()
    try:
        configured=load_model_config()
        config_error=None
    except ModelConfigError as e:
        configured={}
        config_error=e.to_dict()
    keys={(m["role"],m["provider"],m["model_id"]) for m in stored}
    for role,refs in configured.items():
        for ref in refs:
            provider,mid=ref.split("/",1)
            if (role,provider,mid) not in keys:
                stored.append({"role":role,"provider":provider,"model_id":mid,"status":"unknown"})
    return {"models":stored,"config_file_exists":DEFAULT_MODELS_PATH.exists(),"config_error":config_error}

@app.post("/models/check")
def model_check():
    return check_models(settings,repository())

app.mount("/",StaticFiles(directory=str(Path(__file__).resolve().parents[2] / "frontend"),html=True),name="frontend")

if __name__=="__main__":
    import uvicorn
    uvicorn.run(app,host="127.0.0.1",port=8000)
