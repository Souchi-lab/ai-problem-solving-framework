from __future__ import annotations

import json

from apsf.viewer import api


def test_resolve_viewer_config_response_reports_default_sources(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(api, "VIEWER_CONFIG_PATH", tmp_path / "viewer.config.json")
    monkeypatch.delenv("APSF_VIEWER_ACT_EXECUTION_MODE", raising=False)
    monkeypatch.delenv("APSF_VIEWER_ACT_WRAPPER_BACKEND", raising=False)
    monkeypatch.delenv("APSF_VIEWER_BUILD_WRAPPER_BACKEND", raising=False)

    response = api._resolve_viewer_config_response()

    assert response.config_exists is False
    assert response.execution_mode == "wrapper"
    assert response.execution_mode_source == "default"
    assert response.act_wrapper_backend == "claude-cli"
    assert response.act_wrapper_backend_source == "default"
    assert response.build_wrapper_backend == "claude-cli"
    assert response.build_wrapper_backend_source == "default"


def test_resolve_viewer_config_response_reports_config_sources(monkeypatch, tmp_path) -> None:
    config_path = tmp_path / "viewer.config.json"
    config_path.write_text(
        json.dumps(
            {
                "execution_modes": {"act": "provider"},
                "wrapper_backends": {"act": "codex-cli", "build": "claude-cli"},
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(api, "VIEWER_CONFIG_PATH", config_path)
    monkeypatch.delenv("APSF_VIEWER_ACT_EXECUTION_MODE", raising=False)
    monkeypatch.delenv("APSF_VIEWER_ACT_WRAPPER_BACKEND", raising=False)
    monkeypatch.delenv("APSF_VIEWER_BUILD_WRAPPER_BACKEND", raising=False)

    response = api._resolve_viewer_config_response()

    assert response.config_exists is True
    assert response.execution_mode == "provider"
    assert response.execution_mode_source == "viewer_config"
    assert response.act_wrapper_backend == "codex-cli"
    assert response.act_wrapper_backend_source == "viewer_config"
    assert response.build_wrapper_backend == "claude-cli"
    assert response.build_wrapper_backend_source == "viewer_config"


def test_resolve_viewer_config_response_reports_env_override_sources(monkeypatch, tmp_path) -> None:
    config_path = tmp_path / "viewer.config.json"
    config_path.write_text(
        json.dumps(
            {
                "execution_modes": {"act": "provider"},
                "wrapper_backends": {"act": "claude-cli", "build": "claude-cli"},
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(api, "VIEWER_CONFIG_PATH", config_path)
    monkeypatch.setenv("APSF_VIEWER_ACT_EXECUTION_MODE", "wrapper")
    monkeypatch.setenv("APSF_VIEWER_ACT_WRAPPER_BACKEND", "codex")
    monkeypatch.setenv("APSF_VIEWER_BUILD_WRAPPER_BACKEND", "codex-cli")

    response = api._resolve_viewer_config_response()

    assert response.execution_mode == "wrapper"
    assert response.execution_mode_source == "env"
    assert response.act_wrapper_backend == "codex-cli"
    assert response.act_wrapper_backend_source == "env"
    assert response.build_wrapper_backend == "codex-cli"
    assert response.build_wrapper_backend_source == "env"
