"""
PermissionMatrix のテスト

カバー範囲:
  - infer_target_scope: own / foreign / system の 3 分岐
  - PermissionEvaluator.evaluate:
      auto → allowed
      requires_reason × no-force → denied
      requires_reason × force+reason → allowed
      blocked × no-force → denied
      blocked × force+reason → denied（force でも通らない）
  - unknown (operation, scope) は requires_reason にフォールバック
"""

from __future__ import annotations

import pytest

from apsf.core.permissions.permission_matrix import (
    MODE_AUTO,
    MODE_BLOCKED,
    MODE_REQUIRES_REASON,
    OP_WRITE,
    SCOPE_FOREIGN_PHASE,
    SCOPE_OWN_PHASE,
    SCOPE_SYSTEM,
    PermissionEvaluator,
    PermissionRequest,
    infer_target_scope,
)


# ── infer_target_scope ────────────────────────────────────────────────────────

def test_infer_scope_own_phase_planner_plan() -> None:
    assert infer_target_scope("Planner", "plan.md") == SCOPE_OWN_PHASE


def test_infer_scope_own_phase_builder_build() -> None:
    assert infer_target_scope("Builder", "build.md") == SCOPE_OWN_PHASE


def test_infer_scope_own_phase_critic_review() -> None:
    assert infer_target_scope("Critic", "review.md") == SCOPE_OWN_PHASE


def test_infer_scope_own_phase_human_goal() -> None:
    assert infer_target_scope("Human", "goal.md") == SCOPE_OWN_PHASE


def test_infer_scope_foreign_builder_writes_plan() -> None:
    assert infer_target_scope("Builder", "plan.md") == SCOPE_FOREIGN_PHASE


def test_infer_scope_foreign_planner_writes_build() -> None:
    assert infer_target_scope("Planner", "build.md") == SCOPE_FOREIGN_PHASE


def test_infer_scope_system_run_state() -> None:
    assert infer_target_scope("Builder", "run_state.json") == SCOPE_SYSTEM


def test_infer_scope_system_artifact_manifest() -> None:
    assert infer_target_scope("Planner", "artifact_manifest.json") == SCOPE_SYSTEM


def test_infer_scope_system_force_audit() -> None:
    assert infer_target_scope("Critic", "force_audit.json") == SCOPE_SYSTEM


def test_infer_scope_system_session_events() -> None:
    assert infer_target_scope("Builder", "session_events.jsonl") == SCOPE_SYSTEM


def test_infer_scope_system_handoff() -> None:
    assert infer_target_scope("Human", "handoff.json") == SCOPE_SYSTEM


# ── PermissionEvaluator: auto ─────────────────────────────────────────────────

def test_evaluate_own_phase_auto_allowed() -> None:
    req = PermissionRequest(
        operation_type=OP_WRITE,
        target_scope=SCOPE_OWN_PHASE,
        role="Builder",
    )
    decision = PermissionEvaluator().evaluate(req)
    assert decision.allowed is True
    assert decision.approval_mode == MODE_AUTO


def test_evaluate_own_phase_auto_allowed_even_without_force() -> None:
    req = PermissionRequest(
        operation_type=OP_WRITE,
        target_scope=SCOPE_OWN_PHASE,
        role="Planner",
        force=False,
    )
    decision = PermissionEvaluator().evaluate(req)
    assert decision.allowed is True


# ── PermissionEvaluator: requires_reason ─────────────────────────────────────

def test_evaluate_foreign_no_force_denied() -> None:
    req = PermissionRequest(
        operation_type=OP_WRITE,
        target_scope=SCOPE_FOREIGN_PHASE,
        role="Builder",
        force=False,
    )
    decision = PermissionEvaluator().evaluate(req)
    assert decision.allowed is False
    assert decision.approval_mode == MODE_REQUIRES_REASON


def test_evaluate_foreign_force_without_reason_denied() -> None:
    req = PermissionRequest(
        operation_type=OP_WRITE,
        target_scope=SCOPE_FOREIGN_PHASE,
        role="Builder",
        force=True,
        force_reason=None,
    )
    decision = PermissionEvaluator().evaluate(req)
    assert decision.allowed is False
    assert decision.approval_mode == MODE_REQUIRES_REASON


def test_evaluate_foreign_force_with_reason_allowed() -> None:
    req = PermissionRequest(
        operation_type=OP_WRITE,
        target_scope=SCOPE_FOREIGN_PHASE,
        role="Builder",
        force=True,
        force_reason="intentional cross-phase correction",
    )
    decision = PermissionEvaluator().evaluate(req)
    assert decision.allowed is True
    assert decision.approval_mode == MODE_REQUIRES_REASON
    assert "intentional cross-phase correction" in decision.reason


# ── PermissionEvaluator: blocked ─────────────────────────────────────────────

def test_evaluate_system_artifact_denied() -> None:
    req = PermissionRequest(
        operation_type=OP_WRITE,
        target_scope=SCOPE_SYSTEM,
        role="Builder",
    )
    decision = PermissionEvaluator().evaluate(req)
    assert decision.allowed is False
    assert decision.approval_mode == MODE_BLOCKED


def test_evaluate_system_artifact_blocked_even_with_force_and_reason() -> None:
    """system_artifact は force+reason があっても blocked。"""
    req = PermissionRequest(
        operation_type=OP_WRITE,
        target_scope=SCOPE_SYSTEM,
        role="Builder",
        force=True,
        force_reason="I really need to write run_state.json directly",
    )
    decision = PermissionEvaluator().evaluate(req)
    assert decision.allowed is False
    assert decision.approval_mode == MODE_BLOCKED


# ── fallback: unknown (operation, scope) ─────────────────────────────────────

def test_evaluate_unknown_scope_defaults_to_requires_reason() -> None:
    req = PermissionRequest(
        operation_type=OP_WRITE,
        target_scope="unknown_scope",
        role="Builder",
        force=False,
    )
    decision = PermissionEvaluator().evaluate(req)
    assert decision.allowed is False
    assert decision.approval_mode == MODE_REQUIRES_REASON


def test_evaluate_unknown_scope_with_force_reason_allowed() -> None:
    req = PermissionRequest(
        operation_type=OP_WRITE,
        target_scope="unknown_scope",
        role="Builder",
        force=True,
        force_reason="exceptional case",
    )
    decision = PermissionEvaluator().evaluate(req)
    assert decision.allowed is True
