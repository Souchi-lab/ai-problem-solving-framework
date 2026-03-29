"""
tests/test_assignment_service.py

AssignmentService の model-assignment.md パースと provider 生成を検証する。
"""

import pytest
from pathlib import Path
from unittest.mock import patch

from apsf.legacy.orchestration.assignment_service import AssignmentService
from apsf.core.domain.models import Role, ProviderType
from apsf.legacy.config.settings import Settings


@pytest.fixture
def settings() -> Settings:
    """テスト用設定（API キーはダミー）"""
    s = Settings()
    s.openai_api_key = "sk-test-openai"
    s.anthropic_api_key = "sk-ant-test"
    s.gemini_api_key = "AIza-test"
    return s


@pytest.fixture
def service(settings: Settings) -> AssignmentService:
    return AssignmentService(settings=settings)


SAMPLE_ASSIGNMENT_MD = """\
# Model Assignment

## Run Name
2026-03-15_sochi-blocks_sns-post-template

## Role Assignments

| Role | Provider | Model | Human? | Notes |
|---|---|---|---|---|
| Planner | openai | gpt-4o | ✅ | human + AI |
| JuniorBuilder | gemini | gemini-2.0-flash | - | speed first |
| Builder | anthropic | claude-sonnet-4-6 | - | high quality |
| Critic | openai | gpt-4o | - | different from Builder |
| Judge | | | ✅ | human only |
"""


def test_parse_assignments_roles(tmp_path: Path, service: AssignmentService) -> None:
    """アサインファイルから正しく role が読み込まれること"""
    path = tmp_path / "model-assignment.md"
    path.write_text(SAMPLE_ASSIGNMENT_MD, encoding="utf-8")
    run_dir = tmp_path
    context = service.load_from_file(path, run_dir)

    roles = [a.role for a in context.model_assignments]
    assert Role.PLANNER in roles
    assert Role.JUNIOR_BUILDER in roles
    assert Role.BUILDER in roles
    assert Role.CRITIC in roles
    assert Role.JUDGE in roles


def test_parse_builder_assignment(tmp_path: Path, service: AssignmentService) -> None:
    """Builder が Anthropic + 正しいモデルでアサインされること"""
    path = tmp_path / "model-assignment.md"
    path.write_text(SAMPLE_ASSIGNMENT_MD, encoding="utf-8")
    context = service.load_from_file(path, tmp_path)

    builder = context.get_model_assignment(Role.BUILDER)
    assert builder is not None
    assert builder.provider == ProviderType.ANTHROPIC
    assert builder.model == "claude-sonnet-4-6"
    assert builder.is_human is False


def test_parse_judge_is_human(tmp_path: Path, service: AssignmentService) -> None:
    """Judge が人間アサインとして認識されること"""
    path = tmp_path / "model-assignment.md"
    path.write_text(SAMPLE_ASSIGNMENT_MD, encoding="utf-8")
    context = service.load_from_file(path, tmp_path)

    judge = context.get_model_assignment(Role.JUDGE)
    assert judge is not None
    assert judge.is_human is True


def test_create_provider_anthropic(tmp_path: Path, service: AssignmentService) -> None:
    """Builder アサインから AnthropicProvider が生成されること"""
    from apsf.legacy.providers.anthropic_provider import AnthropicProvider

    path = tmp_path / "model-assignment.md"
    path.write_text(SAMPLE_ASSIGNMENT_MD, encoding="utf-8")
    context = service.load_from_file(path, tmp_path)

    provider = service.create_provider(context, Role.BUILDER)
    assert isinstance(provider, AnthropicProvider)
    assert provider.model == "claude-sonnet-4-6"


def test_create_provider_human_returns_none(tmp_path: Path, service: AssignmentService) -> None:
    """人間アサインの role は provider が None を返すこと"""
    path = tmp_path / "model-assignment.md"
    path.write_text(SAMPLE_ASSIGNMENT_MD, encoding="utf-8")
    context = service.load_from_file(path, tmp_path)

    provider = service.create_provider(context, Role.JUDGE)
    assert provider is None


def test_load_missing_file_returns_empty_context(
    tmp_path: Path, service: AssignmentService
) -> None:
    """model-assignment.md が存在しない場合も RunContext が返ること"""
    path = tmp_path / "model-assignment.md"  # 存在しない
    context = service.load_from_file(path, tmp_path)
    assert context.model_assignments == []


def test_run_context_case_key_and_topic() -> None:
    """RunContext の case_key / topic が正しく抽出されること"""
    from apsf.core.domain.models import RunContext
    ctx = RunContext(
        run_name="2026-03-15_sochi-blocks_sns-post-template",
        run_dir=Path("."),
    )
    assert ctx.case_key == "sochi-blocks"
    assert ctx.topic == "sns-post-template"
