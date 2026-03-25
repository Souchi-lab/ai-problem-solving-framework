"""
Role boundary rules — APSF runtime enforcement.

Single source of truth for which roles may write which artifacts at runtime.
Referenced by apsf write-phase (hard-stop) and apsf act (preflight warning).

Design doc: framework/responsibility-matrix.md
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


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


# ---------------------------------------------------------------------------
# Forbidden artifacts per role
#
# Source: framework/responsibility-matrix.md — Role Matrix "Must Not Create"
# Initial scope: review.md / improve.md / result.md (run-021 failure pattern).
# ---------------------------------------------------------------------------
ROLE_FORBIDDEN: dict[str, list[tuple[str, GuardSeverity]]] = {
    "Builder": [
        ("review.md",  GuardSeverity.HARD_STOP),
        ("improve.md", GuardSeverity.HARD_STOP),
        ("result.md",  GuardSeverity.HARD_STOP),
    ],
    "Planner": [
        ("build.md",   GuardSeverity.HARD_STOP),
        ("review.md",  GuardSeverity.HARD_STOP),
        ("improve.md", GuardSeverity.HARD_STOP),
        ("result.md",  GuardSeverity.HARD_STOP),
    ],
    "Critic": [
        ("improve.md", GuardSeverity.HARD_STOP),
        ("result.md",  GuardSeverity.HARD_STOP),
    ],
}

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
) -> Optional[RoleBoundaryViolation]:
    """
    Check whether role is allowed to write target_file.

    Returns:
        None                              — allowed (no violation)
        RoleBoundaryViolation (HARD_STOP) — blocked; caller must exit unless force=True
        RoleBoundaryViolation (WARNING)   — allowed but flagged (force=True downgrade)

    When force=True:
        HARD_STOP is downgraded to WARNING.
        Caller should log the override for auditability.
    """
    for fname, severity in ROLE_FORBIDDEN.get(role, []):
        if fname == target_file:
            effective = GuardSeverity.WARNING if force else severity
            hint = (
                "  Override active (--force). Log the reason for this override."
                if force
                else "  To override (human judgment only): add --force and record your reason."
            )
            return RoleBoundaryViolation(
                role=role,
                target_file=target_file,
                severity=effective,
                message=(
                    f"[Role-Boundary] {role} must not write {target_file}. "
                    f"See framework/responsibility-matrix.md for canonical writers."
                ),
                override_hint=hint,
            )
    return None
