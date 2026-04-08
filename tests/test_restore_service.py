"""
RestoreService / RestoreGate tests.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from apsf.core.restore.restore_gate import RestoreGate, RestoreRequest
from apsf.core.restore.restore_service import RestoreError, RestoreService
from apsf.core.session.session_event import (
    EVENT_SNAPSHOT_APPLY_FAILED,
    EVENT_SNAPSHOT_APPLY_SUCCEEDED,
)
from apsf.core.session.session_event_repository import SessionEventRepository


def _make_snapshot(
    run_dir: Path,
    snapshot_id: str,
    target_paths: list[str],
    payload_contents: dict[str, str] | None = None,
) -> None:
    snap_dir = run_dir / "recovery" / "snapshots" / snapshot_id
    (snap_dir / "payload").mkdir(parents=True, exist_ok=True)

    metadata = {
        "snapshot_id": snapshot_id,
        "source_phase": "BUILD_NEEDED",
        "captured_at": "2026-04-02T00:00:00+00:00",
        "file_count": len(target_paths),
        "target_paths": target_paths,
        "content_hashes": ["hash"] * len(target_paths),
    }
    (snap_dir / "metadata.json").write_text(json.dumps(metadata), encoding="utf-8")

    if payload_contents:
        for rel_path, content in payload_contents.items():
            payload_file = snap_dir / "payload" / rel_path
            payload_file.parent.mkdir(parents=True, exist_ok=True)
            payload_file.write_text(content, encoding="utf-8")


class TestRestoreGate:
    def setup_method(self) -> None:
        self.gate = RestoreGate()

    def _req(self, **kwargs) -> RestoreRequest:
        defaults = {
            "restore_class": "own_run_snapshot",
            "run_id": "my-run",
            "current_run_id": "my-run",
            "target_paths": ["plan.md"],
            "restore_reason": "intentional rollback",
        }
        defaults.update(kwargs)
        return RestoreRequest(**defaults)

    def test_own_run_snapshot_with_reason_is_allowed(self) -> None:
        decision = self.gate.classify(self._req())
        assert decision.allowed is True
        assert decision.verdict == "requires_reason"
        assert "intentional rollback" in decision.reason

    def test_own_run_snapshot_without_reason_is_denied(self) -> None:
        decision = self.gate.classify(self._req(restore_reason=None))
        assert decision.allowed is False
        assert decision.verdict == "requires_reason"
        assert "requires --restore-reason" in decision.reason

    def test_own_run_snapshot_empty_reason_is_denied(self) -> None:
        decision = self.gate.classify(self._req(restore_reason=""))
        assert decision.allowed is False
        assert "requires --restore-reason" in decision.reason

    def test_foreign_run_is_blocked(self) -> None:
        decision = self.gate.classify(self._req(run_id="other-run", restore_reason="test"))
        assert decision.allowed is False
        assert decision.verdict == "blocked"
        assert decision.restore_class == "foreign_run"
        assert "foreign-run restore is blocked" in decision.reason

    def test_system_artifact_touching_is_blocked(self) -> None:
        decision = self.gate.classify(self._req(target_paths=["run_state.json"]))
        assert decision.allowed is False
        assert decision.verdict == "blocked"
        assert decision.restore_class == "system_artifact_touching"

    def test_system_artifact_touching_wins_over_own_run(self) -> None:
        decision = self.gate.classify(
            self._req(
                restore_class="own_run_checkpoint",
                target_paths=["plan.md", "force_audit.json"],
            )
        )
        assert decision.allowed is False
        assert decision.restore_class == "system_artifact_touching"

    def test_all_system_artifacts_are_blocked(self) -> None:
        system_files = [
            "run_state.json",
            "artifact_manifest.json",
            "handoff.json",
            "force_audit.json",
            "session_events.jsonl",
        ]
        for fname in system_files:
            decision = self.gate.classify(self._req(target_paths=[fname]))
            assert decision.allowed is False, f"{fname} should be blocked"
            assert decision.restore_class == "system_artifact_touching"

    def test_mixed_is_blocked(self) -> None:
        decision = self.gate.classify(
            self._req(restore_class="mixed", restore_reason="any reason")
        )
        assert decision.allowed is False
        assert decision.verdict == "blocked"
        assert decision.restore_class == "mixed"
        assert "atomicity" in decision.reason

    def test_foreign_run_takes_priority_over_system_artifact(self) -> None:
        decision = self.gate.classify(
            self._req(
                run_id="other-run",
                target_paths=["run_state.json"],
                restore_reason="test",
            )
        )
        assert decision.restore_class == "foreign_run"


class TestRestoreService:
    def test_apply_snapshot_success(self, tmp_path: Path) -> None:
        run_dir = tmp_path / "my-run"
        run_dir.mkdir()

        _make_snapshot(
            run_dir,
            "snap-001",
            target_paths=["plan.md", "build.md"],
            payload_contents={"plan.md": "# Plan\n", "build.md": "# Build\n"},
        )

        result = RestoreService().apply_snapshot(run_dir, "snap-001", "rollback test")

        assert result.snapshot_id == "snap-001"
        assert sorted(result.restored_paths) == ["build.md", "plan.md"]
        assert result.restore_reason == "rollback test"
        assert (run_dir / "plan.md").read_text(encoding="utf-8") == "# Plan\n"
        assert (run_dir / "build.md").read_text(encoding="utf-8") == "# Build\n"
        events = SessionEventRepository(run_dir).load()
        assert events[-1].event_type == EVENT_SNAPSHOT_APPLY_SUCCEEDED
        assert events[-1].payload["snapshot_id"] == "snap-001"
        assert events[-1].payload["apply_reason"] == "rollback test"
        assert sorted(events[-1].payload["restored_paths"]) == ["build.md", "plan.md"]

    def test_apply_snapshot_missing_reason_raises(self, tmp_path: Path) -> None:
        run_dir = tmp_path / "my-run"
        run_dir.mkdir()
        _make_snapshot(run_dir, "snap-001", ["plan.md"])

        with pytest.raises(RestoreError, match="requires --restore-reason"):
            RestoreService().apply_snapshot(run_dir, "snap-001", None)
        events = SessionEventRepository(run_dir).load()
        assert events[-1].event_type == EVENT_SNAPSHOT_APPLY_FAILED
        assert events[-1].payload["snapshot_id"] == "snap-001"
        assert events[-1].payload["apply_reason"] == ""

    def test_apply_snapshot_empty_reason_raises(self, tmp_path: Path) -> None:
        run_dir = tmp_path / "my-run"
        run_dir.mkdir()
        _make_snapshot(run_dir, "snap-001", ["plan.md"])

        with pytest.raises(RestoreError, match="requires --restore-reason"):
            RestoreService().apply_snapshot(run_dir, "snap-001", "")

    def test_apply_snapshot_not_found_raises(self, tmp_path: Path) -> None:
        run_dir = tmp_path / "my-run"
        run_dir.mkdir()

        with pytest.raises(RestoreError, match="snapshot not found"):
            RestoreService().apply_snapshot(run_dir, "nonexistent", "some reason")
        events = SessionEventRepository(run_dir).load()
        assert events[-1].event_type == EVENT_SNAPSHOT_APPLY_FAILED
        assert events[-1].payload["snapshot_id"] == "nonexistent"
        assert events[-1].payload["apply_reason"] == "some reason"

    def test_apply_snapshot_system_artifact_blocked(self, tmp_path: Path) -> None:
        run_dir = tmp_path / "my-run"
        run_dir.mkdir()
        _make_snapshot(
            run_dir,
            "snap-sys",
            target_paths=["run_state.json"],
            payload_contents={"run_state.json": "{}"},
        )

        with pytest.raises(RestoreError, match="system artifact touching"):
            RestoreService().apply_snapshot(run_dir, "snap-sys", "trying to restore system file")

    def test_apply_snapshot_payload_file_missing_raises(self, tmp_path: Path) -> None:
        run_dir = tmp_path / "my-run"
        run_dir.mkdir()
        _make_snapshot(
            run_dir,
            "snap-no-payload",
            target_paths=["plan.md"],
        )

        with pytest.raises(RestoreError, match="payload file not found"):
            RestoreService().apply_snapshot(run_dir, "snap-no-payload", "test reason")

    def test_apply_snapshot_does_not_modify_recovery_dir(self, tmp_path: Path) -> None:
        run_dir = tmp_path / "my-run"
        run_dir.mkdir()
        _make_snapshot(
            run_dir,
            "snap-001",
            target_paths=["plan.md"],
            payload_contents={"plan.md": "# Plan restored\n"},
        )

        recovery_before = list((run_dir / "recovery").rglob("*"))

        RestoreService().apply_snapshot(run_dir, "snap-001", "test")

        recovery_after = list((run_dir / "recovery").rglob("*"))
        assert sorted(str(p) for p in recovery_before) == sorted(str(p) for p in recovery_after)

    def test_path_traversal_dotdot_is_rejected(self, tmp_path: Path) -> None:
        run_dir = tmp_path / "my-run"
        run_dir.mkdir()
        _make_snapshot(
            run_dir,
            "snap-traversal",
            target_paths=["../outside.txt"],
            payload_contents={"../outside.txt": "malicious"},
        )

        with pytest.raises(RestoreError, match="path traversal rejected"):
            RestoreService().apply_snapshot(run_dir, "snap-traversal", "test reason")

        assert not (tmp_path / "outside.txt").exists()

    def test_path_traversal_absolute_path_is_rejected(self, tmp_path: Path) -> None:
        run_dir = tmp_path / "my-run"
        run_dir.mkdir()
        _make_snapshot(
            run_dir,
            "snap-abs",
            target_paths=[str(tmp_path / "outside.txt")],
        )

        with pytest.raises(RestoreError, match="path traversal rejected"):
            RestoreService().apply_snapshot(run_dir, "snap-abs", "test reason")

    def test_apply_snapshot_updates_manifest_when_present(self, tmp_path: Path) -> None:
        import json as _json

        run_dir = tmp_path / "my-run"
        run_dir.mkdir()

        manifest_data = {
            "run_id": "my-run",
            "entries": {
                "plan.md": {
                    "artifact_name": "plan.md",
                    "artifact_type": "markdown",
                    "owner_role": "Planner",
                    "written_by": "Planner",
                    "status": "generated",
                    "checksum": "old-checksum",
                    "updated_at": "2026-04-01T00:00:00+00:00",
                    "finalized_at": "",
                    "finalized_by": "",
                    "revision": 1,
                    "source_handoff_id": "",
                },
            },
        }
        (run_dir / "artifact_manifest.json").write_text(
            _json.dumps(manifest_data), encoding="utf-8"
        )

        _make_snapshot(
            run_dir,
            "snap-001",
            target_paths=["plan.md"],
            payload_contents={"plan.md": "# Plan restored\n"},
        )

        RestoreService().apply_snapshot(run_dir, "snap-001", "manifest test")

        updated = _json.loads((run_dir / "artifact_manifest.json").read_text(encoding="utf-8"))
        entry = updated["entries"]["plan.md"]
        assert entry["written_by"] == "Restore"
        assert entry["revision"] == 2
        assert entry["checksum"] != "old-checksum"

    def test_apply_snapshot_skips_manifest_update_when_absent(self, tmp_path: Path) -> None:
        run_dir = tmp_path / "my-run"
        run_dir.mkdir()

        _make_snapshot(
            run_dir,
            "snap-001",
            target_paths=["plan.md"],
            payload_contents={"plan.md": "# Plan restored\n"},
        )

        result = RestoreService().apply_snapshot(run_dir, "snap-001", "no manifest run")

        assert result.snapshot_id == "snap-001"
        assert not (run_dir / "artifact_manifest.json").exists()

    def test_partial_payload_missing_leaves_earlier_files_unwritten(self, tmp_path: Path) -> None:
        run_dir = tmp_path / "my-run"
        run_dir.mkdir()

        _make_snapshot(
            run_dir,
            "snap-partial",
            target_paths=["plan.md", "build.md"],
            payload_contents={"plan.md": "# Plan\n"},
        )

        with pytest.raises(RestoreError, match="payload file not found"):
            RestoreService().apply_snapshot(run_dir, "snap-partial", "test reason")

        assert not (run_dir / "plan.md").exists()

    def test_apply_snapshot_warns_once_when_event_log_append_fails(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        from unittest.mock import patch

        run_dir = tmp_path / "my-run"
        run_dir.mkdir()
        _make_snapshot(
            run_dir,
            "snap-001",
            target_paths=["plan.md"],
            payload_contents={"plan.md": "# Plan\n"},
        )

        with patch(
            "apsf.core.session.session_event_repository.SessionEventRepository.append",
            side_effect=OSError("disk full"),
        ):
            result = RestoreService().apply_snapshot(run_dir, "snap-001", "test reason")

        captured = capsys.readouterr()
        assert result.snapshot_id == "snap-001"
        assert captured.err.count("Failed to append session event log") == 1
        assert "Continuing without blocking snapshot apply." in captured.err

    def test_apply_snapshot_keeps_original_error_when_event_log_append_fails(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        from unittest.mock import patch

        run_dir = tmp_path / "my-run"
        run_dir.mkdir()

        with patch(
            "apsf.core.session.session_event_repository.SessionEventRepository.append",
            side_effect=OSError("disk full"),
        ):
            with pytest.raises(RestoreError, match="snapshot not found"):
                RestoreService().apply_snapshot(run_dir, "missing", "test reason")

        captured = capsys.readouterr()
        assert captured.err.count("Failed to append session event log") == 1
