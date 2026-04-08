"""Tests for `apsf model-assignment` CLI command.

run-084: build wrapper model-assignment read
Verifies that the command outputs parseable key=value lines reflecting
the Builder assignment in model-assignment.md.
"""
from __future__ import annotations

import importlib
from pathlib import Path

import pytest
from typer.testing import CliRunner

from apsf.legacy.cli.main import app

runner = CliRunner()


@pytest.fixture(autouse=True)
def reset_settings_singleton():
    """Reset the Settings singleton between tests so APSF_ROOT env changes take effect."""
    import apsf.legacy.config.settings as m
    original = m._settings_instance
    m._settings_instance = None
    yield
    m._settings_instance = original


def _write_run(runs_dir: Path, run_name: str) -> Path:
    run_dir = runs_dir / run_name
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "run_state.json").write_text(
        '{"run_id":"' + run_name + '","current_phase":"BUILD_NEEDED",'
        '"phase_status":"pending","current_owner":"Builder",'
        '"retry_count":0,"last_error":"","active_handoff_id":"","gate_failures":[]}',
        encoding="utf-8",
    )
    return run_dir


def _invoke(monkeypatch, tmp_path: Path, run_name: str, role: str = "Builder") -> str:
    monkeypatch.setenv("APSF_ROOT", str(tmp_path))
    result = runner.invoke(app, ["model-assignment", run_name, "--role", role])
    return result.output.strip()


# ── no model-assignment.md ────────────────────────────────────────────────────

def test_no_model_assignment_file_returns_unset(monkeypatch, tmp_path: Path) -> None:
    _write_run(tmp_path / "runs", "run-084")
    output = _invoke(monkeypatch, tmp_path, "run-084")
    assert "provider=unset" in output
    assert "human=false" in output


# ── anthropic assignment ───────────────────────────────────────────────────────

def test_anthropic_builder_returns_provider_and_model(monkeypatch, tmp_path: Path) -> None:
    run_dir = _write_run(tmp_path / "runs", "run-084")
    (run_dir / "model-assignment.md").write_text(
        "# Model Assignment\n\n"
        "## Role Assignments\n\n"
        "| Role | Provider | Model | Human? | Notes |\n"
        "|---|---|---|---|---|\n"
        "| Builder | anthropic | claude-opus-4-6 | - | main build |\n",
        encoding="utf-8",
    )
    output = _invoke(monkeypatch, tmp_path, "run-084")
    assert "provider=anthropic" in output
    assert "model=claude-opus-4-6" in output
    assert "human=false" in output


# ── human assignment ──────────────────────────────────────────────────────────

def test_human_builder_returns_human_true(monkeypatch, tmp_path: Path) -> None:
    run_dir = _write_run(tmp_path / "runs", "run-084")
    (run_dir / "model-assignment.md").write_text(
        "# Model Assignment\n\n"
        "## Role Assignments\n\n"
        "| Role | Provider | Model | Human? | Notes |\n"
        "|---|---|---|---|---|\n"
        "| Builder | human |  | \u2705 | manual build |\n",
        encoding="utf-8",
    )
    output = _invoke(monkeypatch, tmp_path, "run-084")
    assert "human=true" in output


# ── non-anthropic assignment ──────────────────────────────────────────────────

def test_openai_builder_returns_openai_provider(monkeypatch, tmp_path: Path) -> None:
    run_dir = _write_run(tmp_path / "runs", "run-084")
    (run_dir / "model-assignment.md").write_text(
        "# Model Assignment\n\n"
        "## Role Assignments\n\n"
        "| Role | Provider | Model | Human? | Notes |\n"
        "|---|---|---|---|---|\n"
        "| Builder | openai | gpt-4o | - | |\n",
        encoding="utf-8",
    )
    output = _invoke(monkeypatch, tmp_path, "run-084")
    assert "provider=openai" in output
    assert "model=gpt-4o" in output
    assert "human=false" in output


# ── role not in table ─────────────────────────────────────────────────────────

def test_role_not_in_table_returns_unset(monkeypatch, tmp_path: Path) -> None:
    run_dir = _write_run(tmp_path / "runs", "run-084")
    (run_dir / "model-assignment.md").write_text(
        "# Model Assignment\n\n"
        "## Role Assignments\n\n"
        "| Role | Provider | Model | Human? | Notes |\n"
        "|---|---|---|---|---|\n"
        "| Planner | anthropic | claude-sonnet-4-6 | - | |\n",
        encoding="utf-8",
    )
    output = _invoke(monkeypatch, tmp_path, "run-084", role="Builder")
    assert "provider=unset" in output


# ── unknown role arg ──────────────────────────────────────────────────────────

def test_unknown_role_arg_returns_unset(monkeypatch, tmp_path: Path) -> None:
    _write_run(tmp_path / "runs", "run-084")
    output = _invoke(monkeypatch, tmp_path, "run-084", role="MadeUpRole")
    assert "provider=unset" in output
    assert "human=false" in output


# ── empty model field ─────────────────────────────────────────────────────────

def test_anthropic_without_model_returns_empty_model(monkeypatch, tmp_path: Path) -> None:
    run_dir = _write_run(tmp_path / "runs", "run-084")
    (run_dir / "model-assignment.md").write_text(
        "# Model Assignment\n\n"
        "## Role Assignments\n\n"
        "| Role | Provider | Model | Human? | Notes |\n"
        "|---|---|---|---|---|\n"
        "| Builder | anthropic |  | - | |\n",
        encoding="utf-8",
    )
    output = _invoke(monkeypatch, tmp_path, "run-084")
    assert "provider=anthropic" in output
    assert "model=" in output
    assert "human=false" in output


def test_gemini_builder_returns_unset_when_provider_disabled(monkeypatch, tmp_path: Path) -> None:
    run_dir = _write_run(tmp_path / "runs", "run-084")
    (run_dir / "model-assignment.md").write_text(
        "# Model Assignment\n\n"
        "## Role Assignments\n\n"
        "| Role | Provider | Model | Human? | Notes |\n"
        "|---|---|---|---|---|\n"
        "| Builder | gemini | gemini-2.0-flash | - | disabled |\n",
        encoding="utf-8",
    )
    output = _invoke(monkeypatch, tmp_path, "run-084")
    assert "provider=unset" in output
    assert "human=false" in output
