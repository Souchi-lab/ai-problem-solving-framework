"""
SessionEventRepository — session_events.jsonl への append-only 書き込み / 読み込み

JSON Lines 形式（1 行 = 1 JSON オブジェクト）を使うことで:
- 読み取りなしに末尾 append できる（部分書き込みに強い）
- 各行が独立しているため破損が 1 行に局所化される

このリポジトリはイベントを追記するだけで、既存行を書き換えない。
"""

from __future__ import annotations

import json
from pathlib import Path

from .session_event import SessionEvent


class SessionEventRepository:
    FILENAME = "session_events.jsonl"

    def __init__(self, run_dir: Path) -> None:
        self._path = run_dir / self.FILENAME

    def append(self, event: SessionEvent) -> None:
        """event を session_events.jsonl に 1 行追記する。"""
        line = json.dumps(event.to_dict(), ensure_ascii=False) + "\n"
        with self._path.open("a", encoding="utf-8") as f:
            f.write(line)

    def load(self) -> list[SessionEvent]:
        """
        session_events.jsonl を読んで SessionEvent のリストを返す。
        ファイルが存在しない場合は空リスト。
        パースできない行はスキップする（部分破損に対する耐性）。
        """
        if not self._path.exists():
            return []
        events: list[SessionEvent] = []
        for line in self._path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                events.append(SessionEvent.from_dict(json.loads(line)))
            except (json.JSONDecodeError, KeyError, TypeError):
                continue
        return events
