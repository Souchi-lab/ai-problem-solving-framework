"""
TransitionService — single owner of phase transitions in run_state.json.

All callers that need to change current_phase or phase_status must go through
this service. RunStateRepository is the internal persistence layer and must not
be called directly for phase mutations from outside this module.

Explicit exception (T7 — CheckpointApplyService):
    src/apsf/core/restore/checkpoint_apply_service.py is a recovery path
    protected by its own RestoreGate validation. It directly mutates
    run_state fields as a recovery operation, not a normal phase transition.
    This is the only authorised caller that bypasses TransitionService.
    No other module may write current_phase / phase_status / current_owner
    through RunStateRepository.save() directly.

Phase Transition Rule Map (SC1):

    Normal forward flow:
        GOAL_NEEDED  → SETUP_NEEDED | PLAN_NEEDED
        SETUP_NEEDED → PLAN_NEEDED
        PLAN_NEEDED  → BUILD_NEEDED | IMPROVE_PLAN_OPTIONAL
        IMPROVE_PLAN_OPTIONAL → BUILD_NEEDED | PLAN_NEEDED | IMPROVE_NEEDED
        BUILD_NEEDED → REVIEW_NEEDED
        REVIEW_NEEDED → BUILD_NEEDED | REVIEW_NEEDED | IMPROVE_PLAN_OPTIONAL
                      | IMPROVE_NEEDED | VERIFY_OPTIONAL | RESULT_NEEDED
                      | TRANSCRIPT_RECOMMENDED | COMPLETE
        IMPROVE_NEEDED → VERIFY_OPTIONAL | RESULT_NEEDED | BUILD_NEEDED
                       | PLAN_NEEDED | REVIEW_NEEDED
        VERIFY_OPTIONAL → RESULT_NEEDED | BUILD_NEEDED | REVIEW_NEEDED
        RESULT_NEEDED → TRANSCRIPT_RECOMMENDED | COMPLETE
        TRANSCRIPT_RECOMMENDED → COMPLETE

    Bootstrap (no prior state):
        "" → any phase

    Unconstrained actors (bypass rule map):
        Judge   — Judge decisions can return to any phase
        rerun   — Rerun scripts (apsf-rerun-*.ps1)
        system  — System-level bootstrap and advisory sync operations
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from ..ownership.record import (
    BlockerOwnership,
    TransitionOutcomeRecord,
    TransitionType,
    clear_transition_outcome,
    write_transition_outcome,
)
from .run_state import PhaseStatus, RunState
from .run_state_repository import RunStateRepository


# ---------------------------------------------------------------------------
# Valid transition rule map (SC1: all phase transition patterns documented)
# ---------------------------------------------------------------------------

VALID_TRANSITIONS: frozenset[tuple[str, str]] = frozenset({
    # ── Bootstrap: no prior state ──────────────────────────────────────────
    ("", "GOAL_NEEDED"),
    ("", "SETUP_NEEDED"),
    ("", "PLAN_NEEDED"),
    ("", "IMPROVE_PLAN_OPTIONAL"),
    ("", "BUILD_NEEDED"),
    ("", "REVIEW_NEEDED"),
    ("", "IMPROVE_NEEDED"),
    ("", "VERIFY_OPTIONAL"),
    ("", "RESULT_NEEDED"),
    ("", "TRANSCRIPT_RECOMMENDED"),
    ("", "COMPLETE"),
    # ── Normal forward flow ────────────────────────────────────────────────
    ("GOAL_NEEDED", "SETUP_NEEDED"),
    ("GOAL_NEEDED", "PLAN_NEEDED"),          # setup already filled
    ("SETUP_NEEDED", "PLAN_NEEDED"),
    ("PLAN_NEEDED", "BUILD_NEEDED"),
    ("PLAN_NEEDED", "IMPROVE_PLAN_OPTIONAL"),
    ("IMPROVE_PLAN_OPTIONAL", "BUILD_NEEDED"),
    ("IMPROVE_PLAN_OPTIONAL", "PLAN_NEEDED"),
    ("IMPROVE_PLAN_OPTIONAL", "IMPROVE_NEEDED"),
    ("BUILD_NEEDED", "REVIEW_NEEDED"),
    # ── From REVIEW_NEEDED ─────────────────────────────────────────────────
    ("REVIEW_NEEDED", "BUILD_NEEDED"),           # Judge: return to build
    ("REVIEW_NEEDED", "REVIEW_NEEDED"),          # Judge: return to review (rerun critic)
    ("REVIEW_NEEDED", "IMPROVE_PLAN_OPTIONAL"),
    ("REVIEW_NEEDED", "IMPROVE_NEEDED"),
    ("REVIEW_NEEDED", "VERIFY_OPTIONAL"),
    ("REVIEW_NEEDED", "RESULT_NEEDED"),
    ("REVIEW_NEEDED", "TRANSCRIPT_RECOMMENDED"),
    ("REVIEW_NEEDED", "COMPLETE"),
    # ── Improve phase ──────────────────────────────────────────────────────
    ("IMPROVE_NEEDED", "VERIFY_OPTIONAL"),
    ("IMPROVE_NEEDED", "RESULT_NEEDED"),
    ("IMPROVE_NEEDED", "BUILD_NEEDED"),          # Judge return
    ("IMPROVE_NEEDED", "PLAN_NEEDED"),           # Judge replan
    ("IMPROVE_NEEDED", "REVIEW_NEEDED"),         # Judge return to review
    # ── Verify phase ───────────────────────────────────────────────────────
    ("VERIFY_OPTIONAL", "RESULT_NEEDED"),
    ("VERIFY_OPTIONAL", "BUILD_NEEDED"),
    ("VERIFY_OPTIONAL", "REVIEW_NEEDED"),
    # ── Close-out ──────────────────────────────────────────────────────────
    ("RESULT_NEEDED", "TRANSCRIPT_RECOMMENDED"),
    ("RESULT_NEEDED", "COMPLETE"),
    ("TRANSCRIPT_RECOMMENDED", "COMPLETE"),
    # ── Human phase auto-advance (advisory detector catches completed work) ─
    ("SETUP_NEEDED", "GOAL_NEEDED"),  # edge case, unlikely
})

# Actors that bypass the transition rule map.
# This does not grant direct RunStateRepository.save() access; callers still
# persist through TransitionService. The only direct-writer exception is the
# recovery-only CheckpointApplyService boundary.
_UNCONSTRAINED_ACTORS: frozenset[str] = frozenset({
    "Judge",   # Judge decisions can return the run to any phase
    "rerun",   # Rerun scripts (apsf-rerun-*.ps1)
    "system",  # System bootstrap, advisory sync, and viewer operations
})

# Default current_owner for well-known phases.
_PHASE_OWNER: dict[str, str] = {
    "GOAL_NEEDED":            "Human",
    "SETUP_NEEDED":           "Human",
    "PLAN_NEEDED":            "Planner",
    "IMPROVE_PLAN_OPTIONAL":  "Human",
    "BUILD_NEEDED":           "Builder",
    "REVIEW_NEEDED":          "Critic",
    "IMPROVE_NEEDED":         "Human",
    "VERIFY_OPTIONAL":        "Human",
    "RESULT_NEEDED":          "Human",
    "TRANSCRIPT_RECOMMENDED": "Human",
    "COMPLETE":               "(none)",
}


class TransitionError(Exception):
    """Raised when a phase transition is rejected by validation."""


@dataclass
class TransitionResult:
    """Result of a phase transition or status update operation."""

    success: bool
    run_id: str
    from_phase: str
    to_phase: str
    phase_status: str
    current_owner: str
    actor: str
    reason: str
    error: str = ""


class TransitionService:
    """
    Single owner of phase transitions in run_state.json.

    External callers must use this service for any operation that changes
    current_phase or phase_status in run_state.json.

    RunStateRepository is the internal persistence layer used only from
    within this service (and the explicit exception: CheckpointApplyService).
    """

    def transition(
        self,
        run_dir: Path,
        to_phase: str,
        actor: str,
        reason: str,
        *,
        from_phase: Optional[str] = None,
        phase_status: str = PhaseStatus.PENDING.value,
        current_owner: str = "",
        gate_failures: Optional[list] = None,
        force: bool = False,
    ) -> TransitionResult:
        """
        Transition the run to ``to_phase``.

        If ``from_phase`` is provided and does not match the current state,
        returns a failure result without modifying state.

        Transition validation is skipped for actors in ``_UNCONSTRAINED_ACTORS``
        or when ``force=True``.

        On success, resets retry_count, last_error, and gate_failures (unless
        ``gate_failures`` is provided, in which case that value is stored).
        Phase transitions also clear active_handoff_id because the prior
        ownership handshake is stale once the phase changes.

        Creates a new run_state.json if none exists.

        Raises:
            TransitionError: if the (from, to) pair is not in VALID_TRANSITIONS
                and the actor is not unconstrained and force=False.
        """
        state_repo = RunStateRepository(run_dir)
        state = state_repo.load()

        actual_from = state.current_phase if state is not None else ""

        if from_phase is not None and from_phase != actual_from:
            return TransitionResult(
                success=False,
                run_id=run_dir.name,
                from_phase=actual_from,
                to_phase=to_phase,
                phase_status=state.phase_status if state else "",
                current_owner=state.current_owner if state else "",
                actor=actor,
                reason=reason,
                error=(
                    f"expected from_phase='{from_phase}' "
                    f"but current phase is '{actual_from}'"
                ),
            )

        if not force and actor not in _UNCONSTRAINED_ACTORS:
            if (actual_from, to_phase) not in VALID_TRANSITIONS:
                raise TransitionError(
                    f"transition '{actual_from}' → '{to_phase}' is not in VALID_TRANSITIONS. "
                    f"actor='{actor}', reason='{reason}'. "
                    "Use an unconstrained actor or force=True to bypass."
                )

        owner = current_owner or _PHASE_OWNER.get(to_phase, "")

        now_iso = datetime.now(timezone.utc).isoformat()
        if state is None:
            state = RunState(
                run_id=run_dir.name,
                current_phase=to_phase,
                phase_status=phase_status,
                current_owner=owner,
                retry_count=0,
                last_error="",
                active_handoff_id="",
                gate_failures=gate_failures if gate_failures is not None else [],
                phase_entered_at=now_iso,
            )
        else:
            state.current_phase = to_phase
            state.phase_status = phase_status
            state.current_owner = owner
            state.retry_count = 0
            state.last_error = ""
            state.active_handoff_id = ""
            state.gate_failures = gate_failures if gate_failures is not None else []
            state.phase_entered_at = now_iso

        state_repo.save(state)
        self._sync_transition_outcome(
            run_dir=run_dir,
            from_phase=actual_from,
            to_phase=to_phase,
            actor=actor,
        )

        return TransitionResult(
            success=True,
            run_id=run_dir.name,
            from_phase=actual_from,
            to_phase=to_phase,
            phase_status=phase_status,
            current_owner=owner,
            actor=actor,
            reason=reason,
        )

    def _sync_transition_outcome(
        self,
        *,
        run_dir: Path,
        from_phase: str,
        to_phase: str,
        actor: str,
    ) -> None:
        # transition_outcome.json is a current-cycle authority record.
        # Any new phase transition supersedes prior human-blocked/system-blocked
        # ownership unless this transition itself establishes BUILD_NEEDED or
        # rerun-to-build ownership.
        if to_phase != "BUILD_NEEDED":
            clear_transition_outcome(run_dir)
            return

        transition_type = TransitionType.BUILD_NEEDED
        if actor == "rerun":
            transition_type = TransitionType.RERUN_REQUESTED

        write_transition_outcome(
            run_dir,
            TransitionOutcomeRecord(
                run_id=run_dir.name,
                transition_type=transition_type,
                transitioned_at=datetime.now(timezone.utc).isoformat(),
                transitioned_by=actor,
                blocker_owner=BlockerOwnership.SYSTEM,
                source_phase=from_phase,
                target_phase=to_phase,
            ),
        )

    def set_status(
        self,
        run_dir: Path,
        phase_status: str,
        actor: str,
        reason: str,
        *,
        last_error: str = "",
        increment_retry: bool = False,
        gate_failures: Optional[list] = None,
    ) -> TransitionResult:
        """
        Update phase_status without changing current_phase.

        Used for IN_PROGRESS, FAILED, and COMPLETED status updates within
        the current phase. Does not validate against VALID_TRANSITIONS because
        the phase itself does not change.

        Returns a failure result (success=False) if no run_state.json exists.
        """
        state_repo = RunStateRepository(run_dir)
        state = state_repo.load()

        if state is None:
            return TransitionResult(
                success=False,
                run_id=run_dir.name,
                from_phase="",
                to_phase="",
                phase_status=phase_status,
                current_owner="",
                actor=actor,
                reason=reason,
                error="run_state.json does not exist; cannot set status without a phase",
            )

        current = state.current_phase
        state.phase_status = phase_status
        state.last_error = last_error
        if increment_retry:
            state.retry_count += 1
        if gate_failures is not None:
            state.gate_failures = gate_failures

        state_repo.save(state)

        return TransitionResult(
            success=True,
            run_id=run_dir.name,
            from_phase=current,
            to_phase=current,
            phase_status=phase_status,
            current_owner=state.current_owner,
            actor=actor,
            reason=reason,
        )

    def bootstrap(
        self,
        run_dir: Path,
        run_id: str,
        initial_phase: str,
        actor: str,
        reason: str,
        *,
        current_owner: str = "",
    ) -> TransitionResult:
        """
        Create a new run_state.json at ``initial_phase`` if none exists.

        If run_state.json already exists, returns immediately with the
        existing phase (no mutation).
        """
        state_repo = RunStateRepository(run_dir)
        existing = state_repo.load()

        if existing is not None:
            return TransitionResult(
                success=True,
                run_id=existing.run_id,
                from_phase=existing.current_phase,
                to_phase=existing.current_phase,
                phase_status=existing.phase_status,
                current_owner=existing.current_owner,
                actor=actor,
                reason=reason,
            )

        owner = current_owner or _PHASE_OWNER.get(initial_phase, "")
        state = RunState(
            run_id=run_id,
            current_phase=initial_phase,
            phase_status=PhaseStatus.PENDING.value,
            current_owner=owner,
            retry_count=0,
            last_error="",
            active_handoff_id="",
            gate_failures=[],
        )
        state_repo.save(state)

        return TransitionResult(
            success=True,
            run_id=run_id,
            from_phase="",
            to_phase=initial_phase,
            phase_status=PhaseStatus.PENDING.value,
            current_owner=owner,
            actor=actor,
            reason=reason,
        )

    def set_active_handoff_id(
        self,
        run_dir: Path,
        handoff_id: str,
        actor: str,
        reason: str,
    ) -> TransitionResult:
        """
        Update active_handoff_id without changing current_phase.

        This is a non-phase state mutation, but it still belongs inside the
        canonical run_state boundary so callers do not write run_state.json
        directly from orchestration code.
        """
        state_repo = RunStateRepository(run_dir)
        state = state_repo.load()

        if state is None:
            return TransitionResult(
                success=False,
                run_id=run_dir.name,
                from_phase="",
                to_phase="",
                phase_status="",
                current_owner="",
                actor=actor,
                reason=reason,
                error="run_state.json does not exist; cannot set active_handoff_id",
            )

        current = state.current_phase
        state.active_handoff_id = handoff_id
        state_repo.save(state)

        return TransitionResult(
            success=True,
            run_id=run_dir.name,
            from_phase=current,
            to_phase=current,
            phase_status=state.phase_status,
            current_owner=state.current_owner,
            actor=actor,
            reason=reason,
        )

    def get_current_phase(self, run_dir: Path) -> str:
        """Return current_phase from run_state.json, or "" if no state file exists."""
        state = RunStateRepository(run_dir).load()
        return state.current_phase if state is not None else ""
