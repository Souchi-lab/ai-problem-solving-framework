"""
CheckpointApplyService - minimal own-run execution checkpoint apply.

This module is the single explicit exception to TransitionService ownership.
It exists only for recovery-time checkpoint restore after RestoreGate approval.

run-068 scope:
    - apply only execution state from recovery/checkpoints/<checkpoint_id>.json
    - mutate only run_state.json fields:
        * current_phase
        * phase_status
        * current_owner
    - preserve non-phase state fields such as retry_count / last_error /
      active_handoff_id / gate_failures
    - require explicit apply_reason
    - block foreign-run checkpoint apply

run-069 polish:
    - emit non-blocking session event trace for success/failure
    - warn once to stderr if session event append fails
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from .restore_gate import RestoreGate, RestoreRequest


RECOVERY_BYPASS_CONTRACT = """
CheckpointApplyService is the single explicit exception to TransitionService.

Allowed bypass:
- recovery-time restore after RestoreGate approval
- current run only
- writes only current_phase / phase_status / current_owner

Forbidden bypass:
- normal Judge / Builder / Critic phase routing
- direct writes from CLI, viewer, rerun, or orchestration flows
- mutation of retry_count / last_error / active_handoff_id / gate_failures
""".strip()


class CheckpointApplyError(Exception):
    """Raised when minimal execution checkpoint apply is blocked or fails."""


@dataclass
class CheckpointApplyResult:
    checkpoint_id: str
    run_id: str
    phase: str
    phase_status: str
    current_owner: str
    apply_reason: str


class CheckpointApplyService:
    """Apply recovery-approved checkpoint metadata to the current run_state only."""

    def __init__(self) -> None:
        self._gate = RestoreGate()

    def apply(
        self,
        run_dir: Path,
        checkpoint_id: str,
        apply_reason: Optional[str],
    ) -> CheckpointApplyResult:
        from ..session.session_event import (
            make_checkpoint_apply_failed_event,
            make_checkpoint_apply_succeeded_event,
        )
        from ..session.session_event_repository import SessionEventRepository
        from ..state.run_state_repository import RunStateRepository

        run_id = run_dir.name
        session_repo = SessionEventRepository(run_dir)
        warned_event_log_failure = False

        def _warn_event_log_failure(exc: Exception) -> None:
            nonlocal warned_event_log_failure
            if warned_event_log_failure:
                return
            warned_event_log_failure = True
            print(
                "[Warn] Failed to append session event log "
                f"({SessionEventRepository.FILENAME}): {exc}. "
                "Continuing without blocking checkpoint apply.",
                file=sys.stderr,
            )

        try:
            checkpoint = self._load_checkpoint(run_dir, checkpoint_id)
            if not apply_reason:
                raise CheckpointApplyError(
                    "execution checkpoint apply requires --apply-reason. "
                    "Provide an explicit reason for overwriting current execution state."
                )

            decision = self._gate.classify(
                RestoreRequest(
                    restore_class="own_run_checkpoint",
                    run_id=str(checkpoint["run_id"]),
                    current_run_id=run_id,
                    target_paths=[],
                    restore_reason=apply_reason,
                )
            )
            if not decision.allowed:
                raise CheckpointApplyError(f"[RestoreGate] {decision.reason}")

            state = self._load_run_state(run_dir)
            self._apply_recovery_phase_bypass(
                run_dir=run_dir,
                state=state,
                checkpoint=checkpoint,
            )

            try:
                session_repo.append(
                    make_checkpoint_apply_succeeded_event(
                        run_id=run_id,
                        checkpoint_id=checkpoint_id,
                        apply_reason=apply_reason,
                        phase=state.current_phase,
                        phase_status=state.phase_status,
                        current_owner=state.current_owner,
                    )
                )
            except Exception as exc:
                _warn_event_log_failure(exc)

            return CheckpointApplyResult(
                checkpoint_id=checkpoint_id,
                run_id=run_id,
                phase=state.current_phase,
                phase_status=state.phase_status,
                current_owner=state.current_owner,
                apply_reason=apply_reason,
            )
        except CheckpointApplyError as exc:
            try:
                session_repo.append(
                    make_checkpoint_apply_failed_event(
                        run_id=run_id,
                        checkpoint_id=checkpoint_id,
                        apply_reason=apply_reason or "",
                        error=str(exc),
                    )
                )
            except Exception as event_exc:
                _warn_event_log_failure(event_exc)
            raise

    def _load_checkpoint(self, run_dir: Path, checkpoint_id: str) -> dict:
        checkpoint_path = run_dir / "recovery" / "checkpoints" / f"{checkpoint_id}.json"
        if not checkpoint_path.exists():
            raise CheckpointApplyError(
                f"checkpoint not found: '{checkpoint_id}' "
                f"(expected: {checkpoint_path})"
            )
        try:
            checkpoint = json.loads(checkpoint_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            raise CheckpointApplyError(
                f"failed to load checkpoint '{checkpoint_id}': {exc}"
            ) from exc

        required = ("run_id", "phase", "phase_status", "current_owner")
        missing = [key for key in required if not checkpoint.get(key)]
        if missing:
            raise CheckpointApplyError(
                f"malformed checkpoint '{checkpoint_id}': missing required field(s): "
                f"{', '.join(missing)}"
            )
        return checkpoint

    def _load_run_state(self, run_dir: Path):  # -> RunState
        from ..state.run_state_repository import RunStateRepository

        state = RunStateRepository(run_dir).load()
        if state is None:
            raise CheckpointApplyError(
                f"run_state.json not found in '{run_dir.name}'. "
                "Execution checkpoint apply requires an initialized run state."
            )
        return state

    def _apply_recovery_phase_bypass(self, run_dir: Path, state, checkpoint: dict) -> None:
        """
        Recovery-only direct write boundary.

        This method is the only sanctioned bypass of TransitionService for
        phase fields. Keep all other run_state mutations outside this path.
        """
        from ..state.run_state_repository import RunStateRepository

        # Explicit recovery-only bypass of TransitionService ownership.
        state.current_phase = str(checkpoint["phase"])
        state.phase_status = str(checkpoint["phase_status"])
        state.current_owner = str(checkpoint["current_owner"])
        RunStateRepository(run_dir).save(state)
