from __future__ import annotations

import json
import os
from pathlib import Path

import apsf.legacy.config.settings as settings_module
import pytest
from typer.testing import CliRunner

from apsf.legacy.cli.main import app

runner = CliRunner()


@pytest.fixture(autouse=True)
def reset_settings_singleton():
    settings_module._settings_instance = None
    yield
    settings_module._settings_instance = None


def _setup_env(tmp_path: Path) -> None:
    template_dir = tmp_path / "runs" / "_template"
    template_dir.mkdir(parents=True)
    for fname in [
        "execution-assignment.md",
        "goal.md",
        "plan.md",
        "build.md",
        "review.md",
        "improve.md",
        "result.md",
    ]:
        (template_dir / fname).write_text(f"# {fname}\n", encoding="utf-8")


def _fill_file(run_dir: Path, filename: str, lines: int = 5) -> None:
    content = "\n".join([f"Real content line {i}" for i in range(lines)]) + "\n"
    (run_dir / filename).write_text(content, encoding="utf-8")


def _invoke_next(tmp_path: Path, run_name: str, args: list[str] | None = None):
    env = {**os.environ, "APSF_ROOT": str(tmp_path)}
    return runner.invoke(app, ["next", run_name] + (args or []), env=env)


def test_next_syncs_stale_run_state_via_transition_service(tmp_path: Path) -> None:
    _setup_env(tmp_path)
    run_name = "2099-01-01_test-case_next-sync"
    run_dir = tmp_path / "runs" / run_name
    run_dir.mkdir(parents=True, exist_ok=True)
    for fname in ["execution-assignment.md", "goal.md", "plan.md", "build.md", "review.md"]:
        _fill_file(run_dir, fname)

    (run_dir / "run_state.json").write_text(
        json.dumps(
            {
                "run_id": run_name,
                "current_phase": "REVIEW_NEEDED",
                "phase_status": "failed",
                "current_owner": "Critic",
                "retry_count": 6,
                "last_error": "stale review error",
                "active_handoff_id": "handoff-444",
                "gate_failures": ["old blocker"],
            }
        ),
        encoding="utf-8",
    )

    result = _invoke_next(tmp_path, run_name, ["--phase-only"])

    assert result.exit_code == 0, result.output
    assert result.output.strip() == "IMPROVE_NEEDED"

    state = json.loads((run_dir / "run_state.json").read_text(encoding="utf-8"))
    assert state["current_phase"] == "IMPROVE_NEEDED"
    assert state["phase_status"] == "pending"
    assert state["current_owner"] == "Human"
    assert state["retry_count"] == 0
    assert state["last_error"] == ""
    assert state["active_handoff_id"] == ""
    assert state["gate_failures"] == []
