"""
CriticAgent — レビュー・問題指摘を担当する agent

推奨 executor: HumanExecutor または Builder と別系統の CLIExecutor
重要: Builder と同一ツールで Critic をしない（自己評価バイアスが生じる）
"""

from __future__ import annotations

from ..domain.models import Role, RunContext, StepResult, ExecutionType
from ..executors.base import BaseExecutor, ExecuteRequest
from ..prompts.renderer import render_review_prompt
from .base import AgentError, BaseAgent


class CriticAgent(BaseAgent):
    """
    Critic role の実装。

    build.md + 成果物を読み込み、Critical / Major / Minor 分類レビューを生成する。
    Builder と異なる executor / ツールを使うことで独立した視点を確保する。
    """

    def __init__(self, executor: BaseExecutor):
        super().__init__(role=Role.CRITIC, executor=executor)

    def run(self, context: RunContext) -> StepResult:
        goal_path = context.run_dir / "goal.md"
        build_path = context.run_dir / "build.md"
        handoff_path = context.run_dir / "handoff.md"
        review_path = context.run_dir / "review.md"

        build_content = self._read_file(build_path)
        if not build_content.strip():
            raise AgentError(f"build.md is empty or missing: {build_path}")

        prompt = render_review_prompt(
            goal_content=self._read_file(goal_path),
            build_content=build_content,
            handoff_content=self._read_file(handoff_path),
        )
        workspace = context.run_dir.parent.parent / "workspaces" / "critic"

        request = ExecuteRequest(
            prompt=prompt,
            system=CRITIC_SYSTEM,
            input_files=[goal_path, build_path],
            working_dir=workspace if workspace.exists() else None,
        )

        try:
            response = self.executor.execute(request)
            if (
                response.success
                and response.content
                and self.executor.execution_type != ExecutionType.HUMAN
            ):
                self._write_file(review_path, response.content)

            return StepResult(
                step="review",
                role=self.role,
                success=response.success,
                output_path=review_path if review_path.exists() else None,
                execution_type=self.executor.execution_type,
                notes=f"Reviewed via {self.executor}",
            )
        except Exception as e:
            return StepResult(
                step="review", role=self.role, success=False, error=str(e)
            )


CRITIC_SYSTEM = """\
You are the Critic. Evaluate the Build against the Goal's success criteria.
Classify issues: Critical / Major / Minor.
Provide specific, actionable suggestions. Do NOT praise for the sake of it.
You are intentionally using a different tool/perspective from the Builder.
"""
