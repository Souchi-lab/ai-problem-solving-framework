"""
CheckpointCaptureService のテスト

カバー範囲:
  - success path: checkpoint JSON が正しい schema で保存される
  - run_state あり + session events あり: related_event_id が最新 event に紐づく
  - run_state あり + session events なし: related_event_id = "" (explicit null policy)
  - run_state なし: CheckpointCaptureError
  - summary (note) フィールドが記録される
  - current truth（run_state.json / session_events.jsonl）を変更しない
  - 複数 checkpoint を同一 run に保存できる
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from apsf.core.restore.checkpoint_capture_service import (
    CheckpointCaptureError,
    CheckpointCaptureService,
)


# ── helpers ───────────────────────────────────────────────────────────────────

def _write_run_state(run_dir: Path, phase: str = "BUILD_NEEDED", phase_status: str = "in_progress") -> None:
    state = {
        "run_id": run_dir.name,
        "current_phase": phase,
        "phase_status": phase_status,
        "current_owner": "Builder",
        "retry_count": 0,
        "last_error": "",
        "active_handoff_id": "",
        "gate_failures": [],
    }
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "run_state.json").write_text(json.dumps(state), encoding="utf-8")


def _write_session_events(run_dir: Path, event_ids: list[str]) -> None:
    lines = []
    for eid in event_ids:
        event = {
            "event_id": eid,
            "timestamp": "2026-04-02T00:00:00+00:00",
            "event_type": "act_started",
            "run_id": run_dir.name,
            "payload": {"phase": "BUILD_NEEDED", "target_file": "build.md", "owner": "Builder"},
        }
        lines.append(json.dumps(event))
    (run_dir / "session_events.jsonl").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _load_checkpoint(run_dir: Path, checkpoint_id: str) -> dict:
    return json.loads(
        (run_dir / "recovery" / "checkpoints" / f"{checkpoint_id}.json")
        .read_text(encoding="utf-8")
    )


# ── success path ──────────────────────────────────────────────────────────────

def test_capture_creates_checkpoint_json(tmp_path: Path) -> None:
    run_dir = tmp_path / "my-run"
    _write_run_state(run_dir, phase="BUILD_NEEDED", phase_status="in_progress")

    result = CheckpointCaptureService().capture(run_dir, "cp-001")

    assert result.checkpoint_id == "cp-001"
    assert result.phase == "BUILD_NEEDED"
    assert result.phase_status == "in_progress"

    cp = _load_checkpoint(run_dir, "cp-001")
    assert cp["checkpoint_id"] == "cp-001"
    assert cp["run_id"] == "my-run"
    assert cp["phase"] == "BUILD_NEEDED"
    assert cp["phase_status"] == "in_progress"
    assert cp["current_owner"] == "Builder"
    assert "created_at" in cp


def test_capture_with_session_events_records_latest_event_id(tmp_path: Path) -> None:
    run_dir = tmp_path / "my-run"
    _write_run_state(run_dir)
    _write_session_events(run_dir, ["evt-aaa", "evt-bbb", "evt-ccc"])

    result = CheckpointCaptureService().capture(run_dir, "cp-001")

    assert result.related_event_id == "evt-ccc"
    cp = _load_checkpoint(run_dir, "cp-001")
    assert cp["related_event_id"] == "evt-ccc"


def test_capture_without_session_events_sets_empty_related_event_id(tmp_path: Path) -> None:
    """session_events.jsonl がない場合は related_event_id = "" (explicit null policy)。"""
    run_dir = tmp_path / "my-run"
    _write_run_state(run_dir)
    # session_events.jsonl を作成しない

    result = CheckpointCaptureService().capture(run_dir, "cp-001")

    assert result.related_event_id == ""
    cp = _load_checkpoint(run_dir, "cp-001")
    assert cp["related_event_id"] == ""


def test_capture_with_empty_session_events_sets_empty_related_event_id(tmp_path: Path) -> None:
    """session_events.jsonl が 0 件の場合も related_event_id = ""。"""
    run_dir = tmp_path / "my-run"
    _write_run_state(run_dir)
    _write_session_events(run_dir, [])

    result = CheckpointCaptureService().capture(run_dir, "cp-001")

    assert result.related_event_id == ""


def test_capture_records_summary(tmp_path: Path) -> None:
    run_dir = tmp_path / "my-run"
    _write_run_state(run_dir)

    result = CheckpointCaptureService().capture(run_dir, "cp-001", summary="before risky change")

    assert result.summary == "before risky change"
    cp = _load_checkpoint(run_dir, "cp-001")
    assert cp["summary"] == "before risky change"


def test_capture_multiple_checkpoints_in_same_run(tmp_path: Path) -> None:
    run_dir = tmp_path / "my-run"
    _write_run_state(run_dir, phase="PLAN_NEEDED")

    CheckpointCaptureService().capture(run_dir, "cp-001")
    CheckpointCaptureService().capture(run_dir, "cp-002", summary="second checkpoint")

    cp1 = _load_checkpoint(run_dir, "cp-001")
    cp2 = _load_checkpoint(run_dir, "cp-002")
    assert cp1["checkpoint_id"] == "cp-001"
    assert cp2["checkpoint_id"] == "cp-002"
    assert cp2["summary"] == "second checkpoint"


# ── error path ────────────────────────────────────────────────────────────────

# ── collision policy ──────────────────────────────────────────────────────────

def test_capture_raises_on_existing_checkpoint_id_by_default(tmp_path: Path) -> None:
    """同一 checkpoint_id が既に存在する場合はデフォルトで CheckpointCaptureError。"""
    run_dir = tmp_path / "my-run"
    _write_run_state(run_dir)

    CheckpointCaptureService().capture(run_dir, "cp-001", summary="first")

    with pytest.raises(CheckpointCaptureError, match="already exists"):
        CheckpointCaptureService().capture(run_dir, "cp-001", summary="second")

    # 元の checkpoint が上書きされていないこと
    cp = _load_checkpoint(run_dir, "cp-001")
    assert cp["summary"] == "first"


def test_capture_overwrites_when_overwrite_true(tmp_path: Path) -> None:
    """overwrite=True を指定した場合は既存 checkpoint を上書きできる。"""
    run_dir = tmp_path / "my-run"
    _write_run_state(run_dir)

    CheckpointCaptureService().capture(run_dir, "cp-001", summary="first")
    CheckpointCaptureService().capture(run_dir, "cp-001", summary="updated", overwrite=True)

    cp = _load_checkpoint(run_dir, "cp-001")
    assert cp["summary"] == "updated"


def test_capture_raises_when_run_state_missing(tmp_path: Path) -> None:
    run_dir = tmp_path / "my-run"
    run_dir.mkdir()
    # run_state.json を作成しない

    with pytest.raises(CheckpointCaptureError, match="run_state.json not found"):
        CheckpointCaptureService().capture(run_dir, "cp-001")


# ── current truth protection ──────────────────────────────────────────────────

def test_capture_does_not_modify_run_state(tmp_path: Path) -> None:
    """checkpoint capture は run_state.json を変更しないこと。"""
    run_dir = tmp_path / "my-run"
    _write_run_state(run_dir, phase="BUILD_NEEDED", phase_status="in_progress")

    before = (run_dir / "run_state.json").read_text(encoding="utf-8")

    CheckpointCaptureService().capture(run_dir, "cp-001")

    after = (run_dir / "run_state.json").read_text(encoding="utf-8")
    assert before == after


def test_capture_does_not_modify_session_events(tmp_path: Path) -> None:
    """checkpoint capture は session_events.jsonl を変更しないこと。"""
    run_dir = tmp_path / "my-run"
    _write_run_state(run_dir)
    _write_session_events(run_dir, ["evt-001", "evt-002"])

    before = (run_dir / "session_events.jsonl").read_text(encoding="utf-8")

    CheckpointCaptureService().capture(run_dir, "cp-001")

    after = (run_dir / "session_events.jsonl").read_text(encoding="utf-8")
    assert before == after
