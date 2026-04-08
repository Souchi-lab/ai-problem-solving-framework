"""
test_run_state_repository.py — RunState / RunStateRepository の単体テスト

テスト方針:
- RunState の to_dict / from_dict round-trip
- RunStateRepository の load/save / exists
- run_state.json が存在しない場合は None を返す
- 全フィールドが JSON に含まれる
- bootstrap: run_state.json がない run に ActService を呼ぶと生成される
- retry 記録: LLM 失敗時に retry_count が +1 され last_error が記録される
- phase_status in_progress: LLM 実行前に in_progress が保存される
"""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from apsf.core.storage.force_audit_repository import ForceAuditRepository
from apsf.core.state.run_state import PhaseStatus, RunState
from apsf.core.state.run_state_repository import RunStateRepository


# ── RunState round-trip ──────────────────────────────────────────────────────

def test_run_state_to_dict_contains_all_fields() -> None:
    state = RunState(
        run_id="2026-03-31-038_fw-improvement_test",
        current_phase="PLAN_NEEDED",
        phase_status=PhaseStatus.PENDING.value,
        current_owner="Planner",
        retry_count=0,
        last_error="",
        active_handoff_id="",
    )
    d = state.to_dict()
    assert "run_id" in d
    assert "current_phase" in d
    assert "phase_status" in d
    assert "current_owner" in d
    assert "retry_count" in d
    assert "last_error" in d
    assert "active_handoff_id" in d


def test_run_state_from_dict_round_trip() -> None:
    state = RunState(
        run_id="test-run",
        current_phase="BUILD_NEEDED",
        phase_status=PhaseStatus.COMPLETED.value,
        current_owner="Builder",
        retry_count=2,
        last_error="some error",
        active_handoff_id="hf-001",
    )
    restored = RunState.from_dict(state.to_dict())
    assert restored.run_id == state.run_id
    assert restored.current_phase == state.current_phase
    assert restored.phase_status == state.phase_status
    assert restored.current_owner == state.current_owner
    assert restored.retry_count == state.retry_count
    assert restored.last_error == state.last_error
    assert restored.active_handoff_id == state.active_handoff_id


def test_run_state_from_dict_unknown_fields_ignored() -> None:
    """from_dict は未知のフィールドを無視する（前方互換）。"""
    data = {
        "run_id": "x",
        "current_phase": "REVIEW_NEEDED",
        "phase_status": "pending",
        "current_owner": "Critic",
        "retry_count": 0,
        "last_error": "",
        "active_handoff_id": "",
        "future_field": "ignored",
    }
    state = RunState.from_dict(data)
    assert state.current_phase == "REVIEW_NEEDED"


def test_run_state_from_dict_missing_fields_use_defaults() -> None:
    """from_dict はフィールドが欠けている場合にデフォルト値を使う。"""
    state = RunState.from_dict({"run_id": "minimal"})
    assert state.retry_count == 0
    assert state.last_error == ""
    assert state.phase_status == PhaseStatus.PENDING.value


# ── RunStateRepository ────────────────────────────────────────────────────────

def test_run_state_repository_exists_false_when_no_file(tmp_path: Path) -> None:
    repo = RunStateRepository(tmp_path)
    assert repo.exists() is False


def test_run_state_repository_load_missing_returns_none(tmp_path: Path) -> None:
    repo = RunStateRepository(tmp_path)
    assert repo.load() is None


def test_run_state_repository_save_and_load(tmp_path: Path) -> None:
    repo = RunStateRepository(tmp_path)
    state = RunState(
        run_id="test-save-load",
        current_phase="PLAN_NEEDED",
        phase_status=PhaseStatus.PENDING.value,
        current_owner="Planner",
        retry_count=0,
        last_error="",
        active_handoff_id="",
    )
    repo.save(state)
    assert repo.exists() is True
    loaded = repo.load()
    assert loaded is not None
    assert loaded.run_id == "test-save-load"
    assert loaded.current_phase == "PLAN_NEEDED"
    assert loaded.current_owner == "Planner"


def test_run_state_repository_json_is_readable(tmp_path: Path) -> None:
    """保存されたファイルは有効な JSON であること。"""
    repo = RunStateRepository(tmp_path)
    state = RunState(
        run_id="json-check",
        current_phase="BUILD_NEEDED",
        phase_status=PhaseStatus.IN_PROGRESS.value,
        current_owner="Builder",
        retry_count=1,
        last_error="timeout",
        active_handoff_id="",
    )
    repo.save(state)
    raw = (tmp_path / RunStateRepository.STATE_FILENAME).read_text(encoding="utf-8")
    parsed = json.loads(raw)
    assert parsed["current_phase"] == "BUILD_NEEDED"
    assert parsed["retry_count"] == 1


