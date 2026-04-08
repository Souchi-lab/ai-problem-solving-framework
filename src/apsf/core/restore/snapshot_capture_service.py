"""
SnapshotCaptureService — text-only file snapshot capture

run-066 scope: UTF-8 text artifact の capture のみ。
binary / checkpoint capture / diff-based capture は含まない。

run-065 path/encoding spec:
  - payload path: run-relative POSIX canonical form（separator `/`、`.`/`..`/絶対パス禁止）
  - encoding: UTF-8（BOM なし）
  - binary / non-UTF-8 は SnapshotCaptureError で拒否

Snapshot layout（run-059 準拠）:
    recovery/snapshots/<snapshot_id>/metadata.json
    recovery/snapshots/<snapshot_id>/payload/<canonical_path>
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence


class SnapshotCaptureError(Exception):
    """SnapshotCaptureService が capture を拒否・失敗したときに raise される。"""


@dataclass
class CaptureResult:
    snapshot_id: str
    captured_paths: list[str] = field(default_factory=list)
    encoding: str = "utf-8"


class SnapshotCaptureService:
    """
    対象ファイル群を recovery/snapshots/<snapshot_id>/ に保存する最小 service。

    validate → normalize → UTF-8 read → payload write → metadata write の順。
    1 ファイルでも validation / encoding check に失敗すると全体を拒否する（preflight）。
    """

    ENCODING = "utf-8"

    def capture(
        self,
        run_dir: Path,
        snapshot_id: str,
        target_paths: Sequence[str],
        source_phase: str = "",
    ) -> CaptureResult:
        """
        text file 群を snapshot として保存する。

        Args:
            run_dir:       capture 元の run directory
            snapshot_id:   スナップショット ID（呼び出し元が指定）
            target_paths:  run-relative パスのリスト
            source_phase:  キャプチャ時の phase（空文字可）

        Returns:
            CaptureResult

        Raises:
            SnapshotCaptureError: path invalid / containment violation /
                                   directory 指定 / file not found /
                                   non-UTF-8 または binary content
        """
        resolved_run = run_dir.resolve()

        # preflight: すべてのファイルを validate + read してから write を開始する
        entries: list[tuple[str, str]] = []
        for rel in target_paths:
            canonical, content = self._validate_and_read(run_dir, resolved_run, rel)
            entries.append((canonical, content))

        # write payload files
        snap_dir = run_dir / "recovery" / "snapshots" / snapshot_id
        payload_dir = snap_dir / "payload"
        payload_dir.mkdir(parents=True, exist_ok=True)

        canonical_paths: list[str] = []
        content_hashes: list[str] = []

        for canonical, content in entries:
            dst = payload_dir / canonical
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_text(content, encoding=self.ENCODING)
            canonical_paths.append(canonical)
            content_hashes.append(
                hashlib.sha256(content.encode(self.ENCODING)).hexdigest()
            )

        # write metadata.json
        metadata = {
            "snapshot_id": snapshot_id,
            "source_phase": source_phase,
            "captured_at": datetime.now(timezone.utc).isoformat(),
            "file_count": len(canonical_paths),
            "target_paths": canonical_paths,
            "content_hashes": content_hashes,
            "encoding": self.ENCODING,
        }
        (snap_dir / "metadata.json").write_text(
            json.dumps(metadata, ensure_ascii=False, indent=2),
            encoding=self.ENCODING,
        )

        return CaptureResult(
            snapshot_id=snapshot_id,
            captured_paths=canonical_paths,
            encoding=self.ENCODING,
        )

    # ── private helpers ───────────────────────────────────────────────────────

    def _validate_and_read(
        self,
        run_dir: Path,
        resolved_run: Path,
        rel_path: str,
    ) -> tuple[str, str]:
        """
        rel_path を validate し、canonical POSIX path と UTF-8 content を返す。

        Raises:
            SnapshotCaptureError: validation または encoding check の失敗
        """
        p = Path(rel_path)

        # 絶対パス拒否
        if p.is_absolute():
            raise SnapshotCaptureError(
                f"absolute path is not allowed: '{rel_path}'. "
                "Provide a run-relative path."
            )

        # run_dir 内への containment 確認
        try:
            resolved_file = (run_dir / rel_path).resolve()
            resolved_file.relative_to(resolved_run)
        except ValueError:
            raise SnapshotCaptureError(
                f"path escapes run directory: '{rel_path}'. "
                f"run_dir: {resolved_run}"
            )

        # 存在確認
        if not resolved_file.exists():
            raise SnapshotCaptureError(
                f"file not found: '{rel_path}'"
            )

        # ディレクトリ拒否
        if resolved_file.is_dir():
            raise SnapshotCaptureError(
                f"directory is not supported: '{rel_path}'. "
                "Specify individual files."
            )

        # canonical POSIX path（run-relative、`.`/`..` なし）
        canonical = resolved_file.relative_to(resolved_run).as_posix()

        # UTF-8 read（non-UTF-8 / binary は拒否）
        try:
            content = resolved_file.read_text(encoding=self.ENCODING)
        except UnicodeDecodeError as exc:
            raise SnapshotCaptureError(
                f"non-UTF-8 or binary content is not supported in v1: '{rel_path}'. "
                f"Encoding error: {exc}"
            ) from exc

        return canonical, content
