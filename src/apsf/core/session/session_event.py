"""
SessionEvent - canonical schema for session_events.jsonl.

This module defines the append-only event shapes used for lightweight
observability. These events are facts, not current truth.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


EVENT_ACT_STARTED = "act_started"
EVENT_ACT_COMPLETED = "act_completed"
EVENT_ACT_FAILED = "act_failed"
EVENT_CHECKPOINT_APPLY_SUCCEEDED = "checkpoint_apply_succeeded"
EVENT_CHECKPOINT_APPLY_FAILED = "checkpoint_apply_failed"
EVENT_SNAPSHOT_APPLY_SUCCEEDED = "snapshot_apply_succeeded"
EVENT_SNAPSHOT_APPLY_FAILED = "snapshot_apply_failed"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _new_event_id() -> str:
    return str(uuid.uuid4())


@dataclass
class SessionEvent:
    event_id: str
    timestamp: str
    event_type: str
    run_id: str
    payload: dict = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "timestamp": self.timestamp,
            "event_type": self.event_type,
            "run_id": self.run_id,
            "payload": self.payload,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SessionEvent":
        return cls(
            event_id=str(data.get("event_id", "")),
            timestamp=str(data.get("timestamp", "")),
            event_type=str(data.get("event_type", "")),
            run_id=str(data.get("run_id", "")),
            payload=dict(data.get("payload", {})),
        )


def make_act_started_event(
    run_id: str,
    phase: str,
    target_file: str,
    owner: str,
) -> SessionEvent:
    return SessionEvent(
        event_id=_new_event_id(),
        timestamp=_now_iso(),
        event_type=EVENT_ACT_STARTED,
        run_id=run_id,
        payload={"phase": phase, "target_file": target_file, "owner": owner},
    )


def make_act_completed_event(
    run_id: str,
    phase: str,
    target_file: str,
    next_phase: str,
) -> SessionEvent:
    return SessionEvent(
        event_id=_new_event_id(),
        timestamp=_now_iso(),
        event_type=EVENT_ACT_COMPLETED,
        run_id=run_id,
        payload={"phase": phase, "target_file": target_file, "next_phase": next_phase},
    )


def make_act_failed_event(
    run_id: str,
    phase: str,
    target_file: str,
    error: str,
) -> SessionEvent:
    return SessionEvent(
        event_id=_new_event_id(),
        timestamp=_now_iso(),
        event_type=EVENT_ACT_FAILED,
        run_id=run_id,
        payload={"phase": phase, "target_file": target_file, "error": error},
    )


def make_checkpoint_apply_succeeded_event(
    run_id: str,
    checkpoint_id: str,
    apply_reason: str,
    phase: str,
    phase_status: str,
    current_owner: str,
) -> SessionEvent:
    return SessionEvent(
        event_id=_new_event_id(),
        timestamp=_now_iso(),
        event_type=EVENT_CHECKPOINT_APPLY_SUCCEEDED,
        run_id=run_id,
        payload={
            "checkpoint_id": checkpoint_id,
            "apply_reason": apply_reason,
            "phase": phase,
            "phase_status": phase_status,
            "current_owner": current_owner,
        },
    )


def make_checkpoint_apply_failed_event(
    run_id: str,
    checkpoint_id: str,
    apply_reason: str,
    error: str,
) -> SessionEvent:
    return SessionEvent(
        event_id=_new_event_id(),
        timestamp=_now_iso(),
        event_type=EVENT_CHECKPOINT_APPLY_FAILED,
        run_id=run_id,
        payload={
            "checkpoint_id": checkpoint_id,
            "apply_reason": apply_reason,
            "error": error,
        },
    )


def make_snapshot_apply_succeeded_event(
    run_id: str,
    snapshot_id: str,
    apply_reason: str,
    restored_paths: list[str],
) -> SessionEvent:
    return SessionEvent(
        event_id=_new_event_id(),
        timestamp=_now_iso(),
        event_type=EVENT_SNAPSHOT_APPLY_SUCCEEDED,
        run_id=run_id,
        payload={
            "snapshot_id": snapshot_id,
            "apply_reason": apply_reason,
            "restored_paths": restored_paths,
        },
    )


def make_snapshot_apply_failed_event(
    run_id: str,
    snapshot_id: str,
    apply_reason: str,
    error: str,
) -> SessionEvent:
    return SessionEvent(
        event_id=_new_event_id(),
        timestamp=_now_iso(),
        event_type=EVENT_SNAPSHOT_APPLY_FAILED,
        run_id=run_id,
        payload={
            "snapshot_id": snapshot_id,
            "apply_reason": apply_reason,
            "error": error,
        },
    )
