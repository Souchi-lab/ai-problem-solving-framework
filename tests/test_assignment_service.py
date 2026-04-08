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


def test_resolve_assignment_auto_selects_first_configured_provider(tmp_path: Path, service: AssignmentService) -> None:
    context = service.load_from_file(tmp_path / "model-assignment.md", tmp_path)

    resolved = service.resolve_assignment(context, Role.BUILDER)

    assert resolved.mode == "auto"
    assert resolved.provider == ProviderType.ANTHROPIC
    assert resolved.model == "claude-sonnet-4-6"


def test_create_provider_without_explicit_assignment_uses_auto_selection(tmp_path: Path, service: AssignmentService) -> None:
    from apsf.legacy.providers.anthropic_provider import AnthropicProvider

    context = service.load_from_file(tmp_path / "model-assignment.md", tmp_path)

    provider = service.create_provider(context, Role.BUILDER)

    assert isinstance(provider, AnthropicProvider)
    assert provider.model == "claude-sonnet-4-6"


def test_resolve_assignment_cli_execution_returns_wrapper_backed(tmp_path: Path, service: AssignmentService) -> None:
    context = service.load_from_file(tmp_path / "model-assignment.md", tmp_path)

    resolved = service.resolve_assignment(context, Role.BUILDER, execution_type="cli")

    assert resolved.mode == "wrapper-backed"
    assert resolved.provider is None
    assert resolved.model == ""


def test_resolve_assignment_human_execution_returns_unset(tmp_path: Path, service: AssignmentService) -> None:
    context = service.load_from_file(tmp_path / "model-assignment.md", tmp_path)

    resolved = service.resolve_assignment(context, Role.PLANNER, execution_type="human")

    assert resolved.mode == "unset"
    assert resolved.provider is None


def test_resolve_assignment_explicit_overrides_execution_type(tmp_path: Path, service: AssignmentService) -> None:
    """explicit model-assignment.md は execution_type より優先される"""
    (tmp_path / "model-assignment.md").write_text(
        "| Builder | anthropic | claude-sonnet-4-6 | - | - |\n",
        encoding="utf-8",
    )
    context = service.load_from_file(tmp_path / "model-assignment.md", tmp_path)

    resolved = service.resolve_assignment(context, Role.BUILDER, execution_type="cli")

    assert resolved.mode == "explicit"
    assert resolved.provider == ProviderType.ANTHROPIC


def test_create_provider_cli_execution_returns_none(tmp_path: Path, service: AssignmentService) -> None:
    """cli execution → create_provider は None を返す（wrapper ツールが provider を担う）"""
    context = service.load_from_file(tmp_path / "model-assignment.md", tmp_path)

    provider = service.create_provider(context, Role.BUILDER, execution_type="cli")

    assert provider is None


def test_act_service_raises_for_cli_execution(tmp_path: Path) -> None:
    """_get_provider で cli execution が設定されていれば ActError を出す"""
    from apsf.legacy.orchestration.act_service import ActService, ActError
    from apsf.legacy.orchestration.phase_detector import Phase
    from apsf.legacy.config.settings import get_settings

    (tmp_path / "execution-assignment.md").write_text(
        "| Builder | cli | claude-code | workspaces/builder/ | - |\n",
        encoding="utf-8",
    )
    svc = ActService()
    import pytest
    with pytest.raises(ActError, match="cli execution"):
        svc._get_provider(Phase.BUILD_NEEDED, tmp_path, get_settings())


def test_act_service_raises_for_human_execution(tmp_path: Path) -> None:
    """_get_provider で human execution が設定されていれば ActError を出す"""
    from apsf.legacy.orchestration.act_service import ActService, ActError
    from apsf.legacy.orchestration.phase_detector import Phase
    from apsf.legacy.config.settings import get_settings

    (tmp_path / "execution-assignment.md").write_text(
        "| Planner | human | 手動 | workspaces/planner/ | - |\n",
        encoding="utf-8",
    )
    svc = ActService()
    import pytest
    with pytest.raises(ActError, match="human execution"):
        svc._get_provider(Phase.PLAN_NEEDED, tmp_path, get_settings())


