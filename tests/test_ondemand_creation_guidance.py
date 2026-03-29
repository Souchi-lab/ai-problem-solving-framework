"""
test_ondemand_creation_guidance.py — On-demand creation guidance regression tests

There is no dedicated CLI command for creating handoff.md or model-assignment.md.
Instead, `apsf next` / phase instructions guide the operator to create these
files from the canonical templates in framework/templates/.

This file protects the guidance-path invariant: instructions emitted for
PLAN, BUILD, REVIEW, and IMPROVE_NEEDED phases must reference
framework/templates/handoff.md. The SETUP instruction must reference
framework/templates/model-assignment.md.

Invariants covered:
  1. Canonical templates for optional artifacts exist at framework/templates/.
  2. PLAN / BUILD / REVIEW / IMPROVE_NEEDED instructions reference
     framework/templates/handoff.md for on-demand creation.
  3. SETUP_NEEDED instruction references framework/templates/model-assignment.md
     and marks it as conditional (not always required).
  4. PhaseDetector includes handoff.md in files_to_read only when it exists
     (conditional read → conditional guidance).
"""

from __future__ import annotations

import shutil
from pathlib import Path
from uuid import uuid4

import pytest

from apsf.legacy.orchestration.phase_detector import Phase, PhaseDetector, PhaseInfo
from apsf.legacy.orchestration.next_instruction_builder import NextInstructionBuilder

_PROJECT_ROOT = Path(__file__).parent.parent
_FRAMEWORK_TEMPLATES = _PROJECT_ROOT / "framework" / "templates"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

@pytest.fixture
def tmp_path() -> Path:
    base_dir = _PROJECT_ROOT / "tmp_manual_check_repo" / "pytest-local"
    base_dir.mkdir(parents=True, exist_ok=True)
    path = base_dir / f"guidance-{uuid4().hex}"
    path.mkdir(parents=True, exist_ok=False)
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)

def _fill(run_dir: Path, filename: str, lines: int = 5) -> None:
    """Write enough meaningful lines to satisfy _is_filled() (> 3 lines)."""
    path = run_dir / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    content = "\n".join([f"Content line {i}" for i in range(lines)])
    path.write_text(content, encoding="utf-8")


def _make_phase_info(
    phase: Phase, files_to_read: list[str] | None = None
) -> PhaseInfo:
    """Create a minimal PhaseInfo for NextInstructionBuilder unit tests."""
    return PhaseInfo(
        phase=phase,
        evidence=[],
        next_role="Test",
        files_to_read=files_to_read or [],
        file_to_write="test.md",
        instruction_template="",
    )


def _build_detailed_instruction(
    phase: Phase, files_to_read: list[str] | None = None
) -> str:
    """Build the detailed_instruction string for a given phase."""
    info = _make_phase_info(phase, files_to_read)
    return NextInstructionBuilder().build(info, run_name="test-run").detailed_instruction


# ---------------------------------------------------------------------------
# Class 1: Canonical templates exist
# ---------------------------------------------------------------------------

class TestCanonicalTemplatesExist:
    """The source-of-truth templates for optional artifacts must be present on disk."""

    def test_handoff_template_exists(self) -> None:
        """framework/templates/handoff.md must exist for on-demand creation."""
        assert (_FRAMEWORK_TEMPLATES / "handoff.md").exists(), (
            "framework/templates/handoff.md must exist. "
            "Operators create handoff.md on demand by copying this template."
        )

    def test_model_assignment_template_exists(self) -> None:
        """framework/templates/model-assignment.md must exist for on-demand creation."""
        assert (_FRAMEWORK_TEMPLATES / "model-assignment.md").exists(), (
            "framework/templates/model-assignment.md must exist. "
            "Operators create model-assignment.md by copying this template when needed."
        )

    def test_handoff_template_has_from_to_structure(self) -> None:
        """handoff.md template must contain both From and To role sections."""
        content = (_FRAMEWORK_TEMPLATES / "handoff.md").read_text(encoding="utf-8")
        assert "## From" in content, (
            "handoff.md template must contain '## From' section."
        )
        assert "## To" in content, (
            "handoff.md template must contain '## To' section."
        )

    def test_model_assignment_template_has_role_table(self) -> None:
        """model-assignment.md template must contain a role assignment table."""
        content = (_FRAMEWORK_TEMPLATES / "model-assignment.md").read_text(encoding="utf-8")
        assert "Role" in content, (
            "model-assignment.md template must contain a Role column or Role section."
        )


