from __future__ import annotations

from pathlib import Path

import pytest

from apsf.core.ownership import (
    BlockerOwnership,
    TransitionType,
    get_transition_outcome,
    write_transition_outcome,
    TransitionOutcomeMissing,
    TransitionOutcomeRecord,
)
from apsf.core.state.run_state import PhaseStatus
from apsf.core.state.run_state_repository import RunStateRepository
from apsf.core.state.transition_service import TransitionError, TransitionService


def _load_state(run_dir: Path):
    state = RunStateRepository(run_dir).load()
    assert state is not None
    return state


def test_transition_bootstrap_and_forward_flow_resets_runtime_fields(tmp_path: Path) -> None:
    service = TransitionService()

    bootstrap = service.bootstrap(
        tmp_path,
        run_id=tmp_path.name,
        initial_phase="PLAN_NEEDED",
        actor="system",
        reason="bootstrap test",
    )
    assert bootstrap.success is True

    state = _load_state(tmp_path)
    state.retry_count = 4
    state.last_error = "stale"
    state.active_handoff_id = "hf-001"
    state.gate_failures = ["warn-1"]
    RunStateRepository(tmp_path).save(state)

    result = service.transition(
        tmp_path,
        to_phase="BUILD_NEEDED",
        actor="Planner",
        reason="plan approved",
    )

    assert result.success is True
    updated = _load_state(tmp_path)
    assert updated.current_phase == "BUILD_NEEDED"
    assert updated.phase_status == PhaseStatus.PENDING.value
    assert updated.current_owner == "Builder"
    assert updated.retry_count == 0
    assert updated.last_error == ""
    assert updated.gate_failures == []
    assert updated.active_handoff_id == ""


def test_transition_rejects_invalid_rule_for_constrained_actor(tmp_path: Path) -> None:
    service = TransitionService()
    service.bootstrap(
        tmp_path,
        run_id=tmp_path.name,
        initial_phase="PLAN_NEEDED",
        actor="system",
        reason="bootstrap test",
    )

    with pytest.raises(TransitionError, match="VALID_TRANSITIONS"):
        service.transition(
            tmp_path,
            to_phase="RESULT_NEEDED",
            actor="Planner",
            reason="invalid jump",
        )


def test_set_active_handoff_id_updates_non_phase_state_without_changing_phase(tmp_path: Path) -> None:
    service = TransitionService()
    service.bootstrap(
        tmp_path,
        run_id=tmp_path.name,
        initial_phase="GOAL_NEEDED",
        actor="system",
        reason="bootstrap test",
    )
    service.set_status(
        tmp_path,
        PhaseStatus.FAILED.value,
        actor="system",
        reason="mark failed first",
        last_error="stale",
    )

    result = service.set_active_handoff_id(
        tmp_path,
        "hf-123",
        actor="system",
        reason="bind accepted handoff",
    )

    assert result.success is True
    state = _load_state(tmp_path)
    assert state.current_phase == "GOAL_NEEDED"
    assert state.phase_status == PhaseStatus.FAILED.value
    assert state.current_owner == "Human"
    assert state.last_error == "stale"
    assert state.active_handoff_id == "hf-123"


def test_transition_allows_rerun_actor_to_return_to_build_needed(tmp_path: Path) -> None:
    service = TransitionService()
    service.bootstrap(
        tmp_path,
        run_id=tmp_path.name,
        initial_phase="RESULT_NEEDED",
        actor="system",
        reason="bootstrap test",
    )

    result = service.transition(
        tmp_path,
        to_phase="BUILD_NEEDED",
        actor="rerun",
        reason="judge requested review-to-build return",
    )

    assert result.success is True
    state = _load_state(tmp_path)
    assert state.current_phase == "BUILD_NEEDED"
    assert state.phase_status == PhaseStatus.PENDING.value
    assert state.current_owner == "Builder"

    outcome = get_transition_outcome(tmp_path)
    assert outcome.run_id == tmp_path.name
    assert outcome.transition_type == TransitionType.RERUN_REQUESTED
    assert outcome.blocker_owner == BlockerOwnership.SYSTEM
    assert outcome.source_phase == "RESULT_NEEDED"
    assert outcome.target_phase == "BUILD_NEEDED"


def test_transition_writes_system_owned_record_for_judge_return_to_build(tmp_path: Path) -> None:
    service = TransitionService()
    service.bootstrap(
        tmp_path,
        run_id=tmp_path.name,
        initial_phase="REVIEW_NEEDED",
        actor="system",
        reason="bootstrap test",
    )

    result = service.transition(
        tmp_path,
        to_phase="BUILD_NEEDED",
        actor="Judge",
        reason="return to build",
    )

    assert result.success is True
    outcome = get_transition_outcome(tmp_path)
    assert outcome.transition_type == TransitionType.BUILD_NEEDED
    assert outcome.blocker_owner == BlockerOwnership.SYSTEM
    assert outcome.source_phase == "REVIEW_NEEDED"
    assert outcome.target_phase == "BUILD_NEEDED"


def test_transition_clears_stale_human_blocked_record_when_phase_advances(tmp_path: Path) -> None:
    service = TransitionService()
    service.bootstrap(
        tmp_path,
        run_id=tmp_path.name,
        initial_phase="IMPROVE_NEEDED",
        actor="system",
        reason="bootstrap test",
    )
    write_transition_outcome(
        tmp_path,
        TransitionOutcomeRecord(
            run_id=tmp_path.name,
            transition_type=TransitionType.HUMAN_BLOCKED,
            transitioned_at="2026-04-09T00:00:00+00:00",
            transitioned_by="Judge",
            blocker_owner=BlockerOwnership.HUMAN,
            source_phase="IMPROVE_NEEDED",
            target_phase="IMPROVE_NEEDED",
        ),
    )

    service.transition(
        tmp_path,
        to_phase="RESULT_NEEDED",
        actor="Judge",
        reason="human gate resolved",
    )

    with pytest.raises(TransitionOutcomeMissing):
        get_transition_outcome(tmp_path)
