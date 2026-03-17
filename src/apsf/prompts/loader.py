"""
PromptLoader — framework/templates/ や runs/ 内のファイルを読み込む補助クラス

将来的なプロンプトテンプレート拡張（Jinja2 等）を見越した構造にしているが、
v0.1 では素朴なファイル読み込みに留める。
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional


class PromptLoader:
    """
    Markdown ファイルをプロンプトとして読み込む。

    使用例:
        loader = PromptLoader(framework_root=Path("."))
        template = loader.load_template("plan.md")
        run_file = loader.load_run_file("2026-03-15_sochi-blocks_sns-post-template", "goal.md")
    """

    def __init__(self, framework_root: Path):
        self._root = framework_root

    @property
    def templates_dir(self) -> Path:
        return self._root / "framework" / "templates"

    @property
    def runs_dir(self) -> Path:
        return self._root / "runs"

    def load_template(self, filename: str) -> str:
        """
        framework/templates/ からテンプレートファイルを読み込む。
        存在しない場合は空文字を返す。
        """
        path = self.templates_dir / filename
        if path.exists():
            return path.read_text(encoding="utf-8")
        return ""

    def load_run_file(self, run_name: str, filename: str) -> str:
        """
        runs/<run_name>/<filename> を読み込む。
        存在しない場合は空文字を返す。
        """
        path = self.runs_dir / run_name / filename
        if path.exists():
            return path.read_text(encoding="utf-8")
        return ""

    def load_agent_definition(self, agent_name: str) -> str:
        """
        framework/agents/<agent_name>.md を読み込む。
        agent の責務・プロンプト草案を参照するために使用する。
        """
        path = self._root / "framework" / "agents" / f"{agent_name}.md"
        if path.exists():
            return path.read_text(encoding="utf-8")
        return ""

    def list_run_files(self, run_name: str) -> list[str]:
        """指定 run に存在するファイル名の一覧を返す"""
        run_dir = self.runs_dir / run_name
        if not run_dir.exists():
            return []
        return [f.name for f in sorted(run_dir.iterdir()) if f.is_file()]

    def load_file(self, path: Path) -> Optional[str]:
        """任意パスのファイルを読み込む。存在しない場合は None を返す。"""
        if path.exists():
            return path.read_text(encoding="utf-8")
        return None
