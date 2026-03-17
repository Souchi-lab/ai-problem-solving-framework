"""
BaseAgent — すべての agent の共通インターフェース

設計原則:
- agent は「何をするか（role）」を担当し、「どうやって実行するか（executor）」は知らない
- executor を差し替えても agent のコードは変わらない
- run() が唯一の外部向けインターフェース

v0.1 変更: provider → executor に切り替え
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from ..domain.models import Role, RunContext, StepResult
from ..executors.base import BaseExecutor


class AgentError(Exception):
    """agent 層の基底例外"""
    pass


class BaseAgent(ABC):
    """
    すべての agent の基底クラス。

    role と executor を受け取り、run() で成果物ファイルを生成する。
    executor を差し替えることで同じ role を CLI / Human / 将来 API で実行できる。
    """

    def __init__(self, role: Role, executor: BaseExecutor):
        self._role = role
        self._executor = executor

    @property
    def role(self) -> Role:
        return self._role

    @property
    def executor(self) -> BaseExecutor:
        return self._executor

    @abstractmethod
    def run(self, context: RunContext) -> StepResult:
        """
        このステップを実行して成果物ファイルを生成する。

        Args:
            context: 現在の run コンテキスト（run_dir / assignments 等）

        Returns:
            StepResult: 実行結果（成功/失敗・出力ファイルパス・メモ）
        """
        ...

    def _read_file(self, path: Path) -> str:
        """ファイルを読み込む。存在しない場合は空文字を返す。"""
        if path.exists():
            return path.read_text(encoding="utf-8")
        return ""

    def _write_file(self, path: Path, content: str) -> None:
        """ファイルに書き込む。親ディレクトリがない場合は作成する。"""
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(role={self._role}, executor={self._executor})"
