"""
tests/test_gate_hard_block.py

consistency gate の PRE-write hard block 化を検証する。

- manifest なし → pre-write consistency passes
- manifest あり・該当 artifact なし → passes（初回書き込みは通る）
- manifest に該当 artifact がある → FAIL（phase 逆戻り検出）
- post-write advisory に consistency が含まれないこと（HARD_BLOCK_GATE_TYPES に一致するため除外）
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from apsf.core.domain.enums import GateType
from apsf.core.gates.gate_service import GateService, HARD_BLOCK_GATE_TYPES


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _make_manifest(run_dir: Path, artifact_names: list[str]) -> None:
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


# ---------------------------------------------------------------------------
# HARD_BLOCK_GATE_TYPES 定数
# ---------------------------------------------------------------------------

def test_hard_block_gate_types_contains_schema_valid_and_consistency() -> None:
    """`HARD_BLOCK_GATE_TYPES` に schema_valid と consistency が含まれる。"""
    assert GateType.SCHEMA_VALID.value in HARD_BLOCK_GATE_TYPES
    assert GateType.CONSISTENCY.value in HARD_BLOCK_GATE_TYPES


def test_hard_block_gate_types_does_not_contain_advisory_gates() -> None:
    """completeness と human_approved は advisory のまま（HARD_BLOCK_GATE_TYPES に含まれない）。"""
    assert GateType.COMPLETENESS.value not in HARD_BLOCK_GATE_TYPES
    assert GateType.HUMAN_APPROVED.value not in HARD_BLOCK_GATE_TYPES


# ---------------------------------------------------------------------------
# pre-write consistency: passes when no manifest
# ---------------------------------------------------------------------------

def test_consistency_passes_when_no_manifest(tmp_path: Path) -> None:
    """manifest なし（新規 run）→ pre-write consistency passed。"""
    run_state = _make_run_state_obj("PLAN_NEEDED")
    # ManifestRepository.load() は None を返す
    from apsf.core.manifest.manifest_repository import ManifestRepository
    manifest = ManifestRepository(tmp_path).load()  # → None

    results = GateService().evaluate_consistency(run_state, manifest)
    assert all(r.passed for r in results)


# ---------------------------------------------------------------------------
# pre-write consistency: passes when artifact not yet in manifest (initial write)
# ---------------------------------------------------------------------------

def test_consistency_passes_when_artifact_not_in_manifest(tmp_path: Path) -> None:
    """manifest があるが plan.md はまだ記録されていない → 初回書き込み → passed。"""
    _make_manifest(tmp_path, ["build.md"])  # plan.md は含まない
    (tmp_path / "build.md").write_text("# Build\n", encoding="utf-8")
    run_state = _make_run_state_obj("PLAN_NEEDED")

    from apsf.core.manifest.manifest_repository import ManifestRepository
    manifest = ManifestRepository(tmp_path).load()

    results = GateService().evaluate_consistency(run_state, manifest)
    assert all(r.passed for r in results)


# ---------------------------------------------------------------------------
# pre-write consistency: fails when artifact already in manifest (phase regression)
# ---------------------------------------------------------------------------

def test_consistency_fails_when_plan_in_manifest_at_plan_needed(tmp_path: Path) -> None:
    """plan.md がすでに manifest にある状態で PLAN_NEEDED → phase 逆戻り → FAIL。"""
    _make_manifest(tmp_path, ["plan.md"])
    (tmp_path / "plan.md").write_text("# Plan\n", encoding="utf-8")
    run_state = _make_run_state_obj("PLAN_NEEDED")

    from apsf.core.manifest.manifest_repository import ManifestRepository
    manifest = ManifestRepository(tmp_path).load()

    results = GateService().evaluate_consistency(run_state, manifest)
    failed = [r for r in results if not r.passed]
    assert len(failed) == 1
    assert failed[0].gate_type == GateType.CONSISTENCY.value
    assert "PLAN_NEEDED" in failed[0].reason
    assert "plan.md" in failed[0].reason


# ---------------------------------------------------------------------------
# post-write: consistency は advisory に含まれない
# ---------------------------------------------------------------------------

def test_consistency_is_excluded_from_post_write_advisory_filter(tmp_path: Path) -> None:
    """HARD_BLOCK_GATE_TYPES に consistency が含まれるため、post-write advisory フィルタから除外される。"""
    # post-write advisory の判定式を直接再現して検証する
    from apsf.core.gates.gate_result import GateResult

    consistency_failure = GateResult(
        gate_type=GateType.CONSISTENCY.value,
        passed=False,
        subject="plan.md",
        reason="phase regression",
    )
    completeness_failure = GateResult(
        gate_type=GateType.COMPLETENESS.value,
        passed=False,
        subject="build.md",
        reason="build.md is in manifest but not found on disk",
    )
    gate_results = [consistency_failure, completeness_failure]

    # act_service の advisory フィルタ式と同一
    advisory_failures = [
        r for r in gate_results
        if not r.passed and r.gate_type not in HARD_BLOCK_GATE_TYPES
    ]

    # consistency は HARD_BLOCK_GATE_TYPES に含まれるので除外される
    gate_types_in_advisory = {r.gate_type for r in advisory_failures}
    assert GateType.CONSISTENCY.value not in gate_types_in_advisory
    # completeness は advisory に残る
    assert GateType.COMPLETENESS.value in gate_types_in_advisory
