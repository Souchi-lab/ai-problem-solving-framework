from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path
from typing import Any

from ..storage.artifact_repository import ArtifactRepository


class TransitionType(str, Enum):
    BUILD_NEEDED = "BUILD_NEEDED"
    HUMAN_BLOCKED = "HUMAN_BLOCKED"
    BUILD_COMPLETE = "BUILD_COMPLETE"
    RERUN_REQUESTED = "RERUN_REQUESTED"


class BlockerOwnership(str, Enum):
    SYSTEM = "SYSTEM"
    HUMAN = "HUMAN"


class TransitionOutcomeMissing(FileNotFoundError):
    """Raised when no transition outcome record exists for the run."""


class TransitionOutcomeCorrupt(ValueError):
    """Raised when a transition outcome record exists but is invalid."""


class TransitionOutcomeSuperseded(RuntimeError):
    """Raised when a transition outcome record no longer applies to the current phase."""


@dataclass(frozen=True)
class TransitionOutcomeRecord:
    run_id: str
    transition_type: TransitionType
    transitioned_at: str
    transitioned_by: str
    blocker_owner: BlockerOwnership
    source_phase: str
    target_phase: str

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["transition_type"] = self.transition_type.value
        payload["blocker_owner"] = self.blocker_owner.value
        return payload

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TransitionOutcomeRecord":
        try:
            return cls(
                run_id=str(data["run_id"]),
                transition_type=TransitionType(str(data["transition_type"])),
                transitioned_at=str(data["transitioned_at"]),
                transitioned_by=str(data["transitioned_by"]),
                blocker_owner=BlockerOwnership(str(data["blocker_owner"])),
                source_phase=str(data["source_phase"]),
                target_phase=str(data["target_phase"]),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise TransitionOutcomeCorrupt("transition outcome record failed schema validation") from exc


def _transition_outcome_path(run_dir: Path) -> Path:
    return run_dir / "transition_outcome.json"


def get_transition_outcome(run_dir: Path) -> TransitionOutcomeRecord:
    path = _transition_outcome_path(run_dir)
    if not path.exists():
        raise TransitionOutcomeMissing(f"transition outcome record not found for run '{run_dir.name}'")

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise TransitionOutcomeCorrupt("transition outcome record is not valid JSON") from exc

    record = TransitionOutcomeRecord.from_dict(payload)
    if record.run_id != run_dir.name:
        raise TransitionOutcomeCorrupt(
            f"transition outcome record run_id mismatch: expected '{run_dir.name}', got '{record.run_id}'"
        )
    return record


def write_transition_outcome(run_dir: Path, record: TransitionOutcomeRecord) -> None:
    if record.run_id != run_dir.name:
        raise ValueError(f"record run_id '{record.run_id}' does not match run_dir '{run_dir.name}'")

    artifact_repo = ArtifactRepository(writing_role=None)
    artifact_repo.write(
        _transition_outcome_path(run_dir),
        json.dumps(record.to_dict(), ensure_ascii=False, indent=2),
    )


def clear_transition_outcome(run_dir: Path) -> None:
    path = _transition_outcome_path(run_dir)
    if path.exists():
        path.unlink()
