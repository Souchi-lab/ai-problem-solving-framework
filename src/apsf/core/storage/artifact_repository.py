"""
ArtifactRepository — canonical artifact の安全な書き込み口

すべての canonical artifact 書き込みはこのクラスを経由する。
raw write_text() 直書きの代替として、以下を提供する:

- temp write + atomic rename (os.replace)
- single-writer lock (.lock ファイルによる排他)
- ownership check (writing_role が指定さ���た場合)

使用例:
    from apsf.core.storage.artifact_repository import ArtifactRepository

    # role なし（後方互換 — ownership check はスキップ）
    repo = ArtifactRepository()
    repo.write(Path("runs/my-run/plan.md"), "# Plan\\n...")

    # role あり（ownership check 有効）
    repo = ArtifactRepository(writing_role="Builder")
    repo.write(Path("runs/my-run/build.md"), "# Build\\n...")
"""

from __future__ import annotations

import os
import uuid
from pathlib import Path
from typing import Optional


class FileLockError(Exception):
    """別のプロセスが同じファイルに書き込み中のときに raise される。"""


class OwnershipViolationError(Exception):
    """cross-role overwrite が検出されたときに raise される。"""


class ArtifactRepository:
    """
    canonical artifact の安全な書き込み・読み込みを担当する。

    書き込みは temp write → lock 取得 → atomic rename → lock 解放 の順で行う。
    lock ファイルが既に存在する場合は FileLockError を raise する。

    writing_role が指定された場合、ownership policy に違反す��書き込みは
    OwnershipViolationError を raise する。
    writing_role が None の場合は ownership check をスキップする（後方互換）。
    """

    def __init__(
        self,
        writing_role: Optional[str] = None,
        run_dir: Optional["Path"] = None,
    ) -> None:
        self._writing_role = writing_role
        self._run_dir = run_dir

    def write(self, path: Path, content: str) -> Path:
        """
        canonical artifact を safe write で保存する。

        1. ownership check（writing_role が指定されている場合）
        2. .tmp ファイルに書き込む
        3. .lock ファイルを排他作成 (mode='x') で取得
        4. os.replace() でアトミック rename
        5. finally で .lock ファイルを解放

        Args:
            path:    書き込み先の Path
            content: 書き込む文字列

        Returns:
            書き込んだファイルの Path

        Raises:
            OwnershipViolationError: cross-role overwrite が検出された場合
            FileLockError:           同じファイルへの書き込みが既に進行中の場合
        """
        self._check_ownership(path)

        path.parent.mkdir(parents=True, exist_ok=True)

        # ユニークな tmp パスを使うことで複数ライターの衝突を防ぐ
        tmp_path = path.with_name(f"{path.stem}.{uuid.uuid4().hex[:8]}.tmp")
        lock_path = path.with_suffix(".lock")

        # temp ファイルに書き込む
        tmp_path.write_text(content, encoding="utf-8")

        # lock 取得 → rename → lock 解放
        # owned_lock: このスレッド/プロセスが lock を取得した場合のみ True
        lock_file = None
        owned_lock = False
        try:
            try:
                lock_file = open(lock_path, "x", encoding="utf-8")  # noqa: WPS515
                owned_lock = True
            except FileExistsError:
                tmp_path.unlink(missing_ok=True)
                raise FileLockError(
                    f"Cannot write {path.name}: lock file exists ({lock_path}). "
                    "Another writer may be active."
                )
            os.replace(tmp_path, path)
        finally:
            if lock_file is not None:
                lock_file.close()
            # 自分が取得した lock のみ解放する
            if owned_lock:
                lock_path.unlink(missing_ok=True)

        # manifest 更新: writing_role と run_dir が両方設定されている場合のみ
        if self._writing_role is not None and self._run_dir is not None:
            self._update_manifest(path, content)

        return path

    def _update_manifest(self, path: Path, content: str) -> None:
        """
        artifact_manifest.json を更新する。
        lazy import で循環依存を回避する。
        writing_role と run_dir が両方 set の場合のみ呼ばれる。
        """
        # lazy import: ManifestRepository は ArtifactRepository(writing_role=None) を使うため
        # 再帰的な manifest 更新は発生しない
        from ..manifest.manifest_repository import ManifestRepository
        from ..state.run_state_repository import RunStateRepository

        run_id = self._run_dir.name  # type: ignore[union-attr]
        state = RunStateRepository(self._run_dir).load()
        source_handoff_id = state.active_handoff_id if state is not None else ""

        ManifestRepository(self._run_dir).update_entry(
            artifact_name=path.name,
            writing_role=self._writing_role,  # type: ignore[arg-type]
            content=content,
            run_id=run_id,
            source_handoff_id=source_handoff_id,
        )

    def read(self, path: Path) -> str:
        """
        ファイルを読み込む。存在しない場合は空文字を返す。

        Args:
            path: 読み込む Path

        Returns:
            ファイルの内容。存在しない場合は空文字。
        """
        if path.exists():
            return path.read_text(encoding="utf-8")
        return ""

    def _check_ownership(self, path: Path) -> None:
        """
        writing_role が指定されている場合、ownership policy を確認する。
        cross-role overwrite（HARD_STOP）が検出された場合は OwnershipViolationError を raise する。
        writing_role が None の場合はスキップ（後方互換）。
        """
        if self._writing_role is None:
            return

        from ..domain.ownership import is_allowed_writer

        if not is_allowed_writer(self._writing_role, path.name):
            from ..domain.ownership import get_policy
            policy = get_policy(path.name)
            owner = policy.owner_role if policy else "unknown"
            allowed = policy.allowed_writers if policy else ()
            raise OwnershipViolationError(
                f"[Ownership] {self._writing_role} is not allowed to write {path.name}. "
                f"owner: {owner}, allowed_writers: {allowed}. "
                "Use ArtifactRepository(writing_role=None) to bypass (not recommended), "
                "or pass --force with --force-reason via CLI."
            )
