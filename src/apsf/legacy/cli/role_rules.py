"""
Role boundary rules — APSF runtime enforcement adapter.

ownership policy の canonical 定義は core/domain/ownership.py にある。
このモジュールはその policy を読んで runtime enforcement を行う adapter 層。

以前の ROLE_FORBIDDEN ハードコード�� ownership.py の ARTIFACT_OWNERSHIP_DEFAULTS から
導出する形に変更した。二重正本を防ぐため、ここでは policy の再定義をしない。

Design doc: framework/responsibility-matrix.md
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional

from ...core.domain.ownership import is_allowed_writer, get_policy


class GuardSeverity(str, Enum):
    WARNING   = "WARNING"
    HARD_STOP = "HARD_STOP"


@dataclass
class RoleBoundaryViolation:
    role:          str
    target_file:   str
    severity:      GuardSeverity
    message:       str
    override_hint: str = ""


# Phase value → canonical role name.
# Mirrors phase_detector.AUTO_OWNED_PHASES / act_service._PHASE_TO_ROLE.
PHASE_TO_ROLE: dict[str, str] = {
    "PLAN_NEEDED":   "Planner",
    "BUILD_NEEDED":  "Builder",
    "REVIEW_NEEDED": "Critic",
}


def role_from_phase(phase_value: str) -> Optional[str]:
    """Return canonical role name for an auto-owned phase, or None for human phases."""
    return PHASE_TO_ROLE.get(phase_value)


def check_role_boundary(
    role: str,
    target_file: str,
    *,
    force: bool = False,
    override_reason: Optional[str] = None,
) -> Optional[RoleBoundaryViolation]:
    """
    Check whether role is allowed to write target_file.

    ownership policy (core/domain/ownership.py) を参照して判定する。
    policy 未定義の artifact はチェックしない（寛容）。

    Returns:
        None                              — allowed (no violation)
        RoleBoundaryViolation (HARD_STOP) — blocked
        RoleBoundaryViolation (WARNING)   — allowed but flagged

    force=True の semantics:
        override_reason がある場合のみ HARD_STOP を WARNING に降格する。
        override_reason が空の場合は override 自体を HARD_STOP とし、
        理由未記録の override を通常フローで通さない。
    """
    if is_allowed_writer(role, target_file):
        return None

    policy = get_policy(target_file)
    owner = policy.owner_role if policy else "unknown"

    if force:
        if override_reason:
            hint = f"  Override active (--force). Reason: {override_reason}"
            msg = (
                f"[Role-Boundary] {role} is not in allowed_writers for {target_file} "
                f"(owner: {owner}). Override applied with reason: {override_reason}"
            )
            severity = GuardSeverity.WARNING
        else:
            hint = (
                "  Override blocked. Add --force-reason <reason> "
                "to record the override rationale."
            )
            msg = (
                f"[Role-Boundary] {role} is not in allowed_writers for {target_file} "
                f"(owner: {owner}). --force-reason is required for override."
            )
            severity = GuardSeverity.HARD_STOP
        return RoleBoundaryViolation(
            role=role,
            target_file=target_file,
            severity=severity,
            message=msg,
            override_hint=hint,
        )

    return RoleBoundaryViolation(
        role=role,
        target_file=target_file,
        severity=GuardSeverity.HARD_STOP,
        message=(
            f"[Role-Boundary] {role} must not write {target_file} "
            f"(owner: {owner}, allowed: {policy.allowed_writers if policy else 'undefined'}). "
            "See framework/responsibility-matrix.md for canonical writers."
        ),
        override_hint=(
            "  To override (human judgment only): add --force and --force-reason <reason>."
        ),
    )
