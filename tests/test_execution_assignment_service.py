"""
tests/test_execution_assignment_service.py

ExecutionAssignmentService の基本動作を検証する。

カバレッジ:
- execution-assignment.md テーブルのパース
- cli / human / human+cli 各 execution type の認識
- create_executor() が正しい executor クラスを返すこと
- アサインが無い role はデフォルト HumanExecutor を返すこと
- summarize() が全 role を返すこと
- ファイルが存在しない場合も RunContext が返ること
"""

import pytest
from pathlib import Path

from apsf.orchestration.execution_assignment_service import ExecutionAssignmentService
from apsf.core.domain.models import ExecutionAssignment, ExecutionType, Role, RunContext
from apsf.legacy.executors.cli_executor import CLIExecutor
from apsf.legacy.executors.human_executor import HumanExecutor
from apsf.legacy.config.settings import Settings


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    s = Settings()
    s.framework_root = tmp_path
    return s


@pytest.fixture
def service(settings: Settings) -> ExecutionAssignmentService:
    return ExecutionAssignmentService(settings=settings)


SAMPLE_EXECUTION_MD = """\
# Execution Assignment

| Role | Execution Type | Tool | Workspace | Notes |
|---|---|---|---|---|
| Planner | human | 手動 | workspaces/planner/ | human recommended |
| JuniorBuilder | cli | gemini-cli | workspaces/junior_builder/ | speed first |
| Builder | cli | claude | workspaces/builder/ | best tool |
| Critic | human / cli | 手動 | workspaces/critic/ | different from Builder |
| Judge | human | 手動 | workspaces/judge/ | human only |
"""


# ---------------------------------------------------------------------------
# Parsing: roles
# ---------------------------------------------------------------------------

def test_parse_all_roles(tmp_path: Path, service: ExecutionAssignmentService) -> None:
    """テーブルから 5 役割が正しく読み込まれること"""
    path = tmp_path / "execution-assignment.md"
    path.write_text(SAMPLE_EXECUTION_MD, encoding="utf-8")
    context = service.load_from_file(path, tmp_path)

    roles = [a.role for a in context.execution_assignments]
    assert Role.PLANNER in roles
    assert Role.JUNIOR_BUILDER in roles
    assert Role.BUILDER in roles
    assert Role.CRITIC in roles
    assert Role.JUDGE in roles


def test_parse_execution_types(tmp_path: Path, service: ExecutionAssignmentService) -> None:
    """cli / human の execution type が正しく変換されること"""
    path = tmp_path / "execution-assignment.md"
    path.write_text(SAMPLE_EXECUTION_MD, encoding="utf-8")
    context = service.load_from_file(path, tmp_path)

    builder = context.get_execution_assignment(Role.BUILDER)
    assert builder is not None
    assert builder.execution_type == ExecutionType.CLI

    planner = context.get_execution_assignment(Role.PLANNER)
    assert planner is not None
    assert planner.execution_type == ExecutionType.HUMAN


def test_parse_tool_and_workspace(tmp_path: Path, service: ExecutionAssignmentService) -> None:
    """tool / workspace が正しく抽出されること"""
    path = tmp_path / "execution-assignment.md"
    path.write_text(SAMPLE_EXECUTION_MD, encoding="utf-8")
    context = service.load_from_file(path, tmp_path)

    builder = context.get_execution_assignment(Role.BUILDER)
    assert builder is not None
    assert builder.tool == "claude"
    assert builder.workspace == "workspaces/builder/"

    junior = context.get_execution_assignment(Role.JUNIOR_BUILDER)
    assert junior is not None
    assert junior.tool == "gemini-cli"


def test_parse_human_cli_combination(tmp_path: Path, service: ExecutionAssignmentService) -> None:
    """'human / cli' が human として認識されること（v0.1 では human 優先）"""
    path = tmp_path / "execution-assignment.md"
    path.write_text(SAMPLE_EXECUTION_MD, encoding="utf-8")
    context = service.load_from_file(path, tmp_path)

    critic = context.get_execution_assignment(Role.CRITIC)
    assert critic is not None
    assert critic.execution_type == ExecutionType.HUMAN


# ---------------------------------------------------------------------------
# create_executor()
# ---------------------------------------------------------------------------

def test_create_executor_cli(tmp_path: Path, service: ExecutionAssignmentService) -> None:
    """cli タイプの role に CLIExecutor が返ること"""
    path = tmp_path / "execution-assignment.md"
    path.write_text(SAMPLE_EXECUTION_MD, encoding="utf-8")
    context = service.load_from_file(path, tmp_path)

    executor = service.create_executor(context, Role.BUILDER)
    assert isinstance(executor, CLIExecutor)


