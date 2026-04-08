"""
test_phase_detector_advisory.py — PhaseDetector advisory API のテスト

テスト方針:
- detect_advisory() と detect() が同一結果を返す（backward compat）
- detect() は detect_advisory() の alias である
- apsf next が run_state.json の phase を優先する（canonical）
- apsf next が run_state.json なしの場合は advisory detector を使う
"""
from __future__ import annotations

from pathlib import Path

import pytest
import typer

from apsf.legacy.orchestration.phase_detector import Phase, PhaseDetector


# ── detect_advisory / detect backward compat ────────────────────────────────

def _make_minimal_run(tmp_path: Path) -> Path:
    """goal.md + execution-assignment.md が記入済みの run dir（→ PLAN_NEEDED）。"""
    run_dir = tmp_path / "test-run"
    run_dir.mkdir()
    (run_dir / "execution-assignment.md").write_text(
        "# Execution Assignment\n\n"
        "- Executor: Claude\n- Mode: auto\n- Provider: Anthropic\n- Notes: test\n",
        encoding="utf-8",
    )
    (run_dir / "goal.md").write_text(
        "# Goal\n\n## Goal Statement\nTest goal.\n\n"
        "## Background\nBackground text here.\n\n"
        "## Success Criteria\n- Criteria A\n- Criteria B\n",
        encoding="utf-8",
    )
    return run_dir


def test_detect_advisory_returns_phase_info(tmp_path: Path) -> None:
    """detect_advisory() は PhaseInfo を返す。"""
    run_dir = _make_minimal_run(tmp_path)
    detector = PhaseDetector(run_dir)
    info = detector.detect_advisory()
    assert info is not None
    assert isinstance(info.phase, Phase)


def test_detect_advisory_and_detect_same_result(tmp_path: Path) -> None:
    """detect_advisory() と detect() は同一の phase を返す（backward compat）。"""
    run_dir = _make_minimal_run(tmp_path)
    detector = PhaseDetector(run_dir)
    advisory_info = detector.detect_advisory()
    legacy_info = detector.detect()
    assert advisory_info.phase == legacy_info.phase
    assert advisory_info.file_to_write == legacy_info.file_to_write
    assert advisory_info.files_to_read == legacy_info.files_to_read


def test_detect_is_alias_for_detect_advisory(tmp_path: Path) -> None:
    """detect() が detect_advisory() を呼ぶことで同一オブジェクトを返す。"""
    run_dir = _make_minimal_run(tmp_path)
    detector = PhaseDetector(run_dir)
    # detect() 内部で detect_advisory() を呼ぶ → phase が一致
    assert detector.detect().phase == detector.detect_advisory().phase


def test_detect_advisory_plan_needed(tmp_path: Path) -> None:
    """goal.md のみ記入済みなら PLAN_NEEDED を返す。"""
    run_dir = _make_minimal_run(tmp_path)
    detector = PhaseDetector(run_dir)
    info = detector.detect_advisory()
    assert info.phase == Phase.PLAN_NEEDED


def test_detect_advisory_build_needed(tmp_path: Path) -> None:
    """plan.md まで記入済みなら BUILD_NEEDED を返す。"""
    run_dir = _make_minimal_run(tmp_path)
    (run_dir / "plan.md").write_text(
        "# Plan\n\nLine 1.\nLine 2.\nLine 3.\nLine 4.\n",
        encoding="utf-8",
    )
    detector = PhaseDetector(run_dir)
    info = detector.detect_advisory()
    assert info.phase == Phase.BUILD_NEEDED


# ── apsf next state-first ────────────────────────────────────────────────────

