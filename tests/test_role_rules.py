"""
test_role_rules.py — role_rules.py の単体テスト

テスト方針:
- ROLE_FORBIDDEN の各 role / file 組み合わせが正しく判定される
- force=True で HARD_STOP が WARNING にダウングレードされる
- 許可ファイルへの書き込みは None を返す
- role_from_phase が正しく role 名を返す
- 未知の role は常に None を返す（fail-open: 未知ロールはガードしない）
"""
from __future__ import annotations

import pytest

from apsf.legacy.cli.role_rules import (
    GuardSeverity,
    RoleBoundaryViolation,
    check_role_boundary,
    role_from_phase,
)


# ---------------------------------------------------------------------------
# Builder — forbidden artifacts
# ---------------------------------------------------------------------------

def test_builder_cannot_write_review_md():
    v = check_role_boundary("Builder", "review.md")
    assert v is not None
    assert v.severity == GuardSeverity.HARD_STOP
    assert v.role == "Builder"
    assert v.target_file == "review.md"


def test_builder_cannot_write_improve_md():
    v = check_role_boundary("Builder", "improve.md")
    assert v is not None
    assert v.severity == GuardSeverity.HARD_STOP


def test_builder_cannot_write_result_md():
    v = check_role_boundary("Builder", "result.md")
    assert v is not None
    assert v.severity == GuardSeverity.HARD_STOP


# ---------------------------------------------------------------------------
# Builder — allowed artifacts
# ---------------------------------------------------------------------------

def test_builder_can_write_build_md():
    assert check_role_boundary("Builder", "build.md") is None


def test_builder_can_write_handoff_md():
    assert check_role_boundary("Builder", "handoff.md") is None


def test_builder_cannot_write_plan_md():
    # ownership.py が canonical: plan.md の allowed_writers は ("Planner",) のみ
    # Builder は plan.md に書けない（allowed list ベースの新ポリシー）
    v = check_role_boundary("Builder", "plan.md")
    assert v is not None
    assert v.severity == GuardSeverity.HARD_STOP


# ---------------------------------------------------------------------------
# Planner — forbidden artifacts
# ---------------------------------------------------------------------------

def test_planner_cannot_write_build_md():
    v = check_role_boundary("Planner", "build.md")
    assert v is not None
    assert v.severity == GuardSeverity.HARD_STOP


def test_planner_cannot_write_review_md():
    v = check_role_boundary("Planner", "review.md")
    assert v is not None
    assert v.severity == GuardSeverity.HARD_STOP


def test_planner_cannot_write_improve_md():
    v = check_role_boundary("Planner", "improve.md")
    assert v is not None
    assert v.severity == GuardSeverity.HARD_STOP


def test_planner_cannot_write_result_md():
    v = check_role_boundary("Planner", "result.md")
    assert v is not None
    assert v.severity == GuardSeverity.HARD_STOP


def test_planner_can_write_plan_md():
    assert check_role_boundary("Planner", "plan.md") is None


def test_planner_can_write_goal_md():
    assert check_role_boundary("Planner", "goal.md") is None


# ---------------------------------------------------------------------------
# Critic — forbidden artifacts
# ---------------------------------------------------------------------------

def test_critic_cannot_write_improve_md():
    v = check_role_boundary("Critic", "improve.md")
    assert v is not None
    assert v.severity == GuardSeverity.HARD_STOP


def test_critic_cannot_write_result_md():
    v = check_role_boundary("Critic", "result.md")
    assert v is not None
    assert v.severity == GuardSeverity.HARD_STOP


def test_critic_can_write_review_md():
    assert check_role_boundary("Critic", "review.md") is None


# ---------------------------------------------------------------------------
# --force with reason downgrades HARD_STOP to WARNING
# ---------------------------------------------------------------------------

def test_force_with_reason_downgrades_hardstop_to_warning_builder_review():
    v = check_role_boundary("Builder", "review.md", force=True, override_reason="handoff approved")
    assert v is not None
    assert v.severity == GuardSeverity.WARNING


def test_force_with_reason_downgrades_hardstop_to_warning_planner_build():
    v = check_role_boundary("Planner", "build.md", force=True, override_reason="emergency fix")
    assert v is not None
    assert v.severity == GuardSeverity.WARNING


def test_force_without_reason_remains_hardstop():
    v = check_role_boundary("Builder", "review.md", force=True)
    assert v is not None
    assert v.severity == GuardSeverity.HARD_STOP


def test_force_on_allowed_file_returns_none():
    # force on an allowed file: still no violation
    assert check_role_boundary("Builder", "build.md", force=True) is None


# ---------------------------------------------------------------------------
# Violation message and hint
# ---------------------------------------------------------------------------

def test_violation_message_contains_role_and_file():
    v = check_role_boundary("Builder", "review.md")
    assert v is not None
    assert "Builder" in v.message
    assert "review.md" in v.message


def test_force_violation_override_hint_mentions_force():
    v = check_role_boundary("Builder", "review.md", force=True, override_reason="approved")
    assert v is not None
    assert "--force" in v.override_hint or "Override" in v.override_hint


def test_non_force_violation_hint_mentions_force():
    v = check_role_boundary("Builder", "review.md")
    assert v is not None
    assert "--force" in v.override_hint


# ---------------------------------------------------------------------------
# Unknown / human roles — fail-open
# ---------------------------------------------------------------------------

def test_unknown_role_blocked_for_known_artifact():
    # ownership.py が canonical: review.md の allowed_writers は ("Critic",) のみ
    # 未知の role も allowed_writers にない場合は HARD_STOP（allowed list ベース）
    v = check_role_boundary("UnknownRole", "review.md")
    assert v is not None
    assert v.severity == GuardSeverity.HARD_STOP


def test_human_role_returns_none():
    assert check_role_boundary("Human", "improve.md") is None


# ---------------------------------------------------------------------------
# role_from_phase
# ---------------------------------------------------------------------------

def test_role_from_phase_build_needed():
    assert role_from_phase("BUILD_NEEDED") == "Builder"


def test_role_from_phase_plan_needed():
    assert role_from_phase("PLAN_NEEDED") == "Planner"


def test_role_from_phase_review_needed():
    assert role_from_phase("REVIEW_NEEDED") == "Critic"


def test_role_from_phase_human_phases_return_none():
    for human_phase in [
        "GOAL_NEEDED", "IMPROVE_NEEDED", "RESULT_NEEDED",
        "SETUP_NEEDED", "COMPLETE", "TRANSCRIPT_RECOMMENDED",
    ]:
        assert role_from_phase(human_phase) is None, f"Expected None for {human_phase}"


def test_role_from_phase_unknown_returns_none():
    assert role_from_phase("NONEXISTENT_PHASE") is None
