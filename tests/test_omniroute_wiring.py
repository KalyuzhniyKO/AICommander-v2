"""Application wiring uses mocks and temporary SQLite, never live credentials."""
from dataclasses import replace
from unittest.mock import Mock

import pytest

from backend.app.config import ModelConfigError, load_model_config
from backend.app.orchestration.fallback import run_with_fallback
from backend.app.providers.base import ChatMessage, ChatResult
from backend.app.providers.omniroute import OmniRouteConfig, OmniRouteError


def test_model_ref_accepts_exact_omniroute_route(write_models_config):
    path = write_models_config({"coder": ["omniroute/synthetic/model"]})
    assert load_model_config(path) == {"coder": ["omniroute/synthetic/model"]}


@pytest.mark.parametrize("refs", [["omniroute/a", "omniroute/b"], ["openrouter/a", "omniroute/b"]])
def test_omniroute_role_cannot_have_second_routing_loop(write_models_config, refs):
    with pytest.raises(ModelConfigError) as exc:
        load_model_config(write_models_config({"coder": refs}))
    assert exc.value.status == "omniroute_single_route"


@pytest.mark.parametrize("failure", [OmniRouteError("timeout"), OmniRouteError("rate_limited", 429), OmniRouteError("disabled"), RuntimeError("synthetic-private-credential")])
def test_omniroute_failure_never_replays_or_calls_direct_provider(repository, failure):
    omni, direct = Mock(), Mock()
    omni.chat.side_effect = failure
    outcome = run_with_fallback(role="coder", model_refs=["omniroute/synthetic/model", "openrouter/backup"],
        messages=[ChatMessage("user", "test")], timeout_seconds=2, max_attempts_per_model=8,
        repository=repository, round_id=None, openrouter=direct, omniroute=omni)
    assert not outcome.success and len(outcome.errors) == 1
    assert omni.chat.call_count == 1
    direct.chat.assert_not_called()
    assert repository.list_model_status()[0]["provider"] == "omniroute"
    assert "synthetic-private-credential" not in str(repository.list_model_status())


def test_manual_model_check_uses_omniroute_without_openrouter_key(client, monkeypatch, write_models_config):
    from backend.app import main
    from backend.app.orchestration import model_check
    write_models_config({"coder": ["omniroute/synthetic/model"]})
    config = OmniRouteConfig(enabled=True, base_url="https://gateway.invalid", api_key="synthetic-key")
    monkeypatch.setattr(main, "settings", replace(main.settings, omniroute=config))
    omni, direct = Mock(), Mock()
    omni.chat.return_value = ChatResult("omniroute", "synthetic/model", "OK", 5)
    monkeypatch.setattr(model_check, "OmniRouteProvider", lambda cfg: omni)
    monkeypatch.setattr(model_check, "OpenRouterProvider", lambda *args: direct)
    checked = client.post("/models/check").json()
    assert checked["ok"] and checked["results"][0]["provider"] == "omniroute"
    assert omni.chat.call_args.kwargs["model_id"] == "synthetic/model"
    direct.chat.assert_not_called()
    assert client.get("/models/status").json()["models"][0]["provider"] == "omniroute"


def test_disabled_omniroute_model_check_has_useful_error_and_no_network(client, write_models_config):
    write_models_config({"coder": ["omniroute/synthetic/model"]})
    checked = client.post("/models/check").json()
    assert not checked["ok"]
    assert "OMNIROUTE_ENABLED" in checked["results"][0]["last_error"]


def test_live_smoke_needs_opt_in_and_inference_needs_second_flag(monkeypatch, capsys):
    from backend.app.providers import omniroute_smoke
    factory = Mock()
    monkeypatch.setattr(omniroute_smoke, "OmniRouteProvider", factory)
    assert omniroute_smoke.main() == 2
    factory.assert_not_called()
    monkeypatch.setenv("OMNIROUTE_RUN_LIVE_SMOKE", "true")
    factory.return_value.health.return_value = {"status": "ok"}
    factory.return_value.models.return_value = ["synthetic/model"]
    assert omniroute_smoke.main() == 0
    factory.return_value.chat.assert_not_called()
    monkeypatch.setenv("OMNIROUTE_SMOKE_INFERENCE", "true")
    monkeypatch.setenv("OMNIROUTE_SMOKE_MODEL", "synthetic/model")
    factory.return_value.chat.return_value = ChatResult("omniroute", "synthetic/model", "OK", 1)
    assert omniroute_smoke.main() == 0
    assert factory.return_value.chat.call_count == 1
    assert factory.call_args.args[0].max_output_tokens == 64
    assert "synthetic/model" not in capsys.readouterr().out


def test_legacy_round_and_explicit_rerun_use_exact_omniroute_route(client, monkeypatch, write_models_config):
    from backend.app.orchestration import round_runner
    write_models_config({"manager": ["omniroute/synthetic/model"], "reviewer": ["omniroute/synthetic/reviewer"]})
    omni, direct = Mock(), Mock()
    omni.chat.side_effect = [ChatResult("omniroute", "synthetic/model", "plan", 1),
                             OmniRouteError("timeout"), ChatResult("omniroute", "synthetic/reviewer", "review", 1)]
    monkeypatch.setattr(round_runner, "OmniRouteProvider", lambda cfg: omni)
    monkeypatch.setattr(round_runner, "OpenRouterProvider", lambda *args: direct)
    task = client.post("/tasks", json={"description": "Write docs"}).json()
    rnd = client.post(f"/tasks/{task['id']}/rounds", json={"user_comment": "test"}).json()
    assert [o["status"] for o in rnd["role_outputs"]] == ["completed", "failed"]
    retried = client.post(f"/rounds/{rnd['id']}/roles/reviewer/rerun").json()
    assert [o["status"] for o in retried["role_outputs"]] == ["completed", "completed"]
    assert all(o["provider"] == "omniroute" for o in retried["role_outputs"])
    assert omni.chat.call_count == 3
    direct.chat.assert_not_called()