def test_run_state_repository_load_invalid_json_returns_none(tmp_path: Path) -> None:
    """壊れた JSON は None を返す（例外を raise しない）。"""
    bad_file = tmp_path / RunStateRepository.STATE_FILENAME
    bad_file.write_text("not json {{{", encoding="utf-8")
    repo = RunStateRepository(tmp_path)
    assert repo.load() is None


# ── ActService integration ────────────────────────────────────────────────────

def _make_run_dir(tmp_path: Path) -> Path:
    """goal.md + execution-assignment.md が記入済みの run dir を作成（→ PLAN_NEEDED になる）。"""
    run_dir = tmp_path / "test-run"
    run_dir.mkdir()
    # _is_filled は meaningful lines > 3 が必要（4行以上）
    (run_dir / "execution-assignment.md").write_text(
        "# Execution Assignment\n\n"
        "- Executor: Claude\n"
        "- Mode: auto\n"
        "- Provider: Anthropic\n"
        "- Notes: test run for unit tests\n",
        encoding="utf-8",
    )
    (run_dir / "goal.md").write_text(
        "# Goal\n\n"
        "## Goal Statement\nTest goal for unit tests.\n\n"
        "## Background\nThis is a background sentence.\n\n"
        "## Success Criteria\n"
        "- Criteria A is met\n"
        "- Criteria B is met\n",
        encoding="utf-8",
    )
    return run_dir


def test_bootstrap_creates_run_state_on_first_act(tmp_path: Path) -> None:
    """run_state.json がない run に ActService を呼ぶと run_state.json が生成される。"""
    from apsf.legacy.orchestration.act_service import ActService
    from apsf.legacy.config.settings import Settings

    run_dir = _make_run_dir(tmp_path)

    settings = Settings(anthropic_api_key="sk-test", framework_root=Path("."))

    mock_response = MagicMock()
    mock_response.content = "# Plan\n\nTest plan content here.\nLine 2.\nLine 3.\nLine 4.\n"

    with patch("apsf.legacy.orchestration.act_service.ActService._get_provider") as mock_get_provider:
        mock_provider = MagicMock()
        mock_provider.generate.return_value = mock_response
        mock_get_provider.return_value = mock_provider

        service = ActService()
        result = service.execute(run_dir, "test-run", settings=settings)

    assert result.generated is True
    state_path = run_dir / RunStateRepository.STATE_FILENAME
    assert state_path.exists(), "run_state.json should be created after first act"


def test_run_state_retry_recording(tmp_path: Path) -> None:
    """LLM 失敗時に retry_count が +1 され last_error が記録される。"""
    from apsf.core.providers.base import ProviderError
    from apsf.legacy.orchestration.act_service import ActError, ActService
    from apsf.legacy.config.settings import Settings

    run_dir = _make_run_dir(tmp_path)

    settings = Settings(anthropic_api_key="sk-test", framework_root=Path("."))

    with patch("apsf.legacy.orchestration.act_service.ActService._get_provider") as mock_get_provider:
        mock_provider = MagicMock()
        mock_provider.generate.side_effect = ProviderError("API timeout")
        mock_get_provider.return_value = mock_provider

        service = ActService()
        with pytest.raises(ActError, match="LLM generation failed"):
            service.execute(run_dir, "test-run", settings=settings)

    repo = RunStateRepository(run_dir)
    state = repo.load()
    assert state is not None
    assert state.retry_count == 1
    assert "API timeout" in state.last_error
    assert state.phase_status == PhaseStatus.FAILED.value


def test_phase_status_in_progress_before_llm(tmp_path: Path) -> None:
    """LLM 呼び出し前に phase_status = in_progress が保存される。"""
    from apsf.core.providers.base import ProviderError
    from apsf.legacy.orchestration.act_service import ActError, ActService
    from apsf.legacy.config.settings import Settings

    run_dir = _make_run_dir(tmp_path)
    settings = Settings(anthropic_api_key="sk-test", framework_root=Path("."))

    captured_status: list[str] = []

    original_generate = None

    def capturing_generate(request):
        # generate が呼ばれた時点で run_state の phase_status を記録する
        repo = RunStateRepository(run_dir)
        state = repo.load()
        if state:
            captured_status.append(state.phase_status)
        raise ProviderError("stop here")

    with patch("apsf.legacy.orchestration.act_service.ActService._get_provider") as mock_get_provider:
        mock_provider = MagicMock()
        mock_provider.generate.side_effect = capturing_generate
        mock_get_provider.return_value = mock_provider

        from apsf.legacy.orchestration.act_service import ActError
        service = ActService()
        with pytest.raises(ActError):
            service.execute(run_dir, "test-run", settings=settings)

    assert PhaseStatus.IN_PROGRESS.value in captured_status, (
        "phase_status should be in_progress before LLM call"
    )


