import json
import pytest
from fastapi.testclient import TestClient
from backend.app import config as app_config
from backend.app import main as main_app

@pytest.fixture(autouse=True)
def isolated_app(tmp_path,monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY",raising=False)
    monkeypatch.setenv("DATABASE_URL",f"sqlite:///{tmp_path / 'test.db'}")
    models_path=tmp_path / "models.json"
    monkeypatch.setattr(app_config,"DEFAULT_MODELS_PATH",models_path)
    monkeypatch.setattr(main_app,"DEFAULT_MODELS_PATH",models_path)
    from backend.app.orchestration import model_check
    monkeypatch.setattr(model_check,"DEFAULT_MODELS_PATH",models_path)
    main_app.settings=app_config.get_settings()

@pytest.fixture
def client():
    with TestClient(main_app.app) as c:yield c

@pytest.fixture
def write_models_config(tmp_path):
    def write(data):
        path=tmp_path / "models.json"
        path.write_text(data if isinstance(data,str) else json.dumps(data),encoding="utf-8")
        return path
    return write

@pytest.fixture
def minimal_models_config():
    return {r:[f"openrouter/test-{r}"] for r in ("manager","architect","designer","coder","reviewer")}
