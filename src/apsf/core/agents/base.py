"""
BaseAgent - すべての agent の共通インターフェース

設計前提:
- agent は「何をするか」(role) を表現し、「どうやって実行するか」(executor) は持ち込まない
- executor を差し替えても agent のコードは変わらない
- run() が唯一の共通インターフェース

v0.1 前提: provider ではなく executor に切り替え済み
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from ..domain.models import Role, RunContext, StepResult
from ..executors.base import BaseExecutor
from ..storage.artifact_repository import ArtifactRepository


class AgentError(Exception):
    """agent 側の基底エラー。"""


class BaseAgent(ABC):
    """
    すべての agent の基底クラス。
    role と executor を保持し、run() で成果物ファイルを出力する。
    executor を切り替えることで同じ role を CLI / Human / 将来 API で実行できる。
    """

    def __init__(self, role: Role, executor: BaseExecutor):
        self._role = role
        self._executor = executor
        self._artifact_repo = ArtifactRepository()

    @property
    def role(self) -> Role:
        return self._role

    @property
    def executor(self) -> BaseExecutor:
        return self._executor

    @abstractmethod
    def run(self, context: RunContext) -> StepResult:
        """
        このステップを実行して成果物ファイルを出力する。
        """
        ...

    def _read_file(self, path: Path) -> str:
        """ファイルを読み込む。存在しない場合は空文字を返す。"""
        if path.exists():
            return path.read_text(encoding="utf-8")
        return ""

    def _write_file(self, path: Path, content: str) -> None:
        """ファイルに書き込む。ArtifactRepository 経由で safe write する。"""
        self._artifact_repo.write(path, content)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(role={self._role}, executor={self._executor})"
