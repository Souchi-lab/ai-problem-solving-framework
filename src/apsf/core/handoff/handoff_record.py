"""
HandoffRecord — handoff.json の canonical schema

handoff.json を正本として持つ。handoff.md は view（レンダリング結果）にすぎない。
HandoffStatus は core/domain/enums.py の値を文字列として保持する。
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _new_handoff_id() -> str:
    return uuid.uuid4().hex


@dataclass
class HandoffRecord:
    """
    handoff.json の canonical schema。

    Fields:
        handoff_id:                    UUID (uuid4 hex)
        from_role:                     委譲元 role 名 ("Planner" / "Builder" / "Critic" / "Human")
        to_role:                       委譲先 role 名
        artifact_scope:                このhandoff が対象とする artifact ファイル名リスト
        status:                        HandoffStatus value ("draft" / "offered" / "accepted" / "rejected" / "superseded")
        accepted_by_next_role:         受理した role 名（未受理時は ""）
        supersedes:                    置き換え元 handoff_id（なければ ""）
        created_at:                    ISO 8601 UTC
        accepted_at:                   ISO 8601 UTC（未受理時は ""）
        proceed_without_handoff_reason: handoff なしで進んだ理由（あれば）
    """

    handoff_id: str = field(default_factory=_new_handoff_id)
    from_role: str = ""
    to_role: str = ""
    artifact_scope: list[str] = field(default_factory=list)
    status: str = "offered"
    accepted_by_next_role: str = ""
    supersedes: str = ""
    created_at: str = field(default_factory=_now_iso)
    accepted_at: str = ""
    proceed_without_handoff_reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "handoff_id": self.handoff_id,
            "from_role": self.from_role,
            "to_role": self.to_role,
            "artifact_scope": list(self.artifact_scope),
            "status": self.status,
            "accepted_by_next_role": self.accepted_by_next_role,
            "supersedes": self.supersedes,
            "created_at": self.created_at,
            "accepted_at": self.accepted_at,
            "proceed_without_handoff_reason": self.proceed_without_handoff_reason,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "HandoffRecord":
        """前方互換デシリアライズ。未知フィールドは無視、欠損フィールドはデフォルト値。"""
        return cls(
            handoff_id=data.get("handoff_id", _new_handoff_id()),
            from_role=data.get("from_role", ""),
            to_role=data.get("to_role", ""),
            artifact_scope=list(data.get("artifact_scope", [])),
            status=data.get("status", "offered"),
            accepted_by_next_role=data.get("accepted_by_next_role", ""),
            supersedes=data.get("supersedes", ""),
            created_at=data.get("created_at", _now_iso()),
            accepted_at=data.get("accepted_at", ""),
            proceed_without_handoff_reason=data.get("proceed_without_handoff_reason", ""),
        )
