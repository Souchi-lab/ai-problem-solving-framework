"""
test_existing_run_optional_files.py — Existing run invariant regression tests

Run 011 made handoff.md and model-assignment.md optional. A run directory that
already contains those files must continue to be treated as valid: no tooling
should reject or strip them.

Invariants covered:
  1. RunRepository operations do not strip optional artifacts.
  2. RunRepository.get_run_status() keys only include STANDARD_FILES (no optional keys).
  3. PhaseDetector.detect() returns the correct phase for runs that include optional files.
  4. handoff.md is included in files_to_read when it exists; absent when it does not.
  5. CLI `apsf next` exits 0 and detects the correct phase when optional files are present.
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path
from uuid import uuid4

import pytest
from typer.testing import CliRunner

from apsf.cli.main import app
from apsf.orchestration.phase_detector import Phase, PhaseDetector
from apsf.legacy.storage.run_repository import RunRepository, STANDARD_FILES
import apsf.config.settings as settings_module

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
    path = base_dir / f"existing-run-{uuid4().hex}"
    path.mkdir(parents=True, exist_ok=False)
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fill(run_dir: Path, filename: str, lines: int = 5) -> None:
    """Write enough meaningful lines to satisfy _is_filled() (> 3 lines)."""
    path = run_dir / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    content = "\n".join([f"Content line {i}" for i in range(lines)])
    path.write_text(content, encoding="utf-8")


def _make_completed_run_with_optional_files(run_dir: Path) -> None:
    """Populate run_dir with all mandatory artifacts (filled) + optional files."""
    run_dir.mkdir(parents=True, exist_ok=True)
    for fname in [
        "execution-assignment.md",
        "goal.md",
        "plan.md",
        "build.md",
        "review.md",
        "improve.md",
        "result.md",
    ]:
        _fill(run_dir, fname)
    (run_dir / "handoff.md").write_text("# Handoff\n", encoding="utf-8")
    (run_dir / "model-assignment.md").write_text("# Model Assignment\n", encoding="utf-8")


def _make_run_at_build_phase(run_dir: Path) -> None:
    """Populate run_dir up to BUILD_NEEDED state (plan filled, build unfilled)."""
    run_dir.mkdir(parents=True, exist_ok=True)
    for fname in ["execution-assignment.md", "goal.md", "plan.md"]:
        _fill(run_dir, fname)
    (run_dir / "build.md").write_text("# Build\n", encoding="utf-8")


# ---------------------------------------------------------------------------
# Class 1: RunRepository does not strip optional files
# ---------------------------------------------------------------------------

class TestRunRepositoryDoesNotStripOptionalFiles:
    """RunRepository operations must leave optional artifacts untouched."""

    def test_run_exists_with_optional_files(self, tmp_path: Path) -> None:
        """A run directory that contains optional files is recognized as existing."""
        run_name = "2099-01-01_test-case_optional-present"
        run_dir = tmp_path / "runs" / run_name
        _make_completed_run_with_optional_files(run_dir)
        repo = RunRepository(runs_dir=tmp_path / "runs", template_dir=_REAL_TEMPLATE)
        assert repo.run_exists(run_name)

    def test_get_run_status_does_not_strip_handoff(self, tmp_path: Path) -> None:
        """get_run_status() must not remove handoff.md from the run directory."""
        run_name = "2099-01-01_test-case_status-handoff"
        run_dir = tmp_path / "runs" / run_name
        _make_completed_run_with_optional_files(run_dir)
        repo = RunRepository(runs_dir=tmp_path / "runs", template_dir=_REAL_TEMPLATE)
        repo.get_run_status(run_name)
        assert (run_dir / "handoff.md").exists(), (
            "get_run_status() must not strip handoff.md from the run directory."
        )

    def test_get_run_status_does_not_strip_model_assignment(self, tmp_path: Path) -> None:
        """get_run_status() must not remove model-assignment.md from the run directory."""
        run_name = "2099-01-01_test-case_status-model"
        run_dir = tmp_path / "runs" / run_name
        _make_completed_run_with_optional_files(run_dir)
        repo = RunRepository(runs_dir=tmp_path / "runs", template_dir=_REAL_TEMPLATE)
        repo.get_run_status(run_name)
        assert (run_dir / "model-assignment.md").exists(), (
            "get_run_status() must not strip model-assignment.md from the run directory."
        )

    def test_is_completed_does_not_strip_optional_files(self, tmp_path: Path) -> None:
        """is_completed() must not remove optional artifacts as a side effect."""
        run_name = "2099-01-01_test-case_completed-optional"
        run_dir = tmp_path / "runs" / run_name
        _make_completed_run_with_optional_files(run_dir)
        repo = RunRepository(runs_dir=tmp_path / "runs", template_dir=_REAL_TEMPLATE)
        repo.is_completed(run_name)
        assert (run_dir / "handoff.md").exists(), (
            "is_completed() must not strip handoff.md."
        )
        assert (run_dir / "model-assignment.md").exists(), (
            "is_completed() must not strip model-assignment.md."
        )

    def test_standard_file_status_correct_when_optional_files_co_exist(
        self, tmp_path: Path
    ) -> None:
        """get_run_status() returns True for all mandatory files when optional files co-exist."""
        run_name = "2099-01-01_test-case_status-correct"
        run_dir = tmp_path / "runs" / run_name
        _make_completed_run_with_optional_files(run_dir)
        repo = RunRepository(runs_dir=tmp_path / "runs", template_dir=_REAL_TEMPLATE)
        status = repo.get_run_status(run_name)
        for fname in ["goal.md", "plan.md", "build.md", "review.md", "improve.md", "result.md"]:
            assert status.get(fname) is True, (
                f"{fname} should appear as present in get_run_status()."
            )

    def test_optional_files_not_in_standard_status_keys(self, tmp_path: Path) -> None:
        """get_run_status() must not include optional artifact keys in its return value."""
        run_name = "2099-01-01_test-case_no-optional-keys"
        run_dir = tmp_path / "runs" / run_name
        _make_completed_run_with_optional_files(run_dir)
        repo = RunRepository(runs_dir=tmp_path / "runs", template_dir=_REAL_TEMPLATE)
        status = repo.get_run_status(run_name)
        assert "handoff.md" not in status, (
            "handoff.md is optional and must not appear as a key in get_run_status()."
        )
        assert "model-assignment.md" not in status, (
            "model-assignment.md is optional and must not appear as a key in get_run_status()."
        )


# ---------------------------------------------------------------------------
# Class 2: PhaseDetector handles optional files correctly
# ---------------------------------------------------------------------------

class TestPhaseDetectorWithOptionalFiles:
    """PhaseDetector must not reject or misdetect phases when optional artifacts are present."""

    def test_phase_detection_not_broken_by_optional_files(self, tmp_path: Path) -> None:
        """A completed run with optional files still detects as COMPLETE."""
        run_dir = tmp_path / "run"
        _make_completed_run_with_optional_files(run_dir)
        # Add transcript.md to satisfy the COMPLETE condition
        (run_dir / "transcript.md").write_text(
            "# Transcript\n\nGenerated: 2099-01-01T00:00:00\n\nLine 1\nLine 2\nLine 3\nLine 4\n",
            encoding="utf-8",
        )
        info = PhaseDetector(run_dir).detect()
        assert info.phase == Phase.COMPLETE, (
            f"A completed run with optional files should detect as COMPLETE, got {info.phase}."
        )

    def test_handoff_in_files_to_read_when_present_at_build_phase(
        self, tmp_path: Path
    ) -> None:
        """When handoff.md exists during BUILD_NEEDED, it must appear in files_to_read."""
        run_dir = tmp_path / "run"
        _make_run_at_build_phase(run_dir)
        (run_dir / "handoff.md").write_text("# Handoff\n", encoding="utf-8")
        info = PhaseDetector(run_dir).detect()
        assert info.phase == Phase.BUILD_NEEDED, (
            f"Expected BUILD_NEEDED, got {info.phase}."
        )
        assert "handoff.md" in info.files_to_read, (
            "handoff.md must be included in files_to_read when it exists during BUILD_NEEDED."
        )

    def test_handoff_not_in_files_to_read_when_absent_at_build_phase(
        self, tmp_path: Path
    ) -> None:
        """When handoff.md is absent during BUILD_NEEDED, it must not appear in files_to_read."""
        run_dir = tmp_path / "run"
        _make_run_at_build_phase(run_dir)
        # No handoff.md
        info = PhaseDetector(run_dir).detect()
        assert info.phase == Phase.BUILD_NEEDED, (
            f"Expected BUILD_NEEDED, got {info.phase}."
        )
        assert "handoff.md" not in info.files_to_read, (
            "handoff.md must not appear in files_to_read when it is absent during BUILD_NEEDED."
        )

    def test_handoff_in_files_to_read_when_present_at_review_phase(
        self, tmp_path: Path
    ) -> None:
        """When handoff.md exists during REVIEW_NEEDED, it must appear in files_to_read."""
        run_dir = tmp_path / "run"
        run_dir.mkdir()
        for fname in ["execution-assignment.md", "goal.md", "plan.md", "build.md"]:
            _fill(run_dir, fname)
        (run_dir / "review.md").write_text("# Review\n", encoding="utf-8")
        (run_dir / "handoff.md").write_text("# Handoff\n", encoding="utf-8")
        info = PhaseDetector(run_dir).detect()
        assert info.phase == Phase.REVIEW_NEEDED, (
            f"Expected REVIEW_NEEDED, got {info.phase}."
        )
        assert "handoff.md" in info.files_to_read, (
            "handoff.md must be in files_to_read during REVIEW_NEEDED when it exists."
        )

    def test_model_assignment_does_not_affect_phase_progression(
        self, tmp_path: Path
    ) -> None:
        """model-assignment.md presence must not alter normal phase detection."""
        run_dir = tmp_path / "run"
        run_dir.mkdir()
        _fill(run_dir, "execution-assignment.md")
        _fill(run_dir, "goal.md")
        (run_dir / "model-assignment.md").write_text(
            "# Model Assignment\n", encoding="utf-8"
        )
        (run_dir / "plan.md").write_text("# Plan\n", encoding="utf-8")
        info = PhaseDetector(run_dir).detect()
        assert info.phase == Phase.PLAN_NEEDED, (
            f"model-assignment.md presence should not change phase detection, got {info.phase}."
        )


# ---------------------------------------------------------------------------
# Class 3: CLI apsf next handles optional files without error
# ---------------------------------------------------------------------------

class TestCliNextWithOptionalFiles:
    """apsf next must not fail when optional artifacts exist in the run directory."""

    def _make_plan_phase_run(self, tmp_path: Path) -> str:
        """Create a PLAN_NEEDED run in tmp_path/runs/ with optional files present."""
        run_name = "2099-03-01_test-case_optional-in-cli"
        run_dir = tmp_path / "runs" / run_name
        run_dir.mkdir(parents=True)
        _fill(run_dir, "execution-assignment.md")
        _fill(run_dir, "goal.md")
        (run_dir / "plan.md").write_text("# Plan\n", encoding="utf-8")
        (run_dir / "handoff.md").write_text("# Handoff\n", encoding="utf-8")
        (run_dir / "model-assignment.md").write_text("# Model Assignment\n", encoding="utf-8")
        return run_name

    def test_apsf_next_exits_zero_with_optional_files_present(
        self, tmp_path: Path
    ) -> None:
        """apsf next must exit 0 when optional files exist in the run directory."""
        run_name = self._make_plan_phase_run(tmp_path)
        env = {**os.environ, "APSF_ROOT": str(tmp_path)}
        result = runner.invoke(app, ["next", run_name], env=env)
        assert result.exit_code == 0, (
            f"apsf next must not fail when optional files exist.\nOutput: {result.output}"
        )

    def test_apsf_next_detects_correct_phase_with_optional_files(
        self, tmp_path: Path
    ) -> None:
        """apsf next must detect the correct phase even when optional files are present."""
        run_name = self._make_plan_phase_run(tmp_path)
        env = {**os.environ, "APSF_ROOT": str(tmp_path)}
        result = runner.invoke(app, ["next", run_name], env=env)
        assert result.exit_code == 0, result.output
        assert "PLAN_NEEDED" in result.output or "plan" in result.output.lower(), (
            "apsf next should indicate PLAN_NEEDED when plan.md is unfilled, "
            "regardless of optional file presence."
        )