def test_create_executor_human(tmp_path: Path, service: ExecutionAssignmentService) -> None:
    """human タイプの role に HumanExecutor が返ること"""
    path = tmp_path / "execution-assignment.md"
    path.write_text(SAMPLE_EXECUTION_MD, encoding="utf-8")
    context = service.load_from_file(path, tmp_path)

    executor = service.create_executor(context, Role.JUDGE)
    assert isinstance(executor, HumanExecutor)


def test_create_executor_cli_command(tmp_path: Path, service: ExecutionAssignmentService) -> None:
    """CLIExecutor の command が tool 名と一致すること"""
    path = tmp_path / "execution-assignment.md"
    path.write_text(SAMPLE_EXECUTION_MD, encoding="utf-8")
    context = service.load_from_file(path, tmp_path)

    executor = service.create_executor(context, Role.BUILDER)
    assert isinstance(executor, CLIExecutor)
    assert executor.command == "claude"


def test_create_executor_default_human_when_not_found(
    settings: Settings, service: ExecutionAssignmentService
) -> None:
    """アサインが存在しない role は HumanExecutor (安全なデフォルト) を返すこと"""
    context = RunContext(run_name="test-run", run_dir=Path("."))
    # execution_assignments が空 → デフォルト human
    executor = service.create_executor(context, Role.BUILDER)
    assert isinstance(executor, HumanExecutor)


# ---------------------------------------------------------------------------
# summarize()
# ---------------------------------------------------------------------------

def test_summarize_contains_all_roles(
    tmp_path: Path, service: ExecutionAssignmentService
) -> None:
    """summarize() が 5 役割すべてを含むこと"""
    path = tmp_path / "execution-assignment.md"
    path.write_text(SAMPLE_EXECUTION_MD, encoding="utf-8")
    context = service.load_from_file(path, tmp_path)

    summary = service.summarize(context)
    roles_in_summary = [item["role"] for item in summary]
    for role in [Role.PLANNER, Role.JUNIOR_BUILDER, Role.BUILDER, Role.CRITIC, Role.JUDGE]:
        assert role.value in roles_in_summary


def test_summarize_has_required_keys(
    tmp_path: Path, service: ExecutionAssignmentService
) -> None:
    """summarize() の各アイテムに必要なキーが存在すること"""
    path = tmp_path / "execution-assignment.md"
    path.write_text(SAMPLE_EXECUTION_MD, encoding="utf-8")
    context = service.load_from_file(path, tmp_path)

    summary = service.summarize(context)
    for item in summary:
        assert "role" in item
        assert "execution_type" in item
        assert "tool" in item
        assert "workspace" in item


def test_summarize_default_for_missing_role(
    settings: Settings, service: ExecutionAssignmentService
) -> None:
    """アサインが無い role は 'human (default)' の execution_type を返すこと"""
    context = RunContext(run_name="empty-run", run_dir=Path("."))
    summary = service.summarize(context)

    for item in summary:
        assert item["execution_type"] == "human (default)"


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

def test_load_missing_file_returns_empty_context(
    tmp_path: Path, service: ExecutionAssignmentService
) -> None:
    """execution-assignment.md が存在しない場合も RunContext が返ること"""
    path = tmp_path / "execution-assignment.md"  # 存在しない
    context = service.load_from_file(path, tmp_path)
    assert context.execution_assignments == []


def test_load_ignores_header_and_separator_rows(
    tmp_path: Path, service: ExecutionAssignmentService
) -> None:
    """ヘッダー行・区切り行がパース結果に混入しないこと"""
    path = tmp_path / "execution-assignment.md"
    path.write_text(SAMPLE_EXECUTION_MD, encoding="utf-8")
    context = service.load_from_file(path, tmp_path)

    # "Role" "Execution Type" などのヘッダーが role として混入しないこと
    roles = [a.role for a in context.execution_assignments]
    assert len(roles) == 5  # planner / junior_builder / builder / critic / judge のみ


def test_run_context_get_execution_assignment() -> None:
    """RunContext.get_execution_assignment() が role に対応するアサインを返すこと"""
    assignment = ExecutionAssignment(
        role=Role.BUILDER,
        execution_type=ExecutionType.CLI,
        tool="claude",
        workspace="workspaces/builder/",
    )
    context = RunContext(
        run_name="2026-03-15_sochi-blocks_sns-post-template",
        run_dir=Path("."),
        execution_assignments=[assignment],
    )

    found = context.get_execution_assignment(Role.BUILDER)
    assert found is assignment

    not_found = context.get_execution_assignment(Role.CRITIC)
    assert not_found is None
