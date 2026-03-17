"""
Domain Models — フレームワークの中核データ構造

設計原則:
- Role と ExecutionType は常に分離する
- "ClaudeBuilder" のような密結合は作らない
- ExecutionAssignment が「どうやって実行するか」を表現する
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
    """問題解決ループにおける役割定義。executor とは独立して定義する。"""

    PLANNER = "planner"
    JUNIOR_BUILDER = "junior_builder"
    BUILDER = "builder"
    CRITIC = "critic"
    JUDGE = "judge"
    HUMAN = "human"  # 人間が担当することを明示するための値


class ExecutionType(str, Enum):
    """
    実行手段の種別。role とは独立して定義する。

    v0.1 では cli / human が主要。future-api は将来拡張ポイント。
    """

    CLI = "cli"          # ローカル CLI ツール（Claude Code, Gemini CLI 等）
    HUMAN = "human"      # 人間が手動で実行
    FUTURE_API = "future-api"  # 将来の API executor（v0.2+）


class ProviderType(str, Enum):
    """
    AI プロバイダーの種別。future-api executor で使用する。

    v0.1 では使用しないが、将来の API 対応のために定義しておく。
    """

    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"
    HUMAN = "human"


@dataclass
class ExecutionAssignment:
    """
    1 run における role → execution type / tool の割り当て。

    execution-assignment.md の Python 表現。
    「どうやって実行するか」を定義する。v0.1 の中心的な設定。

    例:
        ExecutionAssignment(role=Role.BUILDER, execution_type=ExecutionType.CLI,
                            tool="claude", workspace="workspaces/builder")
        ExecutionAssignment(role=Role.JUDGE, execution_type=ExecutionType.HUMAN,
                            workspace="workspaces/judge")
    """

    role: Role
    execution_type: ExecutionType
    tool: str = ""               # CLI ツール名 (e.g. "claude", "gemini-cli")
    workspace: str = ""          # 作業ディレクトリ (e.g. "workspaces/builder")
    command: str = ""            # 実行コマンド例（dry-run 表示用）
    manual_procedure: str = ""   # 手動実行の場合の手順
    notes: str = ""


@dataclass
class ModelAssignment:
    """
    1 run における role → provider / model の割り当て。

    model-assignment.md の Python 表現。
    将来 future-api executor で使用する。v0.1 では参考情報として扱う。
    """

    role: Role
    provider: ProviderType
    model: str = ""
    is_human: bool = False
    notes: str = ""


@dataclass
class RunContext:
    """
    1 run のコンテキスト全体。

    run ディレクトリのメタ情報と execution 割り当てを保持する。
    """

    run_name: str  # e.g. "2026-03-15_sochi-blocks_sns-post-template"
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
    role 間の受け渡し情報。

    handoff.md の Python 表現。
    モデルを分けるほど handoff の質が問題解決の品質に直結する。
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
    """
    1 ステップの実行結果。pipeline が各 step の結果を収集するために使う。
    """

    step: str
    role: Role
    success: bool
    output_path: Optional[Path] = None
    execution_type: Optional[ExecutionType] = None
    notes: str = ""
    error: Optional[str] = None
