from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from apsf.legacy.cli.main import app

runner = CliRunner()


@pytest.fixture(autouse=True)
def reset_settings_singleton():
    import apsf.legacy.config.settings as m

    original = m._settings_instance
    m._settings_instance = None
    yield
    m._settings_instance = original


def test_init_child_run_command_creates_child_run(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("APSF_ROOT", str(tmp_path))
    template_dir = tmp_path / "runs" / "_template"
    template_dir.mkdir(parents=True)
    for name in ("goal.md", "plan.md", "build.md"):
        (template_dir / name).write_text(f"# {name}\n", encoding="utf-8")

    parent_dir = tmp_path / "runs" / "work" / "2026-04-09_parent_case"
    parent_dir.mkdir(parents=True)

    result = runner.invoke(
        app,
        [
            "init-child-run",
            "--run-id",
            "001c1_parent_child-run",
            "--parent-run",
            "2026-04-09_parent_case",
            "--taxonomy",
            "work",
            "--title",
            "Child Run",
            "--goal",
            "Verify the child run initialization path.",
        ],
    )

    assert result.exit_code == 0
    child_dir = parent_dir / "001c1_parent_child-run"
    assert child_dir.exists()
    assert "Verify the child run initialization path." in (child_dir / "goal.md").read_text(encoding="utf-8")
    assert "\"current_phase\": \"GOAL_NEEDED\"" in (child_dir / "run_state.json").read_text(encoding="utf-8")
