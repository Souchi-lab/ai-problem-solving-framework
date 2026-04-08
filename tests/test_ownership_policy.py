"""
ownership policy / enum / role boundary のテスト

- enums が import できること
- ARTIFACT_OWNERSHIP_DEFAULTS に主要 artifact が含まれること
- check_role_boundary の cross-role / allowed / force 挙動
- ArtifactRepository の ownership 違反 / no-role スキップ
"""

from __future__ import annotations

from pathlib import Path

import pytest

from apsf.core.domain.enums import ArtifactStatus, GateType, HandoffStatus, RunStatus
from apsf.core.domain.ownership import (
    ARTIFACT_OWNERSHIP_DEFAULTS,
    ArtifactOwnershipPolicy,
    get_policy,
    is_allowed_writer,
)
from apsf.core.storage.artifact_repository import (
    ArtifactRepository,
    OwnershipViolationError,
)
from apsf.legacy.cli.role_rules import GuardSeverity, check_role_boundary


# ── enums ────────────────────────────────────────────────────────────────────

def test_run_status_values() -> None:
    assert RunStatus.NOT_STARTED == "not_started"
    assert RunStatus.BLOCKED == "blocked"
    assert RunStatus.COMPLETED == "completed"


def test_artifact_status_values() -> None:
    assert ArtifactStatus.DRAFT == "draft"
    assert ArtifactStatus.FINAL == "final"
    assert ArtifactStatus.INVALID == "invalid"


def test_handoff_status_values() -> None:
    assert HandoffStatus.OFFERED == "offered"
    assert HandoffStatus.ACCEPTED == "accepted"
    assert HandoffStatus.SUPERSEDED == "superseded"


def test_gate_type_values() -> None:
    assert GateType.COMPLETENESS == "completeness"
    assert GateType.HUMAN_APPROVED == "human_approved"


# ── ArtifactOwnershipPolicy ──────────────────────────────────────────────────

def test_artifact_ownership_defaults_coverage() -> None:
    """主要 artifact が ARTIFACT_OWNERSHIP_DEFAULTS に含まれていること。"""
    required = {"plan.md", "build.md", "review.md", "handoff.md", "result.md", "improve.md"}
    assert required.issubset(set(ARTIFACT_OWNERSHIP_DEFAULTS.keys()))


def test_ownership_policy_is_frozen() -> None:
    """ArtifactOwnershipPolicy は frozen dataclass で不変であること。"""
    policy = get_policy("plan.md")
    assert policy is not None
    with pytest.raises((AttributeError, TypeError)):
        policy.owner_role = "hacked"  # type: ignore[misc]


def test_is_allowed_writer_allowed() -> None:
    assert is_allowed_writer("Builder", "build.md") is True


def test_is_allowed_writer_not_allowed() -> None:
    assert is_allowed_writer("Builder", "review.md") is False


def test_is_allowed_writer_unknown_artifact() -> None:
    """policy 未定義の artifact は全 role に許可（寛容）。"""
    assert is_allowed_writer("Builder", "unknown_artifact.md") is True


# ── check_role_boundary ───────────────────────────────────────────────────────

def test_check_role_boundary_allowed_returns_none() -> None:
    """Builder が build.md を書く → None（通過）。"""
    assert check_role_boundary("Builder", "build.md") is None


def test_check_role_boundary_cross_role_hard_stop() -> None:
    """Builder が review.md を書こうとする → HARD_STOP。"""
    violation = check_role_boundary("Builder", "review.md")
    assert violation is not None
    assert violation.severity == GuardSeverity.HARD_STOP
    assert "Builder" in violation.message
    assert "review.md" in violation.message


def test_check_role_boundary_force_without_reason_hard_stops() -> None:
    """force=True + reason なし → HARD_STOP（run-049 strict policy）。"""
    violation = check_role_boundary("Builder", "review.md", force=True)
    assert violation is not None
    assert violation.severity == GuardSeverity.HARD_STOP
    assert "--force-reason" in violation.message or "--force-reason" in violation.override_hint


def test_check_role_boundary_force_with_reason_warns_with_reason() -> None:
    """force=True + reason あり → WARNING かつ reason が message に含まれる。"""
    reason = "hotfix approved by lead"
    violation = check_role_boundary("Builder", "review.md", force=True, override_reason=reason)
    assert violation is not None
    assert violation.severity == GuardSeverity.WARNING
    assert reason in violation.message


def test_check_role_boundary_planner_cannot_write_build() -> None:
    """Planner が build.md を書こうとする → HARD_STOP。"""
    violation = check_role_boundary("Planner", "build.md")
    assert violation is not None
    assert violation.severity == GuardSeverity.HARD_STOP


def test_check_role_boundary_unknown_artifact_allowed() -> None:
    """policy 未定義の artifact は通過（寛容）。"""
    assert check_role_boundary("Builder", "unknown.md") is None


# ── ArtifactRepository ownership integration ─────────────────────────────────

def test_artifact_repo_ownership_violation_raises(tmp_path: Path) -> None:
    """Builder が review.md に書こうとすると OwnershipViolationError。"""
    repo = ArtifactRepository(writing_role="Builder")
    target = tmp_path / "review.md"

    with pytest.raises(OwnershipViolationError) as exc_info:
        repo.write(target, "# Review\n")

    assert "Builder" in str(exc_info.value)
    assert "review.md" in str(exc_info.value)
    assert not target.exists(), "OwnershipViolationError 後はファイルが作成されていない"


def test_artifact_repo_allowed_write_succeeds(tmp_path: Path) -> None:
    """Builder が build.md に書く → 成功。"""
    repo = ArtifactRepository(writing_role="Builder")
    target = tmp_path / "build.md"
    repo.write(target, "# Build\n")
    assert target.read_text(encoding="utf-8") == "# Build\n"


def test_artifact_repo_no_role_skips_ownership_check(tmp_path: Path) -> None:
    """writing_role なし → ownership check スキップ（後方互換）。"""
    repo = ArtifactRepository()
    target = tmp_path / "review.md"
    repo.write(target, "# Review\n")
    assert target.exists()


def test_artifact_repo_unknown_artifact_allowed(tmp_path: Path) -> None:
    """policy 未定義の artifact は role 付きでも通過（寛容）。"""
    repo = ArtifactRepository(writing_role="Builder")
    target = tmp_path / "custom_artifact.md"
    repo.write(target, "# Custom\n")
    assert target.exists()
