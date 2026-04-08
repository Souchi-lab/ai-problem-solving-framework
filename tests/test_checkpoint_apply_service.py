from __future__ import annotations

import json
import os
from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

import apsf.legacy.config.settings as settings_module
from apsf.core.restore.checkpoint_apply_service import (
    CheckpointApplyError,
    CheckpointApplyService,
)
from apsf.core.session.session_event import (
    EVENT_CHECKPOINT_APPLY_FAILED,
    EVENT_CHECKPOINT_APPLY_SUCCEEDED,
)
from apsf.core.session.session_event_repository import SessionEventRepository
from apsf.legacy.cli.main import app

runner = CliRunner()


@pytest.fixture(autouse=True)
def reset_settings_singleton():
    settings_module._settings_instance = None
    yield
    settings_module._settings_instance = None


def _write_run_state(
    run_dir: Path,
    phase: str = "BUILD_NEEDED",
    phase_status: str = "in_progress",
    current_owner: str = "Builder",
) -> None:
    state = {
        "run_id": run_dir.name,
        "current_phase": phase,
        "phase_status": phase_status,
        "current_owner": current_owner,
        "retry_count": 1,
        "last_error": "keep me",
        "active_handoff_id": "handoff-001",
        "gate_failures": ["warn-1"],
    }
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "run_state.json").write_text(json.dumps(state), encoding="utf-8")


def _write_checkpoint(
    run_dir: Path,
    checkpoint_id: str,
    *,
    run_id: str | None = None,
    phase: str = "REVIEW_NEEDED",
    phase_status: str = "completed",
    current_owner: str = "Critic",
) -> None:
    checkpoint = {
        "checkpoint_id": checkpoint_id,
        "run_id": run_id or run_dir.name,
        "phase": phase,
        "phase_status": phase_status,
        "current_owner": current_owner,
        "related_event_id": "evt-001",
        "created_at": "2026-04-02T00:00:00+00:00",
        "summary": "before review",
    }
    checkpoint_path = run_dir / "recovery" / "checkpoints" / f"{checkpoint_id}.json"
    checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
    checkpoint_path.write_text(json.dumps(checkpoint), encoding="utf-8")


def _load_run_state(run_dir: Path) -> dict:
    return json.loads((run_dir / "run_state.json").read_text(encoding="utf-8"))


def _setup_cli_env(tmp_path: Path) -> None:
    template_dir = tmp_path / "runs" / "_template"
    template_dir.mkdir(parents=True, exist_ok=True)
    for fname in [
        "execution-assignment.md",
        "goal.md",
        "plan.md",
        "build.md",
        "review.md",
        "result.md",
    ]:
        (template_dir / fname).write_text(f"# {fname}\n", encoding="utf-8")


def _invoke_cli(tmp_path: Path, args: list[str]):
    env = {**os.environ, "APSF_ROOT": str(tmp_path)}
    return runner.invoke(app, args, env=env)


def test_apply_updates_run_state_and_appends_success_event(tmp_path: Path) -> None:
    run_dir = tmp_path / "my-run"
    _write_run_state(
        run_dir,
        phase="BUILD_NEEDED",
        phase_status="failed",
        current_owner="Builder",
    )
    _write_checkpoint(
        run_dir,
        "cp-001",
        phase="PLAN_NEEDED",
        phase_status="in_progress",
        current_owner="Planner",
    )
    (run_dir / "session_events.jsonl").write_text(
        '{"event_id":"evt-live","timestamp":"2026-04-02T00:00:00+00:00","event_type":"act_started","run_id":"my-run","payload":{}}\n',
        encoding="utf-8",
    )
    (run_dir / "artifact_manifest.json").write_text('{"entries":[]}', encoding="utf-8")
    (run_dir / "plan.md").write_text("live plan\n", encoding="utf-8")

    before_manifest = (run_dir / "artifact_manifest.json").read_text(encoding="utf-8")
    before_plan = (run_dir / "plan.md").read_text(encoding="utf-8")

    result = CheckpointApplyService().apply(run_dir, "cp-001", "resume planner state")

    assert result.checkpoint_id == "cp-001"
    assert result.phase == "PLAN_NEEDED"
    assert result.phase_status == "in_progress"
    assert result.current_owner == "Planner"
    assert result.apply_reason == "resume planner state"

    state = _load_run_state(run_dir)
    assert state["current_phase"] == "PLAN_NEEDED"
    assert state["phase_status"] == "in_progress"
    assert state["current_owner"] == "Planner"
    assert state["retry_count"] == 1
    assert state["last_error"] == "keep me"
    assert state["active_handoff_id"] == "handoff-001"
    assert state["gate_failures"] == ["warn-1"]
    assert (run_dir / "artifact_manifest.json").read_text(encoding="utf-8") == before_manifest
    assert (run_dir / "plan.md").read_text(encoding="utf-8") == before_plan

    events = SessionEventRepository(run_dir).load()
    assert len(events) == 2
    assert events[0].event_id == "evt-live"
    assert events[1].event_type == EVENT_CHECKPOINT_APPLY_SUCCEEDED
    assert events[1].payload["checkpoint_id"] == "cp-001"
    assert events[1].payload["apply_reason"] == "resume planner state"
    assert events[1].payload["phase"] == "PLAN_NEEDED"
    assert events[1].payload["phase_status"] == "in_progress"
    assert events[1].payload["current_owner"] == "Planner"


