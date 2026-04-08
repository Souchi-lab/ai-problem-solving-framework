"""
SessionEventRepository のテスト

カバー範囲:
  - append / load の基本動作
  - 複数 append の順序保持
  - ファイル不在時の空リスト
  - JSONL フォーマット（1 行 = 1 JSON）
  - 破損行のスキップ（耐性）
  - ActService.execute() 経由の session event 記録（統合）
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from apsf.core.session.session_event import (
    EVENT_ACT_COMPLETED,
    EVENT_ACT_FAILED,
    EVENT_ACT_STARTED,
    SessionEvent,
    make_act_completed_event,
    make_act_failed_event,
    make_act_started_event,
)
from apsf.core.session.session_event_repository import SessionEventRepository


# ── helper ───────────────────────────────────────────────────────────────────

def _make_event(event_type: str = EVENT_ACT_STARTED, run_id: str = "test-run") -> SessionEvent:
    return SessionEvent(
        event_id="test-id",
        timestamp="2026-04-01T00:00:00+00:00",
        event_type=event_type,
        run_id=run_id,
        payload={"phase": "PLAN_NEEDED", "target_file": "plan.md", "owner": "Planner"},
    )


# ── unit tests ───────────────────────────────────────────────────────────────

def test_load_returns_empty_when_file_absent(tmp_path: Path) -> None:
    repo = SessionEventRepository(tmp_path)
    assert repo.load() == []


def test_append_and_load_single_event(tmp_path: Path) -> None:
    repo = SessionEventRepository(tmp_path)
    event = _make_event()
    repo.append(event)

    loaded = repo.load()
    assert len(loaded) == 1
    assert loaded[0].event_id == event.event_id
    assert loaded[0].event_type == EVENT_ACT_STARTED
    assert loaded[0].run_id == "test-run"


def test_append_multiple_preserves_order(tmp_path: Path) -> None:
    repo = SessionEventRepository(tmp_path)
    e1 = make_act_started_event("run-1", "PLAN_NEEDED", "plan.md", "Planner")
    e2 = make_act_completed_event("run-1", "PLAN_NEEDED", "plan.md", "BUILD_NEEDED")
    e3 = make_act_failed_event("run-1", "BUILD_NEEDED", "build.md", "LLM error")
    repo.append(e1)
    repo.append(e2)
    repo.append(e3)

    loaded = repo.load()
    assert len(loaded) == 3
    assert loaded[0].event_type == EVENT_ACT_STARTED
    assert loaded[1].event_type == EVENT_ACT_COMPLETED
    assert loaded[2].event_type == EVENT_ACT_FAILED


def test_jsonl_format_one_json_per_line(tmp_path: Path) -> None:
    repo = SessionEventRepository(tmp_path)
    repo.append(_make_event(EVENT_ACT_STARTED))
    repo.append(_make_event(EVENT_ACT_COMPLETED))

    lines = (tmp_path / SessionEventRepository.FILENAME).read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    for line in lines:
        parsed = json.loads(line)
        assert "event_id" in parsed
        assert "event_type" in parsed


def test_load_skips_corrupt_lines(tmp_path: Path) -> None:
    repo = SessionEventRepository(tmp_path)
    repo.append(_make_event())

    # 破損行を手動で追記
    path = tmp_path / SessionEventRepository.FILENAME
    with path.open("a", encoding="utf-8") as f:
        f.write("not-valid-json\n")

    repo.append(_make_event(EVENT_ACT_COMPLETED))

    loaded = repo.load()
    assert len(loaded) == 2  # 破損行はスキップ
    assert loaded[0].event_type == EVENT_ACT_STARTED
    assert loaded[1].event_type == EVENT_ACT_COMPLETED


def test_event_payload_fields(tmp_path: Path) -> None:
    repo = SessionEventRepository(tmp_path)
    repo.append(make_act_started_event("my-run", "PLAN_NEEDED", "plan.md", "Planner"))

    loaded = repo.load()
    p = loaded[0].payload
    assert p["phase"] == "PLAN_NEEDED"
    assert p["target_file"] == "plan.md"
    assert p["owner"] == "Planner"


def test_act_completed_payload_fields(tmp_path: Path) -> None:
    repo = SessionEventRepository(tmp_path)
    repo.append(make_act_completed_event("my-run", "PLAN_NEEDED", "plan.md", "BUILD_NEEDED"))

    loaded = repo.load()
    p = loaded[0].payload
    assert p["next_phase"] == "BUILD_NEEDED"


def test_act_failed_payload_fields(tmp_path: Path) -> None:
    repo = SessionEventRepository(tmp_path)
    repo.append(make_act_failed_event("my-run", "BUILD_NEEDED", "build.md", "LLM timeout"))

    loaded = repo.load()
    p = loaded[0].payload
    assert p["error"] == "LLM timeout"


# ── integration: ActService.execute() wires session events ───────────────────

def _make_plan_needed_run_dir(tmp_path: Path) -> Path:
    """goal.md + execution-assignment.md 記入済みの run dir（→ PLAN_NEEDED）を作成する。"""
    run_dir = tmp_path / "test-run"
    run_dir.mkdir()
    (run_dir / "execution-assignment.md").write_text(
        "# Execution Assignment\n\n"
        "- Executor: Claude\n- Mode: auto\n- Provider: Anthropic\n- Notes: test\n",
        encoding="utf-8",
    )
    (run_dir / "goal.md").write_text(
        "# Goal\n\n## Goal Statement\nTest.\n\n## Background\nBackground.\n\n"
        "## Success Criteria\n- A\n- B\n- C\n",
        encoding="utf-8",
    )
    return run_dir


def test_act_execute_records_started_and_completed_events(tmp_path: Path) -> None:
    """ActService.execute() の成功系で act_started + act_completed が記録される。"""
    from apsf.legacy.orchestration.act_service import ActService
    from apsf.legacy.config.settings import Settings

    run_dir = _make_plan_needed_run_dir(tmp_path)

    mock_response = MagicMock()
    mock_response.content = "# Plan\n\nTest plan content.\nLine 2.\nLine 3.\nLine 4.\n"
    mock_provider = MagicMock()
    mock_provider.generate.return_value = mock_response

    with patch("apsf.legacy.orchestration.act_service.ActService._get_provider") as mock_get_provider:
        mock_get_provider.return_value = mock_provider
        settings = Settings(anthropic_api_key="test-key")
        result = ActService().execute(run_dir, "test-run", settings=settings)

    assert result.generated is True

    events = SessionEventRepository(run_dir).load()
    event_types = [e.event_type for e in events]
    assert EVENT_ACT_STARTED in event_types
    assert EVENT_ACT_COMPLETED in event_types


def test_act_execute_records_failed_event_on_provider_error(tmp_path: Path) -> None:
    """ActService.execute() の LLM エラー系で act_failed が記録される。"""
    from apsf.legacy.orchestration.act_service import ActService
    from apsf.legacy.config.settings import Settings
    from apsf.core.providers.base import ProviderError

    run_dir = _make_plan_needed_run_dir(tmp_path)

    mock_provider = MagicMock()
    mock_provider.generate.side_effect = ProviderError("LLM timeout")

    with patch("apsf.legacy.orchestration.act_service.ActService._get_provider") as mock_get_provider:
        mock_get_provider.return_value = mock_provider
        settings = Settings(anthropic_api_key="test-key")
        with pytest.raises(Exception):
            ActService().execute(run_dir, "test-run", settings=settings)

    events = SessionEventRepository(run_dir).load()
    event_types = [e.event_type for e in events]
    assert EVENT_ACT_STARTED in event_types
    assert EVENT_ACT_FAILED in event_types


def test_act_execute_warns_once_when_event_log_append_fails(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """event log append failure は stderr に 1 回だけ warning を出し、成功系は継続する。"""
    from apsf.legacy.orchestration.act_service import ActService
    from apsf.legacy.config.settings import Settings

    run_dir = _make_plan_needed_run_dir(tmp_path)

    mock_response = MagicMock()
    mock_response.content = "# Plan\n\nTest plan content.\nLine 2.\nLine 3.\nLine 4.\n"
    mock_provider = MagicMock()
    mock_provider.generate.return_value = mock_response

    with (
        patch("apsf.legacy.orchestration.act_service.ActService._get_provider") as mock_get_provider,
        patch(
            "apsf.core.session.session_event_repository.SessionEventRepository.append",
            side_effect=OSError("disk full"),
        ),
    ):
        mock_get_provider.return_value = mock_provider
        settings = Settings(anthropic_api_key="test-key")
        result = ActService().execute(run_dir, "test-run", settings=settings)

    captured = capsys.readouterr()
    assert result.generated is True
    assert (run_dir / "plan.md").exists()
    assert captured.err.count("Failed to append session event log") == 1
    assert "Continuing without blocking act." in captured.err


def test_act_execute_keeps_provider_error_when_event_log_append_fails(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """event log append failure が重なっても、元の provider failure を優先して返す。"""
    from apsf.legacy.orchestration.act_service import ActError, ActService
    from apsf.legacy.config.settings import Settings
    from apsf.core.providers.base import ProviderError

    run_dir = _make_plan_needed_run_dir(tmp_path)

    mock_provider = MagicMock()
    mock_provider.generate.side_effect = ProviderError("LLM timeout")

    with (
        patch("apsf.legacy.orchestration.act_service.ActService._get_provider") as mock_get_provider,
        patch(
            "apsf.core.session.session_event_repository.SessionEventRepository.append",
            side_effect=OSError("disk full"),
        ),
    ):
        mock_get_provider.return_value = mock_provider
        settings = Settings(anthropic_api_key="test-key")
        with pytest.raises(ActError, match="LLM generation failed: LLM timeout"):
            ActService().execute(run_dir, "test-run", settings=settings)

    captured = capsys.readouterr()
    assert captured.err.count("Failed to append session event log") == 1
