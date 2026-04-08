"""
MarkdownRepository — Markdown ファイルの読み書き補助

agent 間の共通言語は Markdown ファイル。
このクラスがその read/write を一元管理する。
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from ...core.storage.artifact_repository import ArtifactRepository


class MarkdownRepository:
    """
    Markdown ファイルの読み書き・存在確認を担当する。

    使用例:
        repo = MarkdownRepository(base_dir=Path("runs/2026-03-15_sochi-blocks_sns-post-template"))
        content = repo.read("goal.md")
        repo.write("plan.md", "# Plan\n...")
    """

    def __init__(self, base_dir: Path):
        self._base = base_dir
        self._artifact_repo = ArtifactRepository()

    @property
    def base_dir(self) -> Path:
        return self._base

    def read(self, filename: str) -> str:
        """
        ファイルを読み込む。存在しない場合は空文字を返す。
        """
        path = self._base / filename
        if path.exists():
            return path.read_text(encoding="utf-8")
        return ""

    def write(self, filename: str, content: str) -> Path:
        """
        ファイルを書き込む。親ディレクトリがない場合は作成する。
        書き込んだファイルの Path を返す。
        """
        path = self._base / filename
        return self._artifact_repo.write(path, content)

    def exists(self, filename: str) -> bool:
        """ファイルが存在するかどうかを返す。"""
        return (self._base / filename).exists()

    def is_empty(self, filename: str) -> bool:
        """ファイルが存在しないか、中身が空白のみの場合 True を返す。"""
        content = self.read(filename)
        return not content.strip()

    def list_files(self) -> list[str]:
        """base_dir 直下のファイル名一覧を返す（サブディレクトリは除く）。"""
        if not self._base.exists():
            return []
        return [f.name for f in sorted(self._base.iterdir()) if f.is_file()]

    def read_optional(self, filename: str) -> Optional[str]:
        """ファイルが存在する場合はその内容を返す。存在しない場合は None を返す。"""
        path = self._base / filename
        if path.exists():
            return path.read_text(encoding="utf-8")
        return None

    def ensure_dir(self) -> Path:
        """base_dir が存在しない場合は作成する。"""
        self._base.mkdir(parents=True, exist_ok=True)
        return self._base