# ---------------------------------------------------------------------------
# Class 2: Phase instructions reference framework/templates/handoff.md
# ---------------------------------------------------------------------------

class TestHandoffGuidanceInPhaseInstructions:
    """
    Detailed instructions emitted by NextInstructionBuilder must guide the
    operator to create handoff.md from framework/templates/handoff.md.
    """

    def test_plan_instruction_mentions_handoff_template(self) -> None:
        """PLAN_NEEDED detailed instruction must reference framework/templates/handoff.md."""
        instruction = _build_detailed_instruction(Phase.PLAN_NEEDED)
        assert "framework/templates/handoff.md" in instruction, (
            "PLAN_NEEDED instruction must tell the operator where to create handoff.md "
            "when transfer context is needed."
        )

    def test_build_instruction_mentions_handoff_template(self) -> None:
        """BUILD_NEEDED detailed instruction must reference framework/templates/handoff.md."""
        instruction = _build_detailed_instruction(Phase.BUILD_NEEDED)
        assert "framework/templates/handoff.md" in instruction, (
            "BUILD_NEEDED instruction must tell the operator where to create handoff.md "
            "when transfer context is needed."
        )

    def test_review_instruction_mentions_handoff_template(self) -> None:
        """REVIEW_NEEDED detailed instruction must reference framework/templates/handoff.md."""
        instruction = _build_detailed_instruction(Phase.REVIEW_NEEDED)
        assert "framework/templates/handoff.md" in instruction, (
            "REVIEW_NEEDED instruction must tell the operator where to create handoff.md "
            "when transfer context is needed."
        )

    def test_judge_instruction_mentions_handoff_template(self) -> None:
        """IMPROVE_NEEDED (Judge) detailed instruction must reference framework/templates/handoff.md."""
        instruction = _build_detailed_instruction(Phase.IMPROVE_NEEDED)
        assert "framework/templates/handoff.md" in instruction, (
            "IMPROVE_NEEDED (Judge) instruction must tell the operator where to create handoff.md "
            "when transfer context is needed."
        )


# ---------------------------------------------------------------------------
# Class 3: SETUP instruction references model-assignment template
# ---------------------------------------------------------------------------

class TestModelAssignmentGuidanceInSetupInstruction:
    """SETUP_NEEDED instruction must guide operators to model-assignment.md template."""

    def test_setup_instruction_mentions_model_assignment_template(self) -> None:
        """SETUP_NEEDED detailed instruction must reference framework/templates/model-assignment.md."""
        instruction = _build_detailed_instruction(Phase.SETUP_NEEDED)
        assert "framework/templates/model-assignment.md" in instruction, (
            "SETUP_NEEDED instruction must tell the operator where to create model-assignment.md "
            "when model choice matters for the run."
        )

    def test_setup_instruction_marks_model_assignment_as_conditional(self) -> None:
        """SETUP_NEEDED instruction must indicate that model-assignment.md is not always required."""
        instruction = _build_detailed_instruction(Phase.SETUP_NEEDED)
        # The instruction should convey that model-assignment.md is conditional
        assert (
            "optional" in instruction.lower()
            or "mandatory" in instruction
            or "recommended" in instruction
            or "必要な run" in instruction
            or "optional なら省略" in instruction
        ), (
            "SETUP_NEEDED instruction must clarify that model-assignment.md is not required "
            "for every run — only when model choice materially affects the outcome."
        )


