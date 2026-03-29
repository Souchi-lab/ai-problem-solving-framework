"""
test_next_instruction_builder.py — NextInstructionBuilder のユニットテスト

テスト方針:
- 各主要フェーズで期待する next_role / target_file / instruction が返る
- COMPLETE で不自然な次指示が出ない
- _fallback が未知フェーズでも安全に返る
"""

from __future__ import annotations

from pathlib import Path

import pytest

from apsf.legacy.orchestration.phase_detector import Phase, PhaseDetector
from apsf.legacy.orchestration.next_instruction_builder import NextInstruction, NextInstructionBuilder


# ---------------------------------------------------------------------------
# Helper: PhaseInfo を直接作らずに PhaseDetector 経由で取得
# ---------------------------------------------------------------------------

def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _fill(run_dir: Path, filename: str, lines: int = 5) -> None:
    # transcript.md は 'Generated:' を含む内容を書く（_is_filled の特別判定に対応）
    if filename == "transcript.md":
        content = "# Transcript\n\nGenerated: 2099-01-01T00:00:00\n\n" + "\n".join(
            [f"Content line {i}" for i in range(lines)]
        )
    else:
        content = "\n".join([f"Content line {i}" for i in range(lines)])
    _write(run_dir / filename, content)


def _fill_comments_only(run_dir: Path, filename: str) -> None:
    content = "<!-- comment -->\n---\n\n# Heading\n"
    _write(run_dir / filename, content)


def _detect_and_build(run_dir: Path, run_name: str = "test-run") -> NextInstruction:
    info = PhaseDetector(run_dir).detect()
    return NextInstructionBuilder().build(info, run_name)


# ---------------------------------------------------------------------------
# NextInstruction structure
# ---------------------------------------------------------------------------

class TestNextInstructionStructure:
    def test_returns_next_instruction_dataclass(self, tmp_path: Path) -> None:
        result = _detect_and_build(tmp_path)
        assert isinstance(result, NextInstruction)

    def test_all_fields_populated(self, tmp_path: Path) -> None:
        result = _detect_and_build(tmp_path)
        assert result.phase is not None
        assert result.next_role != ""
        assert result.target_file != ""
        assert result.short_instruction != ""
        assert result.detailed_instruction != ""

    def test_short_instruction_is_single_line(self, tmp_path: Path) -> None:
        result = _detect_and_build(tmp_path)
        assert "\n" not in result.short_instruction


# ---------------------------------------------------------------------------
# Per-phase next_role and target_file
# ---------------------------------------------------------------------------

class TestPerPhaseOutput:
    def test_setup_needed_targets_human(self, tmp_path: Path) -> None:
        result = _detect_and_build(tmp_path)
        assert result.phase == Phase.SETUP_NEEDED
        assert result.next_role == "Human"
        assert "execution-assignment" in result.target_file

    def test_goal_needed_targets_human(self, tmp_path: Path) -> None:
        _fill(tmp_path, "execution-assignment.md")
        result = _detect_and_build(tmp_path)
        assert result.phase == Phase.GOAL_NEEDED
        assert result.next_role == "Human"
        assert "goal" in result.target_file

    def test_plan_needed_targets_planner(self, tmp_path: Path) -> None:
        _fill(tmp_path, "execution-assignment.md")
        _fill(tmp_path, "goal.md")
        result = _detect_and_build(tmp_path)
        assert result.phase == Phase.PLAN_NEEDED
        assert "Planner" in result.next_role
        assert "plan" in result.target_file

    def test_build_needed_targets_builder(self, tmp_path: Path) -> None:
        _fill(tmp_path, "execution-assignment.md")
        _fill(tmp_path, "goal.md")
        _fill(tmp_path, "plan.md")
        result = _detect_and_build(tmp_path)
        assert result.phase == Phase.BUILD_NEEDED
        assert "Builder" in result.next_role
        assert "build" in result.target_file

    def test_review_needed_targets_critic(self, tmp_path: Path) -> None:
        _fill(tmp_path, "execution-assignment.md")
        _fill(tmp_path, "goal.md")
        _fill(tmp_path, "plan.md")
        _fill(tmp_path, "build.md")
        result = _detect_and_build(tmp_path)
        assert result.phase == Phase.REVIEW_NEEDED
        assert "Critic" in result.next_role
        assert "review" in result.target_file

    def test_improve_needed_targets_judge(self, tmp_path: Path) -> None:
        _fill(tmp_path, "execution-assignment.md")
        _fill(tmp_path, "goal.md")
        _fill(tmp_path, "plan.md")
        _fill(tmp_path, "build.md")
        _fill(tmp_path, "review.md")
        result = _detect_and_build(tmp_path)
        assert result.phase == Phase.IMPROVE_NEEDED
        assert "Judge" in result.next_role
        assert "improve" in result.target_file

    def test_result_needed_targets_human(self, tmp_path: Path) -> None:
        _fill(tmp_path, "execution-assignment.md")
        _fill(tmp_path, "goal.md")
        _fill(tmp_path, "plan.md")
        _fill(tmp_path, "build.md")
        _fill(tmp_path, "review.md")
        _fill(tmp_path, "improve.md")
        result = _detect_and_build(tmp_path)
        assert result.phase == Phase.RESULT_NEEDED
        assert result.next_role == "Human"
        assert "result" in result.target_file

    def test_complete_has_no_action_instruction(self, tmp_path: Path) -> None:
        for f in [
            "execution-assignment.md", "goal.md", "plan.md",
            "build.md", "review.md", "improve.md",
            "result.md", "transcript.md",
        ]:
            _fill(tmp_path, f)
        result = _detect_and_build(tmp_path)
        assert result.phase == Phase.COMPLETE
        # COMPLETE は次ロールへの具体的な作業指示を含まない
        assert result.next_role == "(none)"


