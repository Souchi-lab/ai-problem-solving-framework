"""
BaseExecutor — すべての executor が実装する共通インターフェース

設計原則:
- executor は「どうやって実行するか」だけを担当する
- agent の「何をするか（role）」は知らない
- execute() が唯一の外部向けインターフェース
- CLI / Human / 将来 API の切り替えはここを通じて行う
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
    executor に渡すリクエスト。executor 共通の形式。

    prompt: AI または人間に渡すメイン指示
    system: システムプロンプト（CLI ツールが対応している場合）
    input_files: 参照するファイルのリスト（context として渡す）
    working_dir: 実行ディレクトリ（workspace に対応）
    dry_run: True の場合、実際には実行せず実行内容だけを返す
    """

    prompt: str
    system: str = ""
    input_files: list[Path] = field(default_factory=list)
    working_dir: Optional[Path] = None
    dry_run: bool = False


@dataclass
class ExecuteResponse:
    """
    executor からの返答。executor 共通の形式。

    content: 生成されたテキスト（または手動実行指示）
    execution_type: 実際に使われた execution type
    success: 実行が成功したか
    dry_run: dry-run モードで実行されたか
    raw: デバッグ用の生出力
    """

    content: str
    execution_type: ExecutionType
    success: bool
    dry_run: bool = False
    raw: Optional[str] = field(default=None, repr=False)


class ExecutorError(Exception):
    """executor 層の基底例外"""
    pass


class BaseExecutor(ABC):
    """
    すべての executor の基底クラス。

    実装クラスは execute() を実装するだけでよい。
    role / agent との依存は持たない。

    CLIExecutor:    subprocess でローカル CLI ツールを呼ぶ
    HumanExecutor:  手動実行指示を返す
    APIExecutor:    将来の API 呼び出し（v0.2+）
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

        dry_run=True の場合は実際には実行せず、
        「何が実行されるか」の説明だけを返す。
        """
        ...

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(type={self.execution_type})"