def test_act_full_loop_artifact_state_gate(tmp_path: Path) -> None:
    """
    ActService.execute() 成功系の full loop 統合テスト。

    1 回の execute() で以下が同時に成立することを確認する:
    - artifact (plan.md) が保存される
    - run_state が次 phase（BUILD_NEEDED）へ前進し phase_status = pending にリセットされる
    - gate 評価が実行され gate_results が返る
    - artifact_manifest.json が更新される
    """
    from apsf.legacy.orchestration.act_service import ActService
    from apsf.legacy.config.settings import Settings
    from apsf.core.state.run_state_repository import RunStateRepository

    run_dir = _make_run_dir(tmp_path)
    settings = Settings(anthropic_api_key="sk-test", framework_root=Path("."))

    mock_response = MagicMock()
    mock_response.content = (
        "# Plan\n\n"
        "## Goal Readiness Check\nAll checks passed.\n\n"
        "## Problem Structure\nMain problem identified.\n\n"
        "## Selected Approach\nOption A selected.\n\n"
        "## Execution Plan\n- Step 1: implement\n- Step 2: test\n"
    )

    with patch("apsf.legacy.orchestration.act_service.ActService._get_provider") as mock_get_provider:
        mock_provider = MagicMock()
        mock_provider.generate.return_value = mock_response
        mock_get_provider.return_value = mock_provider

        service = ActService()
        result = service.execute(run_dir, "test-run", settings=settings)

    # artifact 保存
    assert result.generated is True
    assert (run_dir / "plan.md").exists(), "plan.md should be saved"
    assert (run_dir / "plan.md").stat().st_size > 0

    # run_state phase 前進
    state = RunStateRepository(run_dir).load()
    assert state is not None
    assert state.current_phase == "BUILD_NEEDED", (
        f"phase should advance to BUILD_NEEDED, got {state.current_phase}"
    )
    assert state.phase_status == PhaseStatus.PENDING.value, (
        "phase_status should be reset to pending after phase advance"
    )
    assert state.retry_count == 0, "retry_count should be reset after success"
    assert state.last_error == "", "last_error should be cleared after success"

    # gate 評価が実行されている
    assert result.gate_results is not None
    assert isinstance(result.gate_results, list), "gate_results should be a list"
    # gate 評価が走っていれば少なくとも 1 件以上の result が返る
    assert len(result.gate_results) > 0, "gate_results should contain at least one evaluation"

    # artifact_manifest が更新されている
    manifest_path = run_dir / "artifact_manifest.json"
    assert manifest_path.exists(), "artifact_manifest.json should be updated after write"


def test_act_force_creates_force_audit_entry(tmp_path: Path) -> None:
    """ActService.execute(force=True) で consistency bypass の audit が保存される。"""
    from apsf.legacy.orchestration.act_service import ActService
    from apsf.legacy.config.settings import Settings

    run_dir = _make_run_dir(tmp_path)
    settings = Settings(anthropic_api_key="sk-test", framework_root=Path("."))

    mock_response = MagicMock()
    mock_response.content = "# Plan\n\nTest plan content here.\nLine 2.\nLine 3.\nLine 4.\n"

    with patch("apsf.legacy.orchestration.act_service.ActService._get_provider") as mock_get_provider:
        mock_provider = MagicMock()
        mock_provider.generate.return_value = mock_response
        mock_get_provider.return_value = mock_provider

        service = ActService()
        result = service.execute(
            run_dir,
            "test-run",
            force=True,
            force_reason="intentional bypass",
            settings=settings,
        )

    assert result.generated is True
    entries = ForceAuditRepository(run_dir).load()
    assert len(entries) == 1
    assert entries[0].command == "act"
    assert entries[0].target_file == "plan.md"
    assert entries[0].override_kind == "consistency_gate_bypass"
    assert entries[0].had_reason is True
    assert entries[0].reason == "intentional bypass"
