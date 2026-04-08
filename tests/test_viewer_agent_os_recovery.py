from __future__ import annotations

import asyncio
import json
from pathlib import Path

from apsf.viewer import api


def test_get_agent_os_info_includes_recovery_lists(tmp_path: Path, monkeypatch) -> None:
    run_dir = tmp_path / "run"
    (run_dir / "recovery" / "checkpoints").mkdir(parents=True)
    (run_dir / "recovery" / "snapshots" / "snap-001" / "payload").mkdir(parents=True)
    (run_dir / "session_events.jsonl").write_text(
        json.dumps(
            {
                "event_id": "evt-apply-001",
                "timestamp": "2026-04-02T01:00:00+00:00",
                "event_type": "checkpoint_apply_succeeded",
                "run_id": "run",
                "payload": {
                    "checkpoint_id": "cp-001",
                    "apply_reason": "resume builder",
                    "phase": "BUILD_NEEDED",
                    "phase_status": "in_progress",
                    "current_owner": "Builder",
                },
            }
        ) + "\n" + json.dumps(
            {
                "event_id": "evt-apply-002",
                "timestamp": "2026-04-02T01:10:00+00:00",
                "event_type": "snapshot_apply_failed",
                "run_id": "run",
                "payload": {
                    "snapshot_id": "snap-001",
                    "apply_reason": "rollback plan",
                    "error": "payload file not found",
                },
            }
        ) + "\n",
        encoding="utf-8",
    )

    (run_dir / "recovery" / "checkpoints" / "2026-04-01T00-00-00Z_BUILD_NEEDED_cp-001.json").write_text(
        json.dumps(
            {
                "checkpoint_id": "cp-001",
                "phase": "BUILD_NEEDED",
                "phase_status": "in_progress",
                "related_event_id": "evt-123",
                "created_at": "2026-04-01T00:00:00+00:00",
                "summary": "builder checkpoint",
            }
        ),
        encoding="utf-8",
    )
    (run_dir / "recovery" / "snapshots" / "snap-001" / "metadata.json").write_text(
        json.dumps(
            {
                "snapshot_id": "snap-001",
                "source_phase": "BUILD_NEEDED",
                "captured_at": "2026-04-01T00:05:00+00:00",
                "file_count": 2,
                "target_paths": ["src/app.py", "README.md"],
                "content_hashes": ["abc", "def"],
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(api, "_resolve_run_dir", lambda taxonomy, run_name: run_dir)

    response = asyncio.run(api.get_agent_os_info("fw-improvement", "dummy-run"))

    assert len(response.recovery_checkpoints) == 1
    assert response.recovery_checkpoints[0].checkpoint_id == "cp-001"
    assert response.recovery_checkpoints[0].related_event_id == "evt-123"

    assert len(response.recovery_snapshots) == 1
    assert response.recovery_snapshots[0].snapshot_id == "snap-001"
    assert response.recovery_snapshots[0].file_count == 2
    assert response.recovery_snapshots[0].target_paths == ["src/app.py", "README.md"]
    assert len(response.recovery_apply_traces) == 2
    assert response.recovery_apply_traces[0].event_type == "snapshot_apply_failed"
    assert response.recovery_apply_traces[0].target_kind == "snapshot"
    assert response.recovery_apply_traces[0].target_id == "snap-001"
    assert response.recovery_apply_traces[0].reason == "rollback plan"
    assert response.recovery_apply_traces[0].status == "failure"
    assert response.recovery_apply_traces[1].event_type == "checkpoint_apply_succeeded"
    assert response.recovery_apply_traces[1].target_kind == "checkpoint"
    assert response.recovery_apply_traces[1].target_id == "cp-001"
    assert response.recovery_apply_traces[1].reason == "resume builder"
    assert response.recovery_apply_traces[1].status == "success"


def test_get_agent_os_info_returns_empty_recovery_lists_when_absent(tmp_path: Path, monkeypatch) -> None:
    run_dir = tmp_path / "run"
    run_dir.mkdir()

    monkeypatch.setattr(api, "_resolve_run_dir", lambda taxonomy, run_name: run_dir)

    response = asyncio.run(api.get_agent_os_info("fw-improvement", "dummy-run"))

    assert response.recovery_checkpoints == []
    assert response.recovery_snapshots == []
    assert response.recovery_apply_traces == []
