from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from .record import (
    BlockerOwnership,
    TransitionOutcomeCorrupt,
    TransitionOutcomeMissing,
    TransitionOutcomeSuperseded,
    get_transition_outcome,
)
from ..state.run_state_repository import RunStateRepository


class OwnershipResolutionState(str, Enum):
    SYSTEM = "SYSTEM"
    HUMAN = "HUMAN"
    UNRECORDED = "UNRECORDED"
    CORRUPT = "CORRUPT"
    SUPERSEDED = "SUPERSEDED"


@dataclass(frozen=True)
class OwnershipResolution:
    state: OwnershipResolutionState
    owner: BlockerOwnership | None = None
    detail: str | None = None


class CanonicalOwnershipResolver:
    """Resolve blocker ownership from the durable transition-outcome record only."""

    def resolve(self, run_dir: Path) -> BlockerOwnership:
        record = get_transition_outcome(run_dir)
        state = RunStateRepository(run_dir).load()
        if state is not None and state.current_phase and record.target_phase != state.current_phase:
            raise TransitionOutcomeSuperseded(
                "transition outcome record is superseded by the current phase: "
                f"record target_phase='{record.target_phase}', current_phase='{state.current_phase}'"
            )
        return record.blocker_owner

    def inspect(self, run_dir: Path) -> OwnershipResolution:
        try:
            owner = self.resolve(run_dir)
        except TransitionOutcomeMissing as exc:
            return OwnershipResolution(
                state=OwnershipResolutionState.UNRECORDED,
                detail=str(exc),
            )
        except TransitionOutcomeCorrupt as exc:
            return OwnershipResolution(
                state=OwnershipResolutionState.CORRUPT,
                detail=str(exc),
            )
        except TransitionOutcomeSuperseded as exc:
            return OwnershipResolution(
                state=OwnershipResolutionState.SUPERSEDED,
                detail=str(exc),
            )

        state = OwnershipResolutionState.HUMAN if owner is BlockerOwnership.HUMAN else OwnershipResolutionState.SYSTEM
        return OwnershipResolution(state=state, owner=owner)