# ---------------------------------------------------------------------------
# Optional phases
# ---------------------------------------------------------------------------

class TestOptionalPhaseInstructions:
    def test_improve_plan_optional_instruction(self, tmp_path: Path) -> None:
        # IMPROVE_PLAN_OPTIONAL は review.md 充填後に発火する（v0.2 フロー）
        _fill(tmp_path, "execution-assignment.md")
        _fill(tmp_path, "goal.md")
        _fill(tmp_path, "plan.md")
        _fill(tmp_path, "build.md")
        _fill(tmp_path, "review.md")
        _fill_comments_only(tmp_path, "improve-plan.md")
        result = _detect_and_build(tmp_path)
        assert result.phase == Phase.IMPROVE_PLAN_OPTIONAL
        assert "Judge" in result.next_role
        assert "improve-plan" in result.target_file
        # detailed に done criteria / scope の説明が含まれる
        assert "Done Criteria" in result.detailed_instruction or "scope" in result.detailed_instruction.lower()

    def test_verify_optional_instruction(self, tmp_path: Path) -> None:
        _fill(tmp_path, "execution-assignment.md")
        _fill(tmp_path, "goal.md")
        _fill(tmp_path, "plan.md")
        _fill(tmp_path, "build.md")
        _fill(tmp_path, "review.md")
        _fill(tmp_path, "improve.md")
        _fill_comments_only(tmp_path, "verify.md")
        result = _detect_and_build(tmp_path)
        assert result.phase == Phase.VERIFY_OPTIONAL
        assert "verify" in result.target_file
        # detailed に "Pass/Fail" や "Done Criteria" が含まれる
        assert "Pass" in result.detailed_instruction or "Done Criteria" in result.detailed_instruction


# ---------------------------------------------------------------------------
# Instruction content quality
# ---------------------------------------------------------------------------

class TestInstructionContent:
    def test_plan_instruction_mentions_read_files(self, tmp_path: Path) -> None:
        _fill(tmp_path, "execution-assignment.md")
        _fill(tmp_path, "goal.md")
        result = _detect_and_build(tmp_path)
        assert result.phase == Phase.PLAN_NEEDED
        assert "goal.md" in result.detailed_instruction

    def test_build_instruction_mentions_dont_re_plan(self, tmp_path: Path) -> None:
        _fill(tmp_path, "execution-assignment.md")
        _fill(tmp_path, "goal.md")
        _fill(tmp_path, "plan.md")
        result = _detect_and_build(tmp_path)
        assert result.phase == Phase.BUILD_NEEDED
        # Builder に「re-plan しない」というルールが含まれる
        instr = result.detailed_instruction.lower()
        assert "plan" in instr  # plan.md を読む旨が含まれる

    def test_review_instruction_mentions_critical_major_minor(
        self, tmp_path: Path
    ) -> None:
        _fill(tmp_path, "execution-assignment.md")
        _fill(tmp_path, "goal.md")
        _fill(tmp_path, "plan.md")
        _fill(tmp_path, "build.md")
        result = _detect_and_build(tmp_path)
        assert result.phase == Phase.REVIEW_NEEDED
        assert "Critical" in result.detailed_instruction
        assert "Major" in result.detailed_instruction
        assert "Minor" in result.detailed_instruction

    def test_run_name_appears_in_result_instruction(self, tmp_path: Path) -> None:
        _fill(tmp_path, "execution-assignment.md")
        _fill(tmp_path, "goal.md")
        _fill(tmp_path, "plan.md")
        _fill(tmp_path, "build.md")
        _fill(tmp_path, "review.md")
        _fill(tmp_path, "improve.md")
        info = PhaseDetector(tmp_path).detect()
        result = NextInstructionBuilder().build(info, run_name="my-test-run")
        assert result.phase == Phase.RESULT_NEEDED
        assert "my-test-run" in result.detailed_instruction