def test_write_back_auto_selection_creates_file(tmp_path: Path, service: AssignmentService) -> None:
    """auto-selected assignment は model-assignment.md を新規作成して書き戻す"""
    from apsf.legacy.orchestration.assignment_service import ResolvedModelSelection

    resolved = ResolvedModelSelection(
        role=Role.BUILDER,
        provider=ProviderType.ANTHROPIC,
        model="claude-sonnet-4-6",
        mode="auto",
        reason="auto-selected",
    )
    wrote = service.write_back_auto_selection(tmp_path, Role.BUILDER, resolved)

    assert wrote is True
    assignment_path = tmp_path / "model-assignment.md"
    assert assignment_path.exists()
    content = assignment_path.read_text(encoding="utf-8")
    assert "Builder" in content
    assert "anthropic" in content
    assert "claude-sonnet-4-6" in content
    assert "auto-selected by apsf act" in content


def test_write_back_auto_selection_appends_to_existing_file(tmp_path: Path, service: AssignmentService) -> None:
    """既存 model-assignment.md に新 role 行を追記する"""
    from apsf.legacy.orchestration.assignment_service import ResolvedModelSelection

    (tmp_path / "model-assignment.md").write_text(
        "# Model Assignment\n\n| Role | Provider | Model | Human? | Notes |\n|---|---|---|---|---|\n"
        "| Planner | openai | gpt-4o | no | manual |\n",
        encoding="utf-8",
    )
    resolved = ResolvedModelSelection(
        role=Role.BUILDER,
        provider=ProviderType.ANTHROPIC,
        model="claude-sonnet-4-6",
        mode="auto",
        reason="auto-selected",
    )
    wrote = service.write_back_auto_selection(tmp_path, Role.BUILDER, resolved)

    assert wrote is True
    content = (tmp_path / "model-assignment.md").read_text(encoding="utf-8")
    assert "Planner" in content  # 既存行が消えていない
    assert "Builder" in content  # 新行が追加された


def test_write_back_auto_selection_skips_if_role_already_exists(tmp_path: Path, service: AssignmentService) -> None:
    """既に role 行がある場合は write-back しない（explicit-wins）"""
    from apsf.legacy.orchestration.assignment_service import ResolvedModelSelection

    (tmp_path / "model-assignment.md").write_text(
        "| Builder | anthropic | claude-opus-4-6 | no | manual |\n",
        encoding="utf-8",
    )
    resolved = ResolvedModelSelection(
        role=Role.BUILDER,
        provider=ProviderType.ANTHROPIC,
        model="claude-sonnet-4-6",
        mode="auto",
        reason="auto-selected",
    )
    wrote = service.write_back_auto_selection(tmp_path, Role.BUILDER, resolved)

    assert wrote is False
    content = (tmp_path / "model-assignment.md").read_text(encoding="utf-8")
    assert "claude-opus-4-6" in content  # 元の行が保たれている


def test_write_back_auto_selection_skips_non_auto_mode(tmp_path: Path, service: AssignmentService) -> None:
    """mode が auto でない場合は write-back しない"""
    from apsf.legacy.orchestration.assignment_service import ResolvedModelSelection

    for mode in ("explicit", "unset", "wrapper-backed", "human"):
        resolved = ResolvedModelSelection(
            role=Role.BUILDER,
            provider=ProviderType.ANTHROPIC if mode == "explicit" else None,
            model="claude-sonnet-4-6" if mode == "explicit" else "",
            mode=mode,
            reason="test",
        )
        wrote = service.write_back_auto_selection(tmp_path, Role.BUILDER, resolved)
        assert wrote is False, f"mode={mode} should not write back"


def test_write_back_then_resolve_returns_explicit(tmp_path: Path, service: AssignmentService) -> None:
    """write-back 後に再解決すると explicit mode になる（durable record として機能する）"""
    from apsf.legacy.orchestration.assignment_service import ResolvedModelSelection

    resolved = ResolvedModelSelection(
        role=Role.BUILDER,
        provider=ProviderType.ANTHROPIC,
        model="claude-sonnet-4-6",
        mode="auto",
        reason="auto-selected",
    )
    service.write_back_auto_selection(tmp_path, Role.BUILDER, resolved)

    context = service.load_from_file(tmp_path / "model-assignment.md", tmp_path)
    re_resolved = service.resolve_assignment(context, Role.BUILDER)

    assert re_resolved.mode == "explicit"
    assert re_resolved.provider == ProviderType.ANTHROPIC
    assert re_resolved.model == "claude-sonnet-4-6"


def test_run_context_case_key_and_topic() -> None:
    """RunContext の case_key / topic が正しく抽出されること"""
    from apsf.core.domain.models import RunContext
    ctx = RunContext(
        run_name="2026-03-15_sochi-blocks_sns-post-template",
        run_dir=Path("."),
    )
    assert ctx.case_key == "sochi-blocks"
    assert ctx.topic == "sns-post-template"
