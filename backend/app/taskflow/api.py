"""Separate API namespace; legacy foundation endpoints stay unchanged."""
from fastapi import APIRouter, Depends, HTTPException

from backend.app.storage.repositories import Repository
from .models import CreateRun, Command, OwnerDecision, RunSnapshot
from .service import FlowError, Taskflow


def create_router(repository_dependency):
    router = APIRouter(prefix='/taskflow', tags=['offline-taskflow'])

    def invoke(repo, method, *args):
        try:
            return getattr(Taskflow(repo.conn), method)(*args)
        except FlowError as exc:
            raise HTTPException(status_code=exc.status_code, detail={'code': exc.code, 'message': str(exc)}) from exc

    @router.post('/tasks/{task_id}/runs', response_model=RunSnapshot)
    def create(task_id: int, payload: CreateRun, repo: Repository = Depends(repository_dependency)):
        return invoke(repo, 'create', task_id, payload)

    @router.get('/tasks/{task_id}/runs', response_model=list[RunSnapshot])
    def list_runs(task_id: int, repo: Repository = Depends(repository_dependency)):
        return invoke(repo, 'list_for_task', task_id)

    @router.get('/runs/{run_id}', response_model=RunSnapshot)
    def get(run_id: int, repo: Repository = Depends(repository_dependency)):
        return invoke(repo, 'get', run_id)

    @router.post('/runs/{run_id}/commands', response_model=RunSnapshot)
    def command(run_id: int, payload: Command, repo: Repository = Depends(repository_dependency)):
        return invoke(repo, 'apply', run_id, payload)

    @router.post('/runs/{run_id}/owner-decision', response_model=RunSnapshot)
    def owner_decision(run_id: int, payload: OwnerDecision, repo: Repository = Depends(repository_dependency)):
        return invoke(repo, 'apply', run_id, payload)

    return router