def test_apply_raises_when_reason_missing_and_appends_failure_event(tmp_path: Path) -> None:
    run_dir = tmp_path / "my-run"
    _write_run_state(run_dir)
    _write_checkpoint(run_dir, "cp-001")

    with pytest.raises(CheckpointApplyError, match="requires --apply-reason"):
        CheckpointApplyService().apply(run_dir, "cp-001", "")

    events = SessionEventRepository(run_dir).load()
    assert events[-1].event_type == EVENT_CHECKPOINT_APPLY_FAILED
    assert events[-1].payload["checkpoint_id"] == "cp-001"
    assert events[-1].payload["apply_reason"] == ""
    assert "requires --apply-reason" in events[-1].payload["error"]


def test_apply_raises_when_checkpoint_not_found(tmp_path: Path) -> None:
    run_dir = tmp_path / "my-run"
    _write_run_state(run_dir)

    with pytest.raises(CheckpointApplyError, match="checkpoint not found"):
        CheckpointApplyService().apply(run_dir, "missing", "test reason")

    events = SessionEventRepository(run_dir).load()
    assert events[-1].event_type == EVENT_CHECKPOINT_APPLY_FAILED
    assert events[-1].payload["checkpoint_id"] == "missing"
    assert events[-1].payload["apply_reason"] == "test reason"


def test_apply_raises_when_checkpoint_is_malformed(tmp_path: Path) -> None:
    run_dir = tmp_path / "my-run"
    _write_run_state(run_dir)
    checkpoint_path = run_dir / "recovery" / "checkpoints" / "cp-001.json"
    checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
    checkpoint_path.write_text(
        json.dumps({"run_id": run_dir.name, "phase": "PLAN_NEEDED"}),
        encoding="utf-8",
    )

    with pytest.raises(CheckpointApplyError, match="malformed checkpoint"):
        CheckpointApplyService().apply(run_dir, "cp-001", "test reason")


def test_apply_blocks_foreign_run_checkpoint_and_appends_failure_event(tmp_path: Path) -> None:
    run_dir = tmp_path / "my-run"
    _write_run_state(run_dir)
    _write_checkpoint(run_dir, "cp-001", run_id="other-run")

    with pytest.raises(CheckpointApplyError, match="foreign-run restore is blocked"):
        CheckpointApplyService().apply(run_dir, "cp-001", "test reason")

    events = SessionEventRepository(run_dir).load()
    assert events[-1].event_type == EVENT_CHECKPOINT_APPLY_FAILED
    assert events[-1].payload["apply_reason"] == "test reason"
    assert "foreign-run restore is blocked" in events[-1].payload["error"]


def test_apply_raises_when_run_state_missing(tmp_path: Path) -> None:
    run_dir = tmp_path / "my-run"
    run_dir.mkdir(parents=True, exist_ok=True)
    _write_checkpoint(run_dir, "cp-001")

    with pytest.raises(CheckpointApplyError, match="run_state.json not found"):
        CheckpointApplyService().apply(run_dir, "cp-001", "test reason")


def test_apply_warns_once_when_event_log_append_fails(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    run_dir = tmp_path / "my-run"
    _write_run_state(run_dir)
    _write_checkpoint(run_dir, "cp-001")

    with patch(
        "apsf.core.session.session_event_repository.SessionEventRepository.append",
        side_effect=OSError("disk full"),
    ):
        result = CheckpointApplyService().apply(run_dir, "cp-001", "resume review")

    captured = capsys.readouterr()
    assert result.checkpoint_id == "cp-001"
    assert captured.err.count("Failed to append session event log") == 1
    assert "Continuing without blocking checkpoint apply." in captured.err


def test_apply_keeps_original_error_when_event_log_append_fails(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    run_dir = tmp_path / "my-run"
    _write_run_state(run_dir)

    with patch(
        "apsf.core.session.session_event_repository.SessionEventRepository.append",
        side_effect=OSError("disk full"),
    ):
        with pytest.raises(CheckpointApplyError, match="checkpoint not found"):
            CheckpointApplyService().apply(run_dir, "missing", "resume review")

    captured = capsys.readouterr()
    assert captured.err.count("Failed to append session event log") == 1


def test_cli_apply_checkpoint_updates_run_state(tmp_path: Path) -> None:
    _setup_cli_env(tmp_path)
    run_name = "2099-01-01_test-checkpoint-apply"
    run_dir = tmp_path / "runs" / run_name
    _write_run_state(
        run_dir,
        phase="BUILD_NEEDED",
        phase_status="failed",
        current_owner="Builder",
    )
    _write_checkpoint(
        run_dir,
        "cp-001",
        phase="RESULT_NEEDED",
        phase_status="pending",
        current_owner="Closure",
    )

    result = _invoke_cli(
        tmp_path,
        ["apply-checkpoint", run_name, "cp-001", "--apply-reason", "resume closure"],
    )

    assert result.exit_code == 0
    assert "checkpoint apply succeeded: checkpoint_id=cp-001 reason=resume closure" in result.output
    assert "Checkpoint applied: cp-001" in result.output
    state = _load_run_state(run_dir)
    assert state["current_phase"] == "RESULT_NEEDED"
    assert state["phase_status"] == "pending"
    assert state["current_owner"] == "Closure"


def test_cli_apply_checkpoint_emits_failure_trace(tmp_path: Path) -> None:
    _setup_cli_env(tmp_path)
    run_name = "2099-01-01_test-checkpoint-apply-failed"
    run_dir = tmp_path / "runs" / run_name
    _write_run_state(run_dir)

    result = _invoke_cli(
        tmp_path,
        ["apply-checkpoint", run_name, "missing", "--apply-reason", "resume closure"],
    )

    assert result.exit_code == 1
    assert "checkpoint apply failed: checkpoint_id=missing reason=resume closure" in result.output
    assert "checkpoint not found" in result.output
