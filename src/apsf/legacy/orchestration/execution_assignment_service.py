"""
ExecutionAssignmentService — execution-assignment.md の解析と executor 生成

execution-assignment.md の Python 表現を扱う。
run ごとに role → execution type / tool の割り当てを読み込み、
ExecutionAssignmentService が適切な executor を生成する責務を持つ。
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from ..config.settings import Settings
from ...core.domain.models import ExecutionAssignment, ExecutionType, Role, RunContext
from ...core.executors.base import BaseExecutor
from ..executors.cli_executor import CLIExecutor
from ..executors.human_executor import HumanExecutor
from ..executors.api_executor import APIExecutor


class ExecutionAssignmentService:
    """
    execution-assignment.md を読み込んで executor を生成するサービス。

    使用例:
        service = ExecutionAssignmentService(settings=get_settings())
        context = service.load_from_file(run_dir / "execution-assignment.md", run_dir)
        executor = service.create_executor(context, Role.BUILDER)
    """

    def __init__(self, settings: Settings):
        self._settings = settings

    def load_from_file(self, assignment_path: Path, run_dir: Path) -> RunContext:
        """
        execution-assignment.md を読み込んで RunContext を生成する。

        v0.1 では簡易パーサー。テーブル形式を解析する。
        TODO(v0.2): YAML front matter または構造化フォーマットへの移行を検討。
        """
        run_name = run_dir.name
        context = RunContext(run_name=run_name, run_dir=run_dir)

        if not assignment_path.exists():
            return context

        content = assignment_path.read_text(encoding="utf-8")
        context.execution_assignments = self._parse_assignments(content)
        return context

    def _parse_assignments(self, content: str) -> list[ExecutionAssignment]:
        """
        execution-assignment.md のテーブル行をパースする。

        テーブル形式の例:
        | Builder | cli | claude | workspaces/builder/ | ... |
        | Critic  | human | 手動 | workspaces/critic/ | ... |
        """
        assignments: list[ExecutionAssignment] = []

        role_map = {
            "planner": Role.PLANNER,
            "juniorbuilder": Role.JUNIOR_BUILDER,
            "junior_builder": Role.JUNIOR_BUILDER,
            "junior builder": Role.JUNIOR_BUILDER,
            "builder": Role.BUILDER,
            "critic": Role.CRITIC,
            "judge": Role.JUDGE,
        }

        exec_type_map = {
            "cli": ExecutionType.CLI,
            "human": ExecutionType.HUMAN,
            "human / cli": ExecutionType.HUMAN,
            "future-api": ExecutionType.FUTURE_API,
            "future_api": ExecutionType.FUTURE_API,
        }

        for line in content.splitlines():
            if not line.startswith("|") or "---" in line:
                continue

            cells = [c.strip() for c in line.strip("|").split("|")]
            if len(cells) < 2:
                continue

            role_str = cells[0].lower().strip()
            role = role_map.get(role_str)
            if role is None:
                continue

            exec_str = cells[1].lower().strip()
            execution_type = exec_type_map.get(exec_str, ExecutionType.HUMAN)

            tool = cells[2].strip() if len(cells) > 2 else ""
            workspace = cells[3].strip() if len(cells) > 3 else ""
            notes = cells[4].strip() if len(cells) > 4 else ""

            assignments.append(
                ExecutionAssignment(
                    role=role,
                    execution_type=execution_type,
                    tool=tool,
                    workspace=workspace,
                    notes=notes,
                )
            )

        return assignments

    def create_executor(self, context: RunContext, role: Role) -> BaseExecutor:
        """
        RunContext から指定 role の executor を生成する。
        アサインが見つからない場合は HumanExecutor を返す（安全なデフォルト）。
        """
        assignment = context.get_execution_assignment(role)

        if assignment is None:
            # デフォルト: human executor（判断を人間に委ねる）
            return HumanExecutor(role=role)

        return self._create_executor_instance(assignment, role)

    def _create_executor_instance(
        self,
        assignment: ExecutionAssignment,
        role: Role,
    ) -> BaseExecutor:
        """ExecutionAssignment から具体的な executor を生成する。"""
        if assignment.execution_type == ExecutionType.CLI:
            command = assignment.tool or "claude"  # デフォルトは claude
            workspace_path: Optional[Path] = None
            if assignment.workspace:
                workspace_path = self._settings.framework_root / assignment.workspace
            return CLIExecutor(command=command, working_dir=workspace_path)

        elif assignment.execution_type == ExecutionType.HUMAN:
            return HumanExecutor(role=role)

        elif assignment.execution_type == ExecutionType.FUTURE_API:
            # v0.1 では stub。v0.2 で model-assignment と組み合わせて実装する。
            return APIExecutor(provider_type="", model="")

        # フォールバック: human
        return HumanExecutor(role=role)

    def summarize(self, context: RunContext) -> list[dict]:
        """dry-run 表示用: role ごとの execution 設定のサマリを返す"""
        result = []
        for role in [Role.PLANNER, Role.JUNIOR_BUILDER, Role.BUILDER, Role.CRITIC, Role.JUDGE]:
            assignment = context.get_execution_assignment(role)
            if assignment:
                result.append({
                    "role": role.value,
                    "execution_type": assignment.execution_type.value,
                    "tool": assignment.tool,
                    "workspace": assignment.workspace,
                })
            else:
                result.append({
                    "role": role.value,
                    "execution_type": "human (default)",
                    "tool": "",
                    "workspace": "",
                })
        return result
