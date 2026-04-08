"""
ForceAuditRepository — --force override の audit trail を per-run JSON に記録する

保存先: <run_dir>/force_audit.json

記録項目:
  timestamp     : ISO 8601 UTC 文字列
  command       : "write-phase" | "act"
  target_file   : 対象ファイル名
  role          : 書き込みロール名（不明な場合は空文字）
  had_reason    : reason が指定されていたか（bool）
  reason        : force_reason 文字列（なければ空文字）
  override_kind : "overwrite" | "consistency_gate_bypass"
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path


@dataclass
class ForceAuditEntry:
    timestamp: str
    command: str
    target_file: str
    role: str
    had_reason: bool
    reason: str
    override_kind: str


class ForceAuditRepository:
    FILENAME = "force_audit.json"

    def __init__(self, run_dir: Path) -> None:
        self._path = run_dir / self.FILENAME

    def append(self, entry: ForceAuditEntry) -> None:
        """audit entry を force_audit.json に追記する。"""
        existing = self._load_raw()
        existing.append(asdict(entry))
        self._path.write_text(
            json.dumps({"entries": existing}, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def load(self) -> list[ForceAuditEntry]:
        """保存済みの全 audit entries を返す。ファイルがなければ空リスト。"""
        return [ForceAuditEntry(**r) for r in self._load_raw()]

    def _load_raw(self) -> list[dict]:
        if not self._path.exists():
            return []
        data = json.loads(self._path.read_text(encoding="utf-8"))
        return data.get("entries", [])


def make_audit_entry(
    command: str,
    target_file: str,
    role: str,
    reason: str | None,
    override_kind: str,
) -> ForceAuditEntry:
    """ForceAuditEntry を現在時刻で生成するファクトリ。"""
    return ForceAuditEntry(
        timestamp=datetime.now(timezone.utc).isoformat(),
        command=command,
        target_file=target_file,
        role=role,
        had_reason=bool(reason),
        reason=reason or "",
        override_kind=override_kind,
    )
