"""
RestoreGate — restore apply の前段 safety gate

run-063 spec (restore-apply-safety-gate-spec.md) の classify priority order を実装する。

Priority order:
  1. foreign_run   : run_id != current_run_id → blocked
  2. system_artifact_touching : target_paths に system artifact を含む → blocked
  3. mixed         : restore_class == "mixed" → blocked
  4. own_run_*     : restore_reason が必須（あれば allowed）

この gate は permission matrix の前段 pre-flight として動作し、
matrix を置き換えない。gate 通過後も matrix の scope 評価が後段で実行される。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal, Optional

# system artifact 判定は run-053 の _SYSTEM_ARTIFACTS frozenset と一致させる
from ..permissions.permission_matrix import _SYSTEM_ARTIFACTS

RestoreClass = Literal[
    "own_run_checkpoint",
    "own_run_snapshot",
    "foreign_run",
    "system_artifact_touching",
    "mixed",
]


@dataclass
class RestoreRequest:
    """
    RestoreGate への入力。

    Fields:
        restore_class:   呼び出し元が申告する操作分類
        run_id:          apply 元の run ID（snapshot/checkpoint が属する run）
        current_run_id:  現在の（apply 先の）run ID
        target_paths:    書き込み先ファイルの相対パス一覧（run_dir 起点）
        restore_reason:  理由文字列（None または空文字は "理由なし" として扱う）
    """

    restore_class: RestoreClass
    run_id: str
    current_run_id: str
    target_paths: list[str] = field(default_factory=list)
    restore_reason: Optional[str] = None


@dataclass
class RestoreGateDecision:
    """
    RestoreGate.classify() の結果。

    Fields:
        restore_class: 実際に判定に使われた class（申告値または上書き）
        verdict:       "requires_reason" | "blocked"（v1 は "allow" 未使用）
        allowed:       True = 操作を許可する
        reason:        拒否理由または承認経路の説明
    """

    restore_class: RestoreClass
    verdict: str
    allowed: bool
    reason: str


def _filename(path: str) -> str:
    """パス文字列から basename を返す（system artifact はファイル名で判定する）。"""
    return Path(path).name


class RestoreGate:
    """
    RestoreRequest を受け取り RestoreGateDecision を返す。

    classify() の判定順序は run-063 spec の "Classify Priority Order" に従う:
      1. foreign_run → blocked
      2. system_artifact_touching → blocked
      3. mixed → blocked
      4. own_run_snapshot / own_run_checkpoint → requires_reason
    """

    def classify(self, request: RestoreRequest) -> RestoreGateDecision:
        # 1. foreign_run
        if request.run_id != request.current_run_id:
            return RestoreGateDecision(
                restore_class="foreign_run",
                verdict="blocked",
                allowed=False,
                reason=(
                    f"foreign-run restore is blocked: "
                    f"source run '{request.run_id}' != current run '{request.current_run_id}'."
                ),
            )

        # 2. system_artifact_touching
        #    own-run snapshot であっても、target_paths に system artifact が含まれれば blocked。
        #    (run-063 spec: classify priority order の 2 番が 4 番より先に評価される)
        system_hits = [p for p in request.target_paths if _filename(p) in _SYSTEM_ARTIFACTS]
        if system_hits:
            return RestoreGateDecision(
                restore_class="system_artifact_touching",
                verdict="blocked",
                allowed=False,
                reason=(
                    f"system artifact touching restore is blocked: "
                    f"{system_hits} contains system artifact(s). "
                    f"System artifacts: {sorted(_SYSTEM_ARTIFACTS)}."
                ),
            )

        # 3. mixed
        if request.restore_class == "mixed":
            return RestoreGateDecision(
                restore_class="mixed",
                verdict="blocked",
                allowed=False,
                reason=(
                    "mixed restore (execution + file state in one apply) is blocked: "
                    "partial-apply failure recovery is undefined. "
                    "Defer until atomicity design is complete."
                ),
            )

        # 4. own_run_snapshot / own_run_checkpoint → requires_reason
        if not request.restore_reason:
            return RestoreGateDecision(
                restore_class=request.restore_class,
                verdict="requires_reason",
                allowed=False,
                reason=(
                    f"{request.restore_class} restore requires --restore-reason. "
                    "Provide an explicit reason for overwriting current file state."
                ),
            )

        return RestoreGateDecision(
            restore_class=request.restore_class,
            verdict="requires_reason",
            allowed=True,
            reason=f"restore accepted with reason: {request.restore_reason}",
        )
