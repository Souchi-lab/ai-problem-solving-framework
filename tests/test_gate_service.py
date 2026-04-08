"""
test_gate_service.py — GateResult / GateService のテスト

テスト方針:
- GateResult の to_dict / from_dict round-trip
- GateResult: 欠損フィールドはデフォルト値
- completeness: manifest entry ファイルが存在 → passed
- completeness: manifest entry ファイルが不在 → failed
- schema_valid: valid run_state → passed
- schema_valid: corrupt JSON → failed
- schema_valid: handoff status が不正 → failed
- consistency: plan_needed なのに plan.md が manifest にある → failed
- consistency: phase と manifest が一致 → passed
- human_approved: handoff が OFFERED かつ to_role 一致 → failed
- human_approved: handoff が ACCEPTED → passed
- RunState の gate_failures フィールド round-trip
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from apsf.core.domain.enums import GateType, HandoffStatus
from apsf.core.gates.gate_result import GateResult
from apsf.core.gates.gate_service import GateService


# ── GateResult round-trip ────────────────────────────────────────────────────

def test_gate_result_to_dict_round_trip() -> None:
    """to_dict / from_dict の round-trip が一致する。"""
    result = GateResult(
        gate_type=GateType.COMPLETENESS.value,
        passed=False,
        subject="plan.md",
        reason="plan.md is in manifest but not found on disk",
    )
    restored = GateResult.from_dict(result.to_dict())
    assert restored.gate_type == GateType.COMPLETENESS.value
    assert restored.passed is False
    assert restored.subject == "plan.md"
    assert restored.reason == "plan.md is in manifest but not found on disk"


def test_gate_result_from_dict_missing_fields_use_defaults() -> None:
    """欠損フィールドはデフォルト値で補完される（前方互換）。"""
    minimal = {"gate_type": "schema_valid", "passed": True}
    result = GateResult.from_dict(minimal)
    assert result.gate_type == "schema_valid"
    assert result.passed is True
    assert result.subject == ""
    assert result.reason == ""


# ── completeness ─────────────────────────────────────────────────────────────

def _make_manifest(run_dir: Path, artifact_names: list[str]) -> None:
    """指定 artifact を entries に持つ artifact_manifest.json を生成する。"""
    entries = {
        name: {
            "artifact_name": name,
            "artifact_type": "markdown",
            "owner_role": "",
            "written_by": "",
            "status": "generated",
            "checksum": "",
            "updated_at": "",
            "finalized_at": "",
            "finalized_by": "",
            "revision": 1,
            "source_handoff_id": "",
        }
        for name in artifact_names
    }
    data = {"run_id": "test-run", "entries": entries}
    (run_dir / "artifact_manifest.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def test_completeness_passes_when_all_artifacts_exist(tmp_path: Path) -> None:
    """manifest の全 entry ファイルが存在する場合 → passed。"""
    _make_manifest(tmp_path, ["plan.md"])
    (tmp_path / "plan.md").write_text("# Plan\n\nContent.", encoding="utf-8")

    from apsf.core.manifest.manifest_repository import ManifestRepository
    manifest = ManifestRepository(tmp_path).load()

    results = GateService().evaluate_completeness(tmp_path, manifest)
    assert all(r.passed for r in results)


def test_completeness_fails_when_artifact_missing(tmp_path: Path) -> None:
    """manifest にある artifact ファイルが disk 上に存在しない場合 → failed。"""
    _make_manifest(tmp_path, ["plan.md"])
    # plan.md を作らない

    from apsf.core.manifest.manifest_repository import ManifestRepository
    manifest = ManifestRepository(tmp_path).load()

    results = GateService().evaluate_completeness(tmp_path, manifest)
    failed = [r for r in results if not r.passed]
    assert len(failed) == 1
    assert failed[0].subject == "plan.md"
    assert "not found on disk" in failed[0].reason


# ── schema_valid ─────────────────────────────────────────────────────────────

def _make_run_state(run_dir: Path, current_phase: str = "PLAN_NEEDED") -> None:
    state = {
        "run_id": "test-run",
        "current_phase": current_phase,
        "phase_status": "pending",
        "current_owner": "Planner",
        "retry_count": 0,
        "last_error": "",
        "active_handoff_id": "",
        "gate_failures": [],
    }
    (run_dir / "run_state.json").write_text(
        json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def test_schema_valid_passes_when_run_state_ok(tmp_path: Path) -> None:
    """valid な run_state.json → passed。"""
    _make_run_state(tmp_path)
    from apsf.core.state.run_state_repository import RunStateRepository
    run_state = RunStateRepository(tmp_path).load()

    results = GateService().evaluate_schema_valid(tmp_path, run_state, None, None)
    assert all(r.passed for r in results)


def test_schema_valid_fails_when_run_state_corrupt(tmp_path: Path) -> None:
    """corrupt な run_state.json → failed。"""
    (tmp_path / "run_state.json").write_text("NOT JSON {{", encoding="utf-8")
    from apsf.core.state.run_state_repository import RunStateRepository
    run_state = RunStateRepository(tmp_path).load()  # → None

    results = GateService().evaluate_schema_valid(tmp_path, run_state, None, None)
    failed = [r for r in results if not r.passed]
    assert len(failed) == 1
    assert failed[0].subject == "run_state"
    assert "could not be parsed" in failed[0].reason


def test_schema_valid_fails_when_handoff_status_invalid(tmp_path: Path) -> None:
    """handoff.status が不正値 → failed。"""
    handoff_data = {
        "handoff_id": "abc",
        "from_role": "Planner",
        "to_role": "Builder",
        "artifact_scope": [],
        "status": "UNKNOWN_STATUS",
        "accepted_by_next_role": "",
        "supersedes": "",
        "created_at": "",
        "accepted_at": "",
        "proceed_without_handoff_reason": "",
    }
    (tmp_path / "handoff.json").write_text(
        json.dumps(handoff_data, ensure_ascii=False), encoding="utf-8"
    )
    from apsf.core.handoff.handoff_repository import HandoffRepository
    handoff = HandoffRepository(tmp_path).load()

    results = GateService().evaluate_schema_valid(tmp_path, None, None, handoff)
    failed = [r for r in results if not r.passed]
    assert len(failed) == 1
    assert failed[0].subject == "handoff"
    assert "not a valid HandoffStatus" in failed[0].reason


# ── consistency ──────────────────────────────────────────────────────────────

def _make_run_state_obj(current_phase: str):
    from apsf.core.state.run_state import RunState, PhaseStatus
    return RunState(
        run_id="test-run",
        current_phase=current_phase,
        phase_status=PhaseStatus.PENDING.value,
        current_owner="Planner",
        retry_count=0,
        last_error="",
        active_handoff_id="",
        gate_failures=[],
    )


def test_consistency_fails_when_plan_in_manifest_but_plan_needed(tmp_path: Path) -> None:
    """PLAN_NEEDED なのに manifest に plan.md が記録されている → inconsistent。"""
    _make_manifest(tmp_path, ["plan.md"])
    (tmp_path / "plan.md").write_text("# Plan", encoding="utf-8")

    from apsf.core.manifest.manifest_repository import ManifestRepository
    run_state = _make_run_state_obj("PLAN_NEEDED")
    manifest = ManifestRepository(tmp_path).load()

    results = GateService().evaluate_consistency(run_state, manifest)
    failed = [r for r in results if not r.passed]
    assert len(failed) == 1
    assert failed[0].subject == "plan.md"
    assert "PLAN_NEEDED" in failed[0].reason


def test_consistency_passes_when_phase_aligns_with_manifest(tmp_path: Path) -> None:
    """BUILD_NEEDED で manifest に plan.md のみ → consistent（build.md はまだない）。"""
    _make_manifest(tmp_path, ["plan.md"])
    (tmp_path / "plan.md").write_text("# Plan", encoding="utf-8")

    from apsf.core.manifest.manifest_repository import ManifestRepository
    run_state = _make_run_state_obj("BUILD_NEEDED")
    manifest = ManifestRepository(tmp_path).load()

    results = GateService().evaluate_consistency(run_state, manifest)
    assert all(r.passed for r in results)


# ── human_approved ───────────────────────────────────────────────────────────

def test_human_approved_fails_when_handoff_offered_and_role_matches(tmp_path: Path) -> None:
    """handoff が OFFERED かつ to_role == current_owner → acceptance 未済を検出。"""
    from apsf.core.handoff.handoff_record import HandoffRecord
    run_state = _make_run_state_obj("BUILD_NEEDED")
    run_state.current_owner = "Builder"
    handoff = HandoffRecord(
        from_role="Planner",
        to_role="Builder",
        status=HandoffStatus.OFFERED.value,
    )

    results = GateService().evaluate_human_approved(run_state, handoff)
    failed = [r for r in results if not r.passed]
    assert len(failed) == 1
    assert "OFFERED" in failed[0].reason
    assert "Builder" in failed[0].reason


def test_human_approved_passes_when_handoff_accepted(tmp_path: Path) -> None:
    """handoff が ACCEPTED → passed。"""
    from apsf.core.handoff.handoff_record import HandoffRecord
    run_state = _make_run_state_obj("BUILD_NEEDED")
    run_state.current_owner = "Builder"
    handoff = HandoffRecord(
        from_role="Planner",
        to_role="Builder",
        status=HandoffStatus.ACCEPTED.value,
        accepted_by_next_role="Builder",
    )

    results = GateService().evaluate_human_approved(run_state, handoff)
    assert all(r.passed for r in results)


# ── RunState gate_failures field ─────────────────────────────────────────────

def test_run_state_gate_failures_field_round_trip(tmp_path: Path) -> None:
    """gate_failures フィールドが to_dict / from_dict で正しく round-trip する。"""
    from apsf.core.state.run_state import RunState, PhaseStatus
    from apsf.core.state.run_state_repository import RunStateRepository

    state = RunState(
        run_id="test-run",
        current_phase="BUILD_NEEDED",
        phase_status=PhaseStatus.PENDING.value,
        current_owner="Builder",
        retry_count=0,
        last_error="",
        active_handoff_id="",
        gate_failures=["plan.md is in manifest but not found on disk"],
    )
    repo = RunStateRepository(tmp_path)
    repo.save(state)

    loaded = repo.load()
    assert loaded is not None
    assert loaded.gate_failures == ["plan.md is in manifest but not found on disk"]


def test_run_state_from_dict_missing_gate_failures_uses_empty_list() -> None:
    """前方互換: gate_failures フィールドが欠損していても [] で補完される。"""
    from apsf.core.state.run_state import RunState
    data = {
        "run_id": "test-run",
        "current_phase": "PLAN_NEEDED",
        "phase_status": "pending",
        "current_owner": "Planner",
        "retry_count": 0,
        "last_error": "",
        "active_handoff_id": "",
        # gate_failures は意図的に欠落
    }
    state = RunState.from_dict(data)
    assert state.gate_failures == []
