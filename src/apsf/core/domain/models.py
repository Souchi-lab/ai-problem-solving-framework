"""
Domain Models - framework/workspace の中核データ構造

設計前提:
- Role と ExecutionType は常に分離する
- "ClaudeBuilder" のような混合名詞は作らない
- ExecutionAssignment が「どのように実行するか」を表現する
- ModelAssignment が「どのモデルを使うか」を表現する（将来 API 用）
- RunContext が 1 run の全コンテキストを保持する
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional


class Role(str, Enum):
    """問題解決ループにおける役割定義。Executor とは独立して定義する。"""

    PLANNER = "planner"
    JUNIOR_BUILDER = "junior_builder"
    BUILDER = "builder"
    CRITIC = "critic"
    JUDGE = "judge"
    HUMAN = "human"  # 人間が直接介入することを表現するための補助


class ExecutionType(str, Enum):
    """
    実行形態の定義。Role とは独立して定義する。
    v0.1 では cli / human が中心で、future-api は将来拡張ポイント。
    """

    CLI = "cli"
    HUMAN = "human"
    FUTURE_API = "future-api"


class ProviderType(str, Enum):
    """
    AI プロバイダーの定義。future-api executor で利用する。
    v0.1 では利用しないが、将来の API 対応のために定義しておく。
    """

    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"
    HUMAN = "human"


@dataclass
class ExecutionAssignment:
    """
    1 run における role → execution type / tool の割当て。
    execution-assignment.md の Python 表現。
    「どうやって実行するか」を表現する。v0.1 の中核となる設計。
    """

    role: Role
    execution_type: ExecutionType
    tool: str = ""
    workspace: str = ""
    command: str = ""
    manual_procedure: str = ""
    notes: str = ""


@dataclass
class ModelAssignment:
    """
    1 run における role → provider / model の割当て。
    model-assignment.md の Python 表現。
    将来 future-api executor で利用する。v0.1 では補助情報として扱う。
    """

    role: Role
    provider: ProviderType
    model: str = ""
    is_human: bool = False
    notes: str = ""


@dataclass
class RunContext:
    """
    1 run のコンテキスト情報。
    run ディレクトリのメタ情報と execution 割当てを保持する。
    """

    run_name: str
    run_dir: Path
    execution_assignments: list[ExecutionAssignment] = field(default_factory=list)
    model_assignments: list[ModelAssignment] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)

    @property
    def case_key(self) -> str:
        parts = self.run_name.split("_", maxsplit=2)
        return parts[1] if len(parts) >= 3 else ""

    @property
    def topic(self) -> str:
        parts = self.run_name.split("_", maxsplit=2)
        return parts[2] if len(parts) >= 3 else ""

    def get_execution_assignment(self, role: Role) -> Optional[ExecutionAssignment]:
        for a in self.execution_assignments:
            if a.role == role:
                return a
        return None

    def get_model_assignment(self, role: Role) -> Optional[ModelAssignment]:
        for a in self.model_assignments:
            if a.role == role:
                return a
        return None


@dataclass
class Handoff:
    """
    role 間の引き継ぎ情報。
    handoff.md の Python 表現。
    モデルを替えるほど handoff の質が問題になるため、明示構造として保持する。
    """

    from_role: Role
    to_role: Role
    current_state: str
    decided: list[str] = field(default_factory=list)
    open_items: list[str] = field(default_factory=list)
    next_actions: list[str] = field(default_factory=list)
    constraints: list[str] = field(default_factory=list)
    notes: str = ""


@dataclass
class StepResult:
    """1 ステップの実行結果。Pipeline が各 step の結果を保持するために使う。"""

    step: str
    role: Role
    success: bool
    output_path: Optional[Path] = None
    execution_type: Optional[ExecutionType] = None
    notes: str = ""
    error: Optional[str] = None
