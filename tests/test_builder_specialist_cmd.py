"""Tests for `apsf builder-specialist` CLI command.

run-089: build wrapper Builder specialist injection
Verifies that the command resolves B-TYPE from execution-assignment.md and
outputs parseable key=value metadata (and optionally the specialist content).
"""
from __future__ import annotations

import shutil
from pathlib import Path

import pytest
from typer.testing import CliRunner

from apsf.legacy.cli.main import app

runner = CliRunner()

_REAL_BUILDERS_DIR = Path(__file__).parent.parent / "framework" / "agents" / "builders"


@pytest.fixture(autouse=True)
def reset_settings_singleton():
    """Reset the Settings singleton between tests so APSF_ROOT env changes take effect."""
    import apsf.legacy.config.settings as m
    original = m._settings_instance
    m._settings_instance = None
    yield
    m._settings_instance = original


@pytest.fixture
def env(tmp_path: Path) -> Path:
    """Prepare a tmp APSF_ROOT with specialist files and runs/ directory."""
    # Copy real specialist files so content resolution works
    dest = tmp_path / "framework" / "agents" / "builders"
    dest.mkdir(parents=True)
    for f in _REAL_BUILDERS_DIR.glob("*.md"):
        shutil.copy2(f, dest / f.name)
    (tmp_path / "runs").mkdir()
    return tmp_path


def _write_run(tmp_path: Path, run_name: str) -> Path:
    run_dir = tmp_path / "runs" / run_name
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "run_state.json").write_text(
        '{"run_id":"' + run_name + '","current_phase":"BUILD_NEEDED",'
        '"phase_status":"pending","current_owner":"Builder",'
        '"retry_count":0,"last_error":"","active_handoff_id":"","gate_failures":[]}',
        encoding="utf-8",
    )
    return run_dir


def _invoke(monkeypatch, apsf_root: Path, run_name: str, extra_args: list[str] | None = None) -> str:
    monkeypatch.setenv("APSF_ROOT", str(apsf_root))
    args = ["builder-specialist", run_name] + (extra_args or [])
    result = runner.invoke(app, args)
    return result.output.strip()


# ── no files ──────────────────────────────────────────────────────────────────

def test_no_files_returns_unresolved_with_gap(monkeypatch, env: Path) -> None:
    """No goal.md and no execution-assignment.md → mode=unresolved, gap=true."""
    _write_run(env, "run-089")
    output = _invoke(monkeypatch, env, "run-089")
    assert "mode=unresolved" in output
    assert "gap=true" in output
    assert "code=" in output


# ── explicit B-TYPE ───────────────────────────────────────────────────────────

def test_explicit_btype_returns_correct_metadata(monkeypatch, env: Path) -> None:
    """Explicit B-04 in execution-assignment.md → code=B-04, mode=explicit, gap=false."""
    run_dir = _write_run(env, "run-089")
    (run_dir / "goal.md").write_text("Polish the UI layout and improve responsiveness.", encoding="utf-8")
    (run_dir / "execution-assignment.md").write_text(
        "## Builder Specialist\n- Primary B-TYPE: B-04\n",
        encoding="utf-8",
    )
    output = _invoke(monkeypatch, env, "run-089")
    assert "code=B-04" in output
    assert "mode=explicit" in output
    assert "gap=false" in output


def test_explicit_b01_returns_correct_metadata(monkeypatch, env: Path) -> None:
    run_dir = _write_run(env, "run-089")
    (run_dir / "execution-assignment.md").write_text(
        "## Builder Specialist\n- Primary B-TYPE: B-01\n",
        encoding="utf-8",
    )
    output = _invoke(monkeypatch, env, "run-089")
    assert "code=B-01" in output
    assert "mode=explicit" in output
    assert "gap=false" in output


def test_explicit_none_returns_empty_code_no_gap(monkeypatch, env: Path) -> None:
    """Explicit 'none' B-TYPE → empty code, explicit, no gap."""
    run_dir = _write_run(env, "run-089")
    (run_dir / "execution-assignment.md").write_text(
        "## Builder Specialist\n- Primary B-TYPE: none\n",
        encoding="utf-8",
    )
    output = _invoke(monkeypatch, env, "run-089")
    assert "mode=explicit" in output
    assert "gap=false" in output


def test_explicit_unknown_btype_has_gap(monkeypatch, env: Path) -> None:
    """Explicit B-99 (not in registry) → gap=true."""
    run_dir = _write_run(env, "run-089")
    (run_dir / "execution-assignment.md").write_text(
        "## Builder Specialist\n- Primary B-TYPE: B-99\n",
        encoding="utf-8",
    )
    output = _invoke(monkeypatch, env, "run-089")
    assert "gap=true" in output


# ── inferred ──────────────────────────────────────────────────────────────────

def test_inferred_from_goal_returns_inferred_mode(monkeypatch, env: Path) -> None:
    """No explicit B-TYPE but goal has strong keywords → mode=inferred, gap=false."""
    run_dir = _write_run(env, "run-089")
    (run_dir / "goal.md").write_text(
        "Fix a reproducible regression where state mismatch causes a broken flow.",
        encoding="utf-8",
    )
    output = _invoke(monkeypatch, env, "run-089")
    assert "mode=inferred" in output
    assert "gap=false" in output
    assert "code=" in output  # some code was inferred


# ── --print-content ───────────────────────────────────────────────────────────

def test_print_content_explicit_btype_returns_content(monkeypatch, env: Path) -> None:
    """--print-content with explicit B-04 → outputs specialist file content."""
    run_dir = _write_run(env, "run-089")
    (run_dir / "execution-assignment.md").write_text(
        "## Builder Specialist\n- Primary B-TYPE: B-04\n",
        encoding="utf-8",
    )
    output = _invoke(monkeypatch, env, "run-089", ["--print-content"])
    assert "B-04" in output
    assert "Frontend" in output


def test_print_content_no_match_returns_empty(monkeypatch, env: Path) -> None:
    """--print-content with no files → empty output (no content to inject)."""
    _write_run(env, "run-089")
    output = _invoke(monkeypatch, env, "run-089", ["--print-content"])
    assert output == ""


def test_print_content_explicit_none_returns_empty(monkeypatch, env: Path) -> None:
    """--print-content with B-TYPE: none → empty output."""
    run_dir = _write_run(env, "run-089")
    (run_dir / "execution-assignment.md").write_text(
        "## Builder Specialist\n- Primary B-TYPE: none\n",
        encoding="utf-8",
    )
    output = _invoke(monkeypatch, env, "run-089", ["--print-content"])
    assert output == ""
