"""
AssignmentService - parse model-assignment.md and resolve provider/model for a role.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from ..config.settings import Settings
from ...core.domain.models import ModelAssignment, ProviderType, Role, RunContext
from ...core.providers.base import BaseProvider
from ..providers.anthropic_provider import AnthropicProvider
from ..providers.gemini_provider import GeminiProvider
from ..providers.openai_provider import OpenAIProvider


_ROLE_DISPLAY: dict[Role, str] = {
    Role.PLANNER: "Planner",
    Role.BUILDER: "Builder",
    Role.CRITIC: "Critic",
    Role.JUDGE: "Judge",
    Role.JUNIOR_BUILDER: "JuniorBuilder",
}


@dataclass(frozen=True)
class ResolvedModelSelection:
    role: Role
    provider: Optional[ProviderType]
    model: str
    mode: str  # explicit | default | human | auto | unset
    reason: str
    is_human: bool = False


class AssignmentService:
    """
    Load model-assignment.md and resolve a provider for a role.
    """

    def __init__(self, settings: Settings):
        self._settings = settings

    def load_from_file(self, assignment_path: Path, run_dir: Path) -> RunContext:
        run_name = run_dir.name
        context = RunContext(run_name=run_name, run_dir=run_dir)

        if not assignment_path.exists():
            return context

        content = assignment_path.read_text(encoding="utf-8")
        context.model_assignments = self._parse_assignments(content)
        return context

    def _parse_assignments(self, content: str) -> list[ModelAssignment]:
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

    def resolve_assignment(
        self, context: RunContext, role: Role, execution_type: str = ""
    ) -> ResolvedModelSelection:
        assignment = context.get_model_assignment(role)
        if assignment is not None:
            if self._settings.is_provider_disabled(assignment.provider.value):
                return ResolvedModelSelection(
                    role=role,
                    provider=None,
                    model="",
                    mode="disabled",
                    reason=(
                        f"model-assignment.md selects disabled provider "
                        f"{assignment.provider.value} for {role.value}"
                    ),
                )
            if assignment.is_human or assignment.provider == ProviderType.HUMAN:
                return ResolvedModelSelection(
                    role=role,
                    provider=None,
                    model="",
                    mode="human",
                    reason=f"model-assignment.md marks {role.value} as human-owned",
                    is_human=True,
                )

            if assignment.model.strip():
                model = assignment.model.strip()
                return ResolvedModelSelection(
                    role=role,
                    provider=assignment.provider,
                    model=model,
                    mode="explicit",
                    reason=f"model-assignment.md explicitly selects {assignment.provider.value} / {model} for {role.value}",
                )

            return ResolvedModelSelection(
                role=role,
                provider=assignment.provider,
                model=self._default_model_for_provider(assignment.provider),
                mode="default",
                reason=f"model-assignment.md selects {assignment.provider.value} for {role.value}; using provider default model",
            )

        # Transport-aware: CLI execution means the wrapper tool owns provider/model selection
        if execution_type == "cli":
            return ResolvedModelSelection(
                role=role,
                provider=None,
                model="",
                mode="wrapper-backed",
                reason=f"execution is cli-backed for {role.value}; provider/model is determined by the wrapper tool, not APSF",
            )

        # Human execution: model selection is the operator's responsibility
        if execution_type == "human":
            return ResolvedModelSelection(
                role=role,
                provider=None,
                model="",
                mode="unset",
                reason=f"execution is human for {role.value}; model selection is operator's responsibility",
            )

        # Provider/API execution: auto-select first configured provider
        for provider in (ProviderType.ANTHROPIC, ProviderType.OPENAI, ProviderType.GEMINI):
            if self._settings.has_api_key(provider.value):
                return ResolvedModelSelection(
                    role=role,
                    provider=provider,
                    model=self._default_model_for_provider(provider),
                    mode="auto",
                    reason=f"no explicit model assignment for {role.value}; auto-selected first configured provider {provider.value}",
                )

        return ResolvedModelSelection(
            role=role,
            provider=None,
            model="",
            mode="unset",
            reason=f"no explicit model assignment for {role.value} and no configured API provider is available",
        )

    def write_back_auto_selection(
        self, run_dir: Path, role: Role, resolved: ResolvedModelSelection
    ) -> bool:
        """
        auto-selected provider/model を model-assignment.md に write-back する。

        Write-back 条件:
        - resolved.mode == "auto"
        - 対象 role の行が model-assignment.md に未記録

        Returns True if wrote, False if skipped (non-auto mode / explicit already exists).
        """
        if resolved.mode != "auto" or resolved.provider is None:
            return False

        assignment_path = run_dir / "model-assignment.md"

        # 既存の explicit entry があれば上書きしない
        if assignment_path.exists():
            existing_context = self.load_from_file(assignment_path, run_dir)
            if existing_context.get_model_assignment(role) is not None:
                return False

        role_display = _ROLE_DISPLAY.get(role, role.value.title())
        new_row = (
            f"| {role_display} | {resolved.provider.value} | {resolved.model}"
            f" | no | auto-selected by apsf act |\n"
        )

        if assignment_path.exists():
            content = assignment_path.read_text(encoding="utf-8")
            if not content.endswith("\n"):
                content += "\n"
            content += new_row
        else:
            content = (
                "# Model Assignment\n\n"
                "| Role | Provider | Model | Human? | Notes |\n"
                "|---|---|---|---|---|\n"
                f"{new_row}"
            )

        assignment_path.write_text(content, encoding="utf-8")
        return True

    def create_provider(
        self, context: RunContext, role: Role, execution_type: str = ""
    ) -> Optional[BaseProvider]:
        resolved = self.resolve_assignment(context, role, execution_type=execution_type)
        if resolved.provider is None or resolved.is_human:
            return None

        return self._create_provider_instance(
            ModelAssignment(
                role=role,
                provider=resolved.provider,
                model=resolved.model,
                is_human=resolved.is_human,
            )
        )

    def _default_model_for_provider(self, provider: ProviderType) -> str:
        return {
            ProviderType.ANTHROPIC: self._settings.default_anthropic_model,
            ProviderType.OPENAI: self._settings.default_openai_model,
            ProviderType.GEMINI: self._settings.default_gemini_model,
        }.get(provider, "")

    def _create_provider_instance(self, assignment: ModelAssignment) -> BaseProvider:
        if self._settings.is_provider_disabled(assignment.provider.value):
            raise ValueError(f"Provider is disabled: {assignment.provider.value}")
        if assignment.provider == ProviderType.ANTHROPIC:
            return AnthropicProvider(
                model=assignment.model or self._settings.default_anthropic_model,
                api_key=self._settings.anthropic_api_key,
            )
        if assignment.provider == ProviderType.OPENAI:
            return OpenAIProvider(
                model=assignment.model or self._settings.default_openai_model,
                api_key=self._settings.openai_api_key,
            )
        if assignment.provider == ProviderType.GEMINI:
            return GeminiProvider(
                model=assignment.model or self._settings.default_gemini_model,
                api_key=self._settings.gemini_api_key,
            )
        raise ValueError(f"Unknown provider type: {assignment.provider}")
