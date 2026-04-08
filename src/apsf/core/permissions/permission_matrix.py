"""
PermissionMatrix — operation_type × target_scope × approval_mode の最小 evaluator

責務:
  - 「どの操作を」「どの範囲で」「どう承認するか」を 1 つのモデルで表現する
  - 既存の role-boundary / ownership check を置き換えない（Option A: 前段 preflight として追加）
  - sandbox 実装・MCP registry・GUI 権限 UI は scope 外

既存 guard との関係:
  role_rules.check_role_boundary  — role 別の forbidden table（downstream で継続稼働）
  ownership_policy.check_ownership — artifact の owner 照合（downstream で継続稼働）
  --force / --force-reason strict  — permission matrix の requires_reason と対応

3 軸:
  operation_type : "write" （v1 は write のみ）
  target_scope   : "own_phase_artifact" | "foreign_phase_artifact" | "system_artifact"
  approval_mode  : "auto" | "requires_reason" | "blocked"
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

# ── 定数 ─────────────────────────────────────────────────────────────────────

# operation_type
OP_WRITE = "write"

# target_scope
SCOPE_OWN_PHASE     = "own_phase_artifact"
SCOPE_FOREIGN_PHASE = "foreign_phase_artifact"
SCOPE_SYSTEM        = "system_artifact"

# approval_mode
MODE_AUTO           = "auto"
MODE_REQUIRES_REASON = "requires_reason"
MODE_BLOCKED        = "blocked"

# ── システム管理ファイル（agent が直接 write してはならない）────────────────────
_SYSTEM_ARTIFACTS: frozenset[str] = frozenset({
    "run_state.json",
    "artifact_manifest.json",
    "handoff.json",
    "force_audit.json",
    "session_events.jsonl",
})

# ── role → 所有 artifact のマッピング ─────────────────────────────────────────
_ROLE_OWNED_ARTIFACTS: dict[str, frozenset[str]] = {
    "Planner": frozenset({"plan.md"}),
    "Builder": frozenset({"build.md"}),
    "Critic":  frozenset({"review.md"}),
    "Human":   frozenset({
        "goal.md", "execution-assignment.md",
        "improve.md", "improve-plan.md",
        "verify.md", "result.md",
    }),
    "Judge":   frozenset({
        "goal.md", "execution-assignment.md",
        "improve.md", "improve-plan.md",
        "verify.md", "result.md",
    }),
}

# ── static permission matrix ─────────────────────────────────────────────────
# (operation_type, target_scope) → approval_mode
_MATRIX: dict[tuple[str, str], str] = {
    (OP_WRITE, SCOPE_OWN_PHASE):     MODE_AUTO,
    (OP_WRITE, SCOPE_FOREIGN_PHASE): MODE_REQUIRES_REASON,
    (OP_WRITE, SCOPE_SYSTEM):        MODE_BLOCKED,
}


# ── schema ───────────────────────────────────────────────────────────────────

@dataclass
class PermissionRequest:
    """
    permission 判定のリクエスト。

    Fields:
        operation_type: 操作種別（"write"）
        target_scope:   対象範囲（SCOPE_* 定数）
        role:           実行ロール名（"Planner" / "Builder" / "Critic" / "Human"）
        force:          --force フラグ
        force_reason:   --force-reason 文字列（なければ None）
    """
    operation_type: str
    target_scope:   str
    role:           str
    force:          bool = False
    force_reason:   Optional[str] = None


@dataclass
class PermissionDecision:
    """
    permission 判定の結果。

    Fields:
        allowed:       許可するか
        approval_mode: 要求された承認方式
        reason:        拒否理由 or 承認経路の説明
    """
    allowed:       bool
    approval_mode: str
    reason:        str = ""


# ── helper ───────────────────────────────────────────────────────────────────

def infer_target_scope(role: str, target_file: str) -> str:
    """
    role と target_file から target_scope を推定する。

    優先順位:
      1. system_artifact（run_state.json 等）→ SCOPE_SYSTEM
      2. role が所有する artifact → SCOPE_OWN_PHASE
      3. それ以外 → SCOPE_FOREIGN_PHASE
    """
    if target_file in _SYSTEM_ARTIFACTS:
        return SCOPE_SYSTEM
    owned = _ROLE_OWNED_ARTIFACTS.get(role, frozenset())
    if target_file in owned:
        return SCOPE_OWN_PHASE
    return SCOPE_FOREIGN_PHASE


# ── evaluator ────────────────────────────────────────────────────────────────

class PermissionEvaluator:
    """
    PermissionRequest を受け取り PermissionDecision を返す最小 evaluator。

    使用例:
        scope = infer_target_scope("Builder", "build.md")
        req = PermissionRequest(operation_type=OP_WRITE, target_scope=scope, role="Builder")
        decision = PermissionEvaluator().evaluate(req)
        if not decision.allowed:
            raise PermissionDenied(decision.reason)
    """

    def evaluate(self, request: PermissionRequest) -> PermissionDecision:
        """
        static matrix を引いて PermissionDecision を返す。

        approval_mode ごとの判定:
          auto            → 常に allowed
          requires_reason → force=True かつ force_reason が非空のとき allowed、それ以外は denied
          blocked         → force の有無に関わらず denied
        """
        approval_mode = _MATRIX.get(
            (request.operation_type, request.target_scope),
            MODE_REQUIRES_REASON,  # unknown (operation, scope) はデフォルト requires_reason
        )

        if approval_mode == MODE_AUTO:
            return PermissionDecision(
                allowed=True,
                approval_mode=MODE_AUTO,
                reason="",
            )

        if approval_mode == MODE_REQUIRES_REASON:
            if request.force and request.force_reason:
                return PermissionDecision(
                    allowed=True,
                    approval_mode=MODE_REQUIRES_REASON,
                    reason=f"override accepted with reason: {request.force_reason}",
                )
            return PermissionDecision(
                allowed=False,
                approval_mode=MODE_REQUIRES_REASON,
                reason=(
                    f"writing {request.target_scope} requires --force --force-reason. "
                    f"Role '{request.role}' does not own this artifact."
                ),
            )

        # blocked
        return PermissionDecision(
            allowed=False,
            approval_mode=MODE_BLOCKED,
            reason=(
                f"system artifact cannot be written directly by agent. "
                f"Target scope: {request.target_scope}."
            ),
        )
