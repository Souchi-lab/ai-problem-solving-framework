"""
CheckpointCaptureService — execution checkpoint capture

run-067 scope: run_state.json と session_events.jsonl を read-only に参照し、
recovery/checkpoints/<checkpoint_id>.json に最小 metadata を保存する。

apply / replay / mixed capture は含まない。

Data sources:
    run_state.json          — phase / phase_status / current_owner
    session_events.jsonl    — latest event_id を related_event_id として記録
                              （events がない場合は "" = explicit null policy）

Checkpoint schema:
    checkpoint_id       str
    run_id              str
    phase               str   (from run_state.current_phase)
    phase_status        str   (from run_state.phase_status)
    current_owner       str   (from run_state.current_owner)
    related_event_id    str   (latest session event_id, "" if none)
    created_at          str   (ISO 8601 UTC, capture 時刻)
    summary             str   (optional note, "" if not provided)

current truth との関係:
    run_state.json / session_events.jsonl は read-only 参照のみ。
    recovery/checkpoints/ への書き込みは current truth を変更しない。
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


class CheckpointCaptureError(Exception):
    """CheckpointCaptureService が capture を拒否・失敗したときに raise される。"""


@dataclass
class CheckpointCaptureResult:
    checkpoint_id: str
    run_id: str
    phase: str
    phase_status: str
    related_event_id: str
    summary: str


class CheckpointCaptureService:
    """
    current run_state を snapshot して recovery/checkpoints/<checkpoint_id>.json に保存する。

    run_state.json が存在しない場合は CheckpointCaptureError を raise する。
    session_events.jsonl が存在しない場合は related_event_id を "" として保存する。
    """

    def capture(
        self,
        run_dir: Path,
        checkpoint_id: str,
        summary: str = "",
        overwrite: bool = False,
    ) -> CheckpointCaptureResult:
        """
        execution checkpoint を capture する。

        Args:
            run_dir:       capture 元の run directory
            checkpoint_id: チェックポイント ID（呼び出し元が指定）
            summary:       任意の補足メモ（空文字可）
            overwrite:     True の場合のみ既存 checkpoint を上書きする。
                           False（デフォルト）で既存 ID があれば CheckpointCaptureError。

        Returns:
            CheckpointCaptureResult

        Raises:
            CheckpointCaptureError: run_state.json が存在しない / 読み取れない /
                                    checkpoint_id が衝突かつ overwrite=False
        """
        run_id = run_dir.name

        # 衝突チェック（overwrite=False のデフォルト: 既存 ID は拒否）
        checkpoint_path = run_dir / "recovery" / "checkpoints" / f"{checkpoint_id}.json"
        if checkpoint_path.exists() and not overwrite:
            raise CheckpointCaptureError(
                f"checkpoint '{checkpoint_id}' already exists. "
                "Use overwrite=True (CLI: --overwrite) to replace it."
            )

        # run_state 読み取り（required）
        state = self._load_run_state(run_dir)

        # session events 読み取り（optional — なければ related_event_id = ""）
        related_event_id = self._resolve_related_event_id(run_dir)

        # checkpoint metadata 組み立て
        checkpoint = {
            "checkpoint_id": checkpoint_id,
            "run_id": run_id,
            "phase": state.current_phase,
            "phase_status": state.phase_status,
            "current_owner": state.current_owner,
            "related_event_id": related_event_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "summary": summary,
        }

        # recovery/checkpoints/ に保存
        checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
        checkpoint_path.write_text(
            json.dumps(checkpoint, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        return CheckpointCaptureResult(
            checkpoint_id=checkpoint_id,
            run_id=run_id,
            phase=state.current_phase,
            phase_status=state.phase_status,
            related_event_id=related_event_id,
            summary=summary,
        )

    # ── private helpers ───────────────────────────────────────────────────────

    def _load_run_state(self, run_dir: Path):  # -> RunState
        """
        run_state.json を読み込む。

        Raises:
            CheckpointCaptureError: ファイルが存在しない / 読み取れない
        """
        from ..state.run_state_repository import RunStateRepository

        state = RunStateRepository(run_dir).load()
        if state is None:
            raise CheckpointCaptureError(
                f"run_state.json not found in '{run_dir.name}'. "
                "Execution checkpoint requires an initialized run state."
            )
        return state

    def _resolve_related_event_id(self, run_dir: Path) -> str:
        """
        session_events.jsonl から最新 event の event_id を返す。

        session_events.jsonl が存在しない、またはイベントが 0 件の場合は "" を返す
        （explicit null policy: error にしない）。
        """
        from ..session.session_event_repository import SessionEventRepository

        try:
            events = SessionEventRepository(run_dir).load()
        except Exception:
            return ""

        if not events:
            return ""

        return events[-1].event_id
