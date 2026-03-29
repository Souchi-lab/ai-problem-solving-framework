"""
test_optionalization_fresh_run.py — Fresh run invariant regression tests

Run 011 removed handoff.md and model-assignment.md from the default artifact set.
This file protects that behavior: a newly initialized run must NOT contain those files.

Invariant:
  A fresh run directory initialized from runs/_template/ does NOT contain
  handoff.md or model-assignment.md unless explicitly requested.

Coverage:
  - Template directory itself does not contain the removed files
  - RunRepository.init_run() does not produce them
  - CLI `apsf start-run` does not produce them
  - All mandatory artifacts are still created
  - No error is emitted solely due to the absence of optional artifacts
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path
from uuid import uuid4

import pytest
from typer.testing import CliRunner

from apsf.cli.main import app
from apsf.legacy.storage.run_repository import RunRepository, STANDARD_FILES
import apsf.legacy.config.settings as settings_module

runner = CliRunner()

_PROJECT_ROOT = Path(__file__).parent.parent
_REAL_TEMPLATE = _PROJECT_ROOT / "runs" / "_template"


# ---------------------------------------------------------------------------
# Fixture: reset settings singleton
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def reset_settings_singleton():
    settings_module._settings_instance = None
    yield
    settings_module._settings_instance = None


@pytest.fixture
def tmp_path() -> Path:
    base_dir = _PROJECT_ROOT / "tmp_manual_check_repo" / "pytest-local"
    base_dir.mkdir(parents=True, exist_ok=True)
    path = base_dir / f"fresh-run-{uuid4().hex}"
    path.mkdir(parents=True, exist_ok=False)
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)


# ---------------------------------------------------------------------------
# Class 1: Template directory does not include optional files
# ---------------------------------------------------------------------------

class TestFreshRunTemplateAbsence:
    """The runs/_template/ directory must not contain the now-optional files."""

    def test_template_does_not_contain_handoff(self) -> None:
        """handoff.md must not be in runs/_template/ (optional since run-011)."""
        assert not (_REAL_TEMPLATE / "handoff.md").exists(), (
            "handoff.md should not be in runs/_template/. "
            "It is an optional artifact created on demand from framework/templates/handoff.md."
        )

    def test_template_does_not_contain_model_assignment(self) -> None:
        """model-assignment.md must not be in runs/_template/ (optional since run-011)."""
        assert not (_REAL_TEMPLATE / "model-assignment.md").exists(), (
            "model-assignment.md should not be in runs/_template/. "
            "It is an optional artifact created on demand from framework/templates/model-assignment.md."
        )


# ---------------------------------------------------------------------------
# Class 2: init_run does not create optional files
# ---------------------------------------------------------------------------

class TestFreshRunInitRunAbsence:
    """RunRepository.init_run() must not create optional artifacts in fresh runs."""

    def test_init_run_does_not_create_handoff(self, tmp_path: Path) -> None:
        runs_dir = tmp_path / "runs"
        runs_dir.mkdir()
        repo = RunRepository(runs_dir=runs_dir, template_dir=_REAL_TEMPLATE)
        run_dir = repo.init_run("2099-01-01_test-case_no-handoff")
        assert not (run_dir / "handoff.md").exists(), (
            "handoff.md must not be created by init_run. "
            "It should only exist when explicitly created by the operator."
        )

    def test_init_run_does_not_create_model_assignment(self, tmp_path: Path) -> None:
        runs_dir = tmp_path / "runs"
        runs_dir.mkdir()
        repo = RunRepository(runs_dir=runs_dir, template_dir=_REAL_TEMPLATE)
        run_dir = repo.init_run("2099-01-01_test-case_no-model-assignment")
        assert not (run_dir / "model-assignment.md").exists(), (
            "model-assignment.md must not be created by init_run. "
            "It should only exist when model choice is mandatory/recommended for the run."
        )

    def test_init_run_still_creates_mandatory_artifacts(self, tmp_path: Path) -> None:
        """Fresh run must still contain all mandatory artifacts after run-011."""
        runs_dir = tmp_path / "runs"
        runs_dir.mkdir()
        repo = RunRepository(runs_dir=runs_dir, template_dir=_REAL_TEMPLATE)
        run_dir = repo.init_run("2099-01-01_test-case_mandatory-check")
        for fname in ["goal.md", "plan.md", "build.md", "review.md", "improve.md", "result.md"]:
            assert (run_dir / fname).exists(), (
                f"{fname} must still be created by init_run after run-011."
            )

    def test_init_run_no_error_without_optional_files(self, tmp_path: Path) -> None:
        """init_run must complete without error when optional files are absent."""
        runs_dir = tmp_path / "runs"
        runs_dir.mkdir()
        repo = RunRepository(runs_dir=runs_dir, template_dir=_REAL_TEMPLATE)
        # Should not raise
        run_dir = repo.init_run("2099-01-01_test-case_no-error")
        assert run_dir.is_dir()


# ---------------------------------------------------------------------------
# Class 3: CLI start-run does not create optional files
# ---------------------------------------------------------------------------

class TestFreshRunCliAbsence:
    """CLI `apsf start-run` must not create optional artifacts in fresh runs."""

    def test_start_run_does_not_create_handoff(self, tmp_path: Path) -> None:
        env = {**os.environ, "APSF_ROOT": str(_PROJECT_ROOT)}
        run_name = "2099-02-01_test-case_cli-no-handoff"
        result = runner.invoke(app, ["start-run", run_name], env=env)
        assert result.exit_code == 0, result.output
        # Determine where the run was actually created
        run_dir = _PROJECT_ROOT / "runs" / run_name
        try:
            assert not (run_dir / "handoff.md").exists(), (
                "CLI start-run must not create handoff.md. "
                "It is optional and created on demand."
            )
        finally:
            if run_dir.exists():
                import shutil
                shutil.rmtree(run_dir)

    def test_start_run_does_not_create_model_assignment(self, tmp_path: Path) -> None:
        env = {**os.environ, "APSF_ROOT": str(_PROJECT_ROOT)}
        run_name = "2099-02-01_test-case_cli-no-model-assignment"
        result = runner.invoke(app, ["start-run", run_name], env=env)
        assert result.exit_code == 0, result.output
        run_dir = _PROJECT_ROOT / "runs" / run_name
        try:
            assert not (run_dir / "model-assignment.md").exists(), (
                "CLI start-run must not create model-assignment.md. "
                "It is optional and created when model choice matters."
            )
        finally:
            if run_dir.exists():
                import shutil
                shutil.rmtree(run_dir)

    def test_start_run_exits_zero_without_optional_files(self, tmp_path: Path) -> None:
        """CLI start-run must succeed without emitting an error about absent optional files."""
        env = {**os.environ, "APSF_ROOT": str(_PROJECT_ROOT)}
        run_name = "2099-02-01_test-case_cli-no-error"
        result = runner.invoke(app, ["start-run", run_name], env=env)
        run_dir = _PROJECT_ROOT / "runs" / run_name
        try:
            assert result.exit_code == 0, result.output
            # No error about missing optional artifacts
            assert "handoff" not in result.output.lower() or "optional" in result.output.lower()
        finally:
            if run_dir.exists():
                import shutil
                shutil.rmtree(run_dir)
