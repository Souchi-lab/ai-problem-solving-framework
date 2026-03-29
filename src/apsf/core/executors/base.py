"""
BaseExecutor - すべての executor が守るべき共通インターフェース

設計前提:
- executor は「どうやって実行するか」だけを責務にする
- agent の「何をするか」(role) とは切り離す
- execute() が唯一の共通インターフェース
- CLI / Human / 将来 API の切り替えをここで吸収する
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from ..domain.models import ExecutionType


@dataclass
class ExecuteRequest:
    """
    executor に投げるリクエスト。Executor 共通の形。
    """

    prompt: str
    system: str = ""
    input_files: list[Path] = field(default_factory=list)
    working_dir: Optional[Path] = None
    dry_run: bool = False


@dataclass
class ExecuteResponse:
    """
    executor からの応答。Executor 共通の形。
    """

    content: str
    execution_type: ExecutionType
    success: bool
    dry_run: bool = False
    raw: Optional[str] = field(default=None, repr=False)


class ExecutorError(Exception):
    """executor 側の基底エラー。"""


class BaseExecutor(ABC):
    """
    すべての executor の基底クラス。
    実装クラスは execute() を実装するだけでよい。
    role / agent との結合は持たない。
    """

    @property
    @abstractmethod
    def execution_type(self) -> ExecutionType:
        """この executor の execution type を返す。"""
        ...

    @abstractmethod
    def execute(self, request: ExecuteRequest) -> ExecuteResponse:
        """
        リクエストを実行して結果を返す。
        """
        ...

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(type={self.execution_type})"