# ---------------------------------------------------------------------------
# Class 4: handoff.md conditional inclusion in files_to_read
# ---------------------------------------------------------------------------

class TestHandoffConditionalInclusion:
    """
    PhaseDetector must include handoff.md in files_to_read only when the file
    actually exists in the run directory. This is the core mechanism that makes
    guidance conditional on the file's presence.
    """

    def test_handoff_in_files_to_read_at_build_phase_when_present(
        self, tmp_path: Path
    ) -> None:
        """files_to_read must include handoff.md at BUILD_NEEDED when the file exists."""
        run_dir = tmp_path / "run"
        run_dir.mkdir()
        _fill(run_dir, "execution-assignment.md")
        _fill(run_dir, "goal.md")
        _fill(run_dir, "plan.md")
        (run_dir / "build.md").write_text("# Build\n", encoding="utf-8")
        (run_dir / "handoff.md").write_text("# Handoff\n", encoding="utf-8")
        info = PhaseDetector(run_dir).detect()
        assert info.phase == Phase.BUILD_NEEDED
        assert "handoff.md" in info.files_to_read, (
            "handoff.md must appear in files_to_read at BUILD_NEEDED when the file exists."
        )

    def test_handoff_absent_from_files_to_read_at_build_phase_when_missing(
        self, tmp_path: Path
    ) -> None:
        """files_to_read must NOT include handoff.md at BUILD_NEEDED when the file is absent."""
        run_dir = tmp_path / "run"
        run_dir.mkdir()
        _fill(run_dir, "execution-assignment.md")
        _fill(run_dir, "goal.md")
        _fill(run_dir, "plan.md")
        (run_dir / "build.md").write_text("# Build\n", encoding="utf-8")
        # No handoff.md
        info = PhaseDetector(run_dir).detect()
        assert info.phase == Phase.BUILD_NEEDED
        assert "handoff.md" not in info.files_to_read, (
            "handoff.md must not appear in files_to_read at BUILD_NEEDED when the file is absent."
        )

    def test_handoff_in_files_to_read_at_review_phase_when_present(
        self, tmp_path: Path
    ) -> None:
        """files_to_read must include handoff.md at REVIEW_NEEDED when the file exists."""
        run_dir = tmp_path / "run"
        run_dir.mkdir()
        _fill(run_dir, "execution-assignment.md")
        _fill(run_dir, "goal.md")
        _fill(run_dir, "plan.md")
        _fill(run_dir, "build.md")
        (run_dir / "review.md").write_text("# Review\n", encoding="utf-8")
        (run_dir / "handoff.md").write_text("# Handoff\n", encoding="utf-8")
        info = PhaseDetector(run_dir).detect()
        assert info.phase == Phase.REVIEW_NEEDED
        assert "handoff.md" in info.files_to_read, (
            "handoff.md must appear in files_to_read at REVIEW_NEEDED when the file exists."
        )

    def test_handoff_in_files_to_read_at_improve_phase_when_present(
        self, tmp_path: Path
    ) -> None:
        """files_to_read must include handoff.md at IMPROVE_NEEDED when the file exists."""
        run_dir = tmp_path / "run"
        run_dir.mkdir()
        _fill(run_dir, "execution-assignment.md")
        _fill(run_dir, "goal.md")
        _fill(run_dir, "plan.md")
        _fill(run_dir, "build.md")
        _fill(run_dir, "review.md")
        (run_dir / "improve.md").write_text("# Improve\n", encoding="utf-8")
        (run_dir / "handoff.md").write_text("# Handoff\n", encoding="utf-8")
        info = PhaseDetector(run_dir).detect()
        assert info.phase == Phase.IMPROVE_NEEDED
        assert "handoff.md" in info.files_to_read, (
            "handoff.md must appear in files_to_read at IMPROVE_NEEDED when the file exists."
        )
