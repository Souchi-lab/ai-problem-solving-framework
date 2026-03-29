"""
AssignmentService — model-assignment.md の解析と role 割り当て管理

model-assignment.md の Python 表現を扱う。
run ごとに role → provider/model の割り当てを読み込み、
AssignmentService が provider を生成する責務を持つ。
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

from ..config.settings import Settings
from ..core.domain.models import ModelAssignment, ProviderType, Role, RunContext
from ..core.providers.base import BaseProvider
from ..providers.anthropic_provider import AnthropicProvider
from ..providers.gemini_provider import GeminiProvider
from ..providers.openai_provider import OpenAIProvider


class AssignmentService:
    """
    model-assignment.md を読み込んで provider を生成するサービス。

    使用例:
        service = AssignmentService(settings=get_settings())
        context = service.load_from_file(run_dir / "model-assignment.md", run_dir)
        provider = service.create_provider(context, Role.BUILDER)
    """

    def __init__(self, settings: Settings):
        self._settings = settings

    def load_from_file(self, assignment_path: Path, run_dir: Path) -> RunContext:
        """
        model-assignment.md を読み込んで RunContext を生成する。

        v0.1 では簡易パーサー。
        TODO(v0.2): YAML front matter や構造化パーサーに移行する。
        """
        run_name = run_dir.name
        context = RunContext(run_name=run_name, run_dir=run_dir)

        if not assignment_path.exists():
            return context  # アサインなしで RunContext を返す

        content = assignment_path.read_text(encoding="utf-8")
        assignments = self._parse_assignments(content)
        context.model_assignments = assignments
        return context

    def _parse_assignments(self, content: str) -> list[ModelAssignment]:
        """
        model-assignment.md のテーブル行を簡易パースする。

        テーブル形式の例:
        | Builder | anthropic | claude-sonnet-4-6 | - | ... |
        | Critic  | openai    | gpt-4o            | - | ... |
        | Judge   |           |                   | ✅ | ... |
        """
        assignments: list[ModelAssignment] = []

        role_map = {
            "planner": Role.PLANNER,
            "juniorbuilder": Role.JUNIOR_BUILDER,
            "junior_builder": Role.JUNIOR_BUILDER,
            "builder": Role.BUILDER,
            "critic": Role.CRITIC,
            "judge": Role.JUDGE,
        }

        provider_map = {
            "openai": ProviderType.OPENAI,
            "anthropic": ProviderType.ANTHROPIC,
            "gemini": ProviderType.GEMINI,
            "human": ProviderType.HUMAN,
        }

        for line in content.splitlines():
            if not line.startswith("|") or "---" in line:
                continue

            cells = [c.strip() for c in line.strip("|").split("|")]
            if len(cells) < 3:
                continue

            role_str = cells[0].lower().replace(" ", "")
            role = role_map.get(role_str)
            if role is None:
                continue

            provider_str = cells[1].lower().strip()
            provider_type = provider_map.get(provider_str, ProviderType.HUMAN)

            model = cells[2].strip() if len(cells) > 2 else ""
            is_human = "✅" in (cells[3] if len(cells) > 3 else "")

            assignments.append(
                ModelAssignment(
                    role=role,
                    provider=provider_type,
                    model=model,
                    is_human=is_human,
                )
            )

        return assignments

    def create_provider(self, context: RunContext, role: Role) -> Optional[BaseProvider]:
        """
        RunContext から指定 role の provider を生成する。
        アサインが見つからない場合は None を返す。
        """
        assignment = context.get_model_assignment(role)
        if assignment is None:
            return None

        if assignment.is_human or assignment.provider == ProviderType.HUMAN:
            return None  # 人間担当の場合は provider を作成しない

        return self._create_provider_instance(assignment)

    def _create_provider_instance(self, assignment: ModelAssignment) -> BaseProvider:
        """ModelAssignment から具体的な provider インスタンスを生成する。"""
        if assignment.provider == ProviderType.ANTHROPIC:
            return AnthropicProvider(
                model=assignment.model or self._settings.default_anthropic_model,
                api_key=self._settings.anthropic_api_key,
            )
        elif assignment.provider == ProviderType.OPENAI:
            return OpenAIProvider(
                model=assignment.model or self._settings.default_openai_model,
                api_key=self._settings.openai_api_key,
            )
        elif assignment.provider == ProviderType.GEMINI:
            return GeminiProvider(
                model=assignment.model or self._settings.default_gemini_model,
                api_key=self._settings.gemini_api_key,
            )
        else:
            raise ValueError(f"Unknown provider type: {assignment.provider}")