def _make_run_with_state(runs_dir: Path, run_name: str, phase_value: str) -> Path:
    """run_state.json を持つ run dir を作成する（runs_dir/<run_name>/）。"""
    import json
    run_dir = runs_dir / run_name
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "execution-assignment.md").write_text(
        "# Execution Assignment\n\n"
        "- Executor: Claude\n- Mode: auto\n- Provider: Anthropic\n- Notes: test\n",
        encoding="utf-8",
    )
    (run_dir / "goal.md").write_text(
        "# Goal\n\n## Goal Statement\nTest goal.\n\n"
        "## Background\nBackground text here.\n\n"
        "## Success Criteria\n- Criteria A\n- Criteria B\n",
        encoding="utf-8",
    )
    state = {
        "run_id": run_name,
        "current_phase": phase_value,
        "phase_status": "pending",
        "current_owner": "Builder",
        "retry_count": 0,
        "last_error": "",
        "active_handoff_id": "",
    }
    (run_dir / "run_state.json").write_text(
        json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return run_dir


def _invoke_next(tmp_path: Path, run_name: str) -> str:
    """
    APSF_ROOT を tmp_path に向けて singleton をリセットしてから apsf next を呼ぶ。
    出力文字列を返す。
    """
    import os
    import apsf.legacy.config.settings as _settings_mod
    from typer.testing import CliRunner
    from apsf.legacy.cli.main import app

    original_env = os.environ.copy()
    original_instance = _settings_mod._settings_instance
    try:
        os.environ["APSF_ROOT"] = str(tmp_path)
        _settings_mod._settings_instance = None
        runner = CliRunner()
        result = runner.invoke(app, ["next", run_name])
        return result.output
    finally:
        os.environ.clear()
        os.environ.update(original_env)
        _settings_mod._settings_instance = original_instance


def test_next_cmd_shows_canonical_phase_when_state_exists(tmp_path: Path) -> None:
    """apsf next は run_state.json の phase を [canonical] として表示する。"""
    runs_dir = tmp_path / "runs"
    # run_state.json に BUILD_NEEDED を設定（file-based は PLAN_NEEDED になるはず）
    _make_run_with_state(runs_dir, "test-run", "BUILD_NEEDED")

    output = _invoke_next(tmp_path, "test-run")
    assert "BUILD_NEEDED" in output, f"Expected BUILD_NEEDED in output: {output!r}"
    assert "[canonical]" in output, f"Expected [canonical] in output: {output!r}"


def test_next_cmd_shows_advisory_phase_when_no_state(tmp_path: Path) -> None:
    """apsf next は run_state.json がない場合 [advisory] を表示する。"""
    runs_dir = tmp_path / "runs"
    run_dir = runs_dir / "test-run"
    run_dir.mkdir(parents=True)
    (run_dir / "execution-assignment.md").write_text(
        "# Execution Assignment\n\n"
        "- Executor: Claude\n- Mode: auto\n- Provider: Anthropic\n- Notes: test\n",
        encoding="utf-8",
    )
    (run_dir / "goal.md").write_text(
        "# Goal\n\n## Goal Statement\nTest goal.\n\n"
        "## Background\nBackground text here.\n\n"
        "## Success Criteria\n- Criteria A\n- Criteria B\n",
        encoding="utf-8",
    )

    output = _invoke_next(tmp_path, "test-run")
    assert "[advisory]" in output, f"Expected [advisory] in output: {output!r}"


def test_next_cmd_falls_back_to_advisory_when_state_refresh_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """run_state refresh save が失敗しても apsf next は advisory phase を表示して継続する。"""
    import os
    import apsf.legacy.config.settings as _settings_mod
    from typer.testing import CliRunner
    from apsf.legacy.cli.main import app
    from apsf.core.state.run_state_repository import RunStateRepository

    runs_dir = tmp_path / "runs"
    _make_run_with_state(runs_dir, "test-run", "PLAN_NEEDED")
    (runs_dir / "test-run" / "plan.md").write_text(
        "# Plan\n\nLine 1.\nLine 2.\nLine 3.\nLine 4.\n",
        encoding="utf-8",
    )

    def _boom(self: RunStateRepository, state) -> None:
        raise PermissionError("access denied during test")

    monkeypatch.setattr(RunStateRepository, "save", _boom)

    original_env = os.environ.copy()
    original_instance = _settings_mod._settings_instance
    try:
        os.environ["APSF_ROOT"] = str(tmp_path)
        _settings_mod._settings_instance = None
        runner = CliRunner()
        result = runner.invoke(app, ["next", "test-run"])
    finally:
        os.environ.clear()
        os.environ.update(original_env)
        _settings_mod._settings_instance = original_instance

    assert result.exit_code == 0, result.output
    assert "BUILD_NEEDED" in result.output, result.output
    assert "[advisory]" in result.output, result.output
    assert "Failed to refresh run_state.json" in result.output, result.output
