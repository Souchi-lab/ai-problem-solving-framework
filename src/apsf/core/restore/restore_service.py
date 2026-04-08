"""
RestoreService - apply an own-run file snapshot to the live run directory.

run-064 scope:
    - own-run snapshot apply only
    - no checkpoint restore / mixed restore / foreign restore

run-071 trace polish:
    - append snapshot apply success/failure events to session_events.jsonl
    - keep event append failure non-blocking with a single stderr warning
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from .restore_gate import RestoreGate, RestoreRequest


class RestoreError(Exception):
    """Raised when snapshot apply is blocked or fails."""


@dataclass
class RestoreResult:
    snapshot_id: str
    restored_paths: list[str] = field(default_factory=list)
    restore_reason: str = ""


_RESTORE_ROLE = "Restore"


class RestoreService:
    """Apply a file snapshot into the current run directory."""

    def __init__(self) -> None:
        self._gate = RestoreGate()

    def apply_snapshot(
        self,
        run_dir: Path,
        snapshot_id: str,
        restore_reason: Optional[str],
    ) -> RestoreResult:
        from ..session.session_event import (
            make_snapshot_apply_failed_event,
            make_snapshot_apply_succeeded_event,
        )
        from ..session.session_event_repository import SessionEventRepository

        run_id = run_dir.name
        session_repo = SessionEventRepository(run_dir)
        warned_event_log_failure = False

        def _warn_event_log_failure(exc: Exception) -> None:
            nonlocal warned_event_log_failure
            if warned_event_log_failure:
                return
            warned_event_log_failure = True
            print(
                "[Warn] Failed to append session event log "
                f"({SessionEventRepository.FILENAME}): {exc}. "
                "Continuing without blocking snapshot apply.",
                file=sys.stderr,
            )

        try:
            metadata = self._load_metadata(run_dir, snapshot_id)
            target_paths: list[str] = metadata.get("target_paths", [])

            request = RestoreRequest(
                restore_class="own_run_snapshot",
                run_id=run_id,
                current_run_id=run_id,
                target_paths=target_paths,
                restore_reason=restore_reason or None,
            )
            decision = self._gate.classify(request)
            if not decision.allowed:
                raise RestoreError(f"[RestoreGate] {decision.reason}")

            resolved_run_dir = run_dir.resolve()
            self._check_path_containment(resolved_run_dir, target_paths)

            payload_dir = run_dir / "recovery" / "snapshots" / snapshot_id / "payload"
            plan = self._preflight_payload(payload_dir, snapshot_id, target_paths)
            restored = self._execute_writes(run_dir, run_id, plan)

            try:
                session_repo.append(
                    make_snapshot_apply_succeeded_event(
                        run_id=run_id,
                        snapshot_id=snapshot_id,
                        apply_reason=restore_reason or "",
                        restored_paths=restored,
                    )
                )
            except Exception as exc:
                _warn_event_log_failure(exc)

            return RestoreResult(
                snapshot_id=snapshot_id,
                restored_paths=restored,
                restore_reason=restore_reason or "",
            )
        except RestoreError as exc:
            try:
                session_repo.append(
                    make_snapshot_apply_failed_event(
                        run_id=run_id,
                        snapshot_id=snapshot_id,
                        apply_reason=restore_reason or "",
                        error=str(exc),
                    )
                )
            except Exception as event_exc:
                _warn_event_log_failure(event_exc)
            raise

    def _load_metadata(self, run_dir: Path, snapshot_id: str) -> dict:
        metadata_path = run_dir / "recovery" / "snapshots" / snapshot_id / "metadata.json"
        if not metadata_path.exists():
            raise RestoreError(
                f"snapshot not found: '{snapshot_id}' "
                f"(expected: {metadata_path})"
            )
        try:
            data = json.loads(metadata_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            raise RestoreError(
                f"failed to load snapshot metadata for '{snapshot_id}': {exc}"
            ) from exc

        encoding = data.get("encoding", "utf-8")
        if encoding != "utf-8":
            raise RestoreError(
                f"unsupported snapshot encoding: '{encoding}'. "
                "Only 'utf-8' is supported in v1."
            )

        return data

    def _check_path_containment(
        self,
        resolved_run_dir: Path,
        target_paths: list[str],
    ) -> None:
        for rel_path in target_paths:
            p = Path(rel_path)
            if p.is_absolute():
                raise RestoreError(
                    f"path traversal rejected: '{rel_path}' is an absolute path. "
                    "target_paths must be relative to the run directory."
                )
            try:
                resolved = (resolved_run_dir / rel_path).resolve()
                resolved.relative_to(resolved_run_dir)
            except ValueError:
                raise RestoreError(
                    f"path traversal rejected: '{rel_path}' escapes the run directory. "
                    f"run_dir: {resolved_run_dir}"
                )

    def _preflight_payload(
        self,
        payload_dir: Path,
        snapshot_id: str,
        target_paths: list[str],
    ) -> list[tuple[Path, str]]:
        plan: list[tuple[Path, str]] = []
        for rel_path in target_paths:
            src = payload_dir / rel_path
            if not src.exists():
                raise RestoreError(
                    f"payload file not found: '{rel_path}' "
                    f"in snapshot '{snapshot_id}'"
                )
            content = src.read_text(encoding="utf-8")
            plan.append((Path(rel_path), content))
        return plan

    def _execute_writes(
        self,
        run_dir: Path,
        run_id: str,
        plan: list[tuple[Path, str]],
    ) -> list[str]:
        from ..manifest.manifest_repository import ManifestRepository
        from ..storage.artifact_repository import ArtifactRepository

        artifact_repo = ArtifactRepository(writing_role=None)
        manifest_repo = ManifestRepository(run_dir)
        restored: list[str] = []

        for rel_path, content in plan:
            dst = run_dir / rel_path
            dst.parent.mkdir(parents=True, exist_ok=True)
            artifact_repo.write(dst, content)

            if manifest_repo.exists():
                manifest_repo.update_entry(
                    artifact_name=rel_path.name,
                    writing_role=_RESTORE_ROLE,
                    content=content,
                    run_id=run_id,
                )

            restored.append(str(rel_path))

        return restored
