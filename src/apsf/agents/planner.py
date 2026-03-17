"""
PlannerAgent — 問題分解・計画立案を担当する agent

推奨 executor: HumanExecutor（人間 + AI の共同で品質が安定しやすい）
推奨ツール: ChatGPT / Claude.ai ブラウザ / 手書き
"""

from __future__ import annotations

from ..domain.models import Role, RunContext, StepResult, ExecutionType
from ..executors.base import BaseExecutor, ExecuteRequest
from ..prompts.renderer import render_plan_prompt
from .base import AgentError, BaseAgent


class PlannerAgent(BaseAgent):
    """
    Planner role の実装。

    goal.md を読み込み、plan.md の生成指示を executor に渡す。
    HumanExecutor の場合は「何を書くべきか」の指示を出力する。
    CLIExecutor の場合は CLI ツールに prompt を渡す。
    """

    def __init__(self, executor: BaseExecutor):
        super().__init__(role=Role.PLANNER, executor=executor)

    def run(self, context: RunContext) -> StepResult:
        """goal.md → plan.md 生成の指示または実行"""
        goal_path = context.run_dir / "goal.md"
        plan_path = context.run_dir / "plan.md"

        goal_content = self._read_file(goal_path)
        if not goal_content.strip():
            raise AgentError(
                f"goal.md is empty or missing: {goal_path}\n"
                "Please write goal.md before running Planner."
            )

        prompt = render_plan_prompt(goal_content=goal_content)
        workspace = context.run_dir.parent.parent / "workspaces" / "planner"

        request = ExecuteRequest(
            prompt=prompt,
            system=PLANNER_SYSTEM,
            input_files=[goal_path],
            working_dir=workspace if workspace.exists() else None,
        )

        try:
            response = self.executor.execute(request)

            # CLI / API executor が実際に内容を生成した場合はファイルに書く
            if (
                response.success
                and response.content
                and self.executor.execution_type != ExecutionType.HUMAN
            ):
                self._write_file(plan_path, response.content)

            return StepResult(
                step="plan",
                role=self.role,
                success=response.success,
                output_path=plan_path if plan_path.exists() else None,
                execution_type=self.executor.execution_type,
                notes=f"via {self.executor}",
            )
        except Exception as e:
            return StepResult(
                step="plan", role=self.role, success=False, error=str(e)
            )


PLANNER_SYSTEM = """\
You are the Planner in an AI Problem Solving Framework.

Break down the Goal into a structured plan.md.
Propose at least 2 options and select the best one with reasoning.
Write a concrete Execution Plan the Builder can follow directly.

You do NOT implement anything. Plan only.
"""
