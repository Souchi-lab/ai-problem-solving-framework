"""
HandoffRepository — handoff.json の load / save

ArtifactRepository 経由で書き込むことで safe write / lock semantics を適用する。
writing_role=None（ownership check skip）: handoff.json は system state。
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from ..storage.artifact_repository import ArtifactRepository
from .handoff_record import HandoffRecord


class HandoffRepository:
    FILENAME = "handoff.json"

    def __init__(self, run_dir: Path) -> None:
        self._run_dir = run_dir
        self._path = run_dir / self.FILENAME
        self._artifact_repo = ArtifactRepository(writing_role=None)

    def exists(self) -> bool:
        return self._path.exists()

    def load(self) -> Optional[HandoffRecord]:
        """
        handoff.json を読んで HandoffRecord を返す。
        ファイルが存在しない場合は None を返す（例外は raise しない）。
        """
        if not self._path.exists():
            return None
        try:
            data = json.loads(self._path.read_text(encoding="utf-8"))
            return HandoffRecord.from_dict(data)
        except (json.JSONDecodeError, KeyError, TypeError):
            return None

    def save(self, record: HandoffRecord) -> None:
        """
        HandoffRecord を handoff.json に保存する。
        ArtifactRepository 経由で atomic write + lock を適用する。
        """
        json_text = json.dumps(record.to_dict(), ensure_ascii=False, indent=2)
        self._artifact_repo.write(self._path, json_text)
