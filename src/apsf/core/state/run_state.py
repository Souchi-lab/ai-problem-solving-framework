"""
RunState — run_state.json の canonical schema

run の現在 phase・進行状態・retry 記録を保持する。
artifact truth（各 .md の内容）とは分離し、phase routing の canonical source となる。

Agent OS v1 migration Step 3 で導入。
Step 7 で phase_detector の advisory 化が完了すると、
このモジュールが phase routing の完全な canonical source になる。
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class PhaseStatus(str, Enum):
    """run_state.json が持つ phase 進行状態。"""

    PENDING      = "pending"       # phase 開始前（前 phase が完了し次 phase が確定した状態）
    IN_PROGRESS  = "in_progress"   # LLM 実行中（中断・クラッシュ検知に使用）
    COMPLETED    = "completed"     # phase 完了・次 phase へ進める
    FAILED       = "failed"        # エラー発生・retry 可能


@dataclass
class RunState:
    """
    run_state.json の canonical schema。

    フィールド:
        run_id:            run ディレクトリ名（例: "2026-03-31-038_fw-improvement_..."）
        current_phase:     Phase.value 文字列（例: "PLAN_NEEDED"）
        phase_status:      PhaseStatus.value 文字列
        current_owner:     現 phase の担当 role 名（"Planner" / "Builder" / "Critic" / "Human" / ""）
        retry_count:       現 phase の retry 回数（phase が進むとリセット）
        last_error:        最後のエラーメッセージ（正常時は ""）
        active_handoff_id: 参照中 handoff ID（未使用時は ""）

    責務境界:
        - artifact の内容（plan.md 等）は持たない
        - artifact status（draft / final 等）は持たない（Step 5 の manifest で扱う）
        - cross-run ledger は持たない
    """

    run_id:            str
    current_phase:     str
    phase_status:      str
    current_owner:     str
    retry_count:       int
    last_error:        str
    active_handoff_id: str
    gate_failures:     list = field(default_factory=list)  # advisory gate failure reasons（空リストが正常）

    def to_dict(self) -> dict[str, Any]:
        """JSON シリアライズ用 dict を返す。"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RunState":
        """JSON デシリアライズ。不明フィールドは無視する（前方互換）。"""
        return cls(
            run_id=str(data.get("run_id", "")),
            current_phase=str(data.get("current_phase", "")),
            phase_status=str(data.get("phase_status", PhaseStatus.PENDING.value)),
            current_owner=str(data.get("current_owner", "")),
            retry_count=int(data.get("retry_count", 0)),
            last_error=str(data.get("last_error", "")),
            active_handoff_id=str(data.get("active_handoff_id", "")),
            gate_failures=list(data.get("gate_failures", [])),
        )
