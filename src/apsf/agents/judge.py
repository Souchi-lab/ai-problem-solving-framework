"""
JudgeAgent — 完了判定・最終評価を担当する agent

推奨 executor: HumanExecutor（v0.1 では必須）
人間の判断が品質を安定させる。AI による評価サマリは補助として使う。
"""

from __future__ import annotations

from ..domain.models import Role, RunContext, StepResult, ExecutionType
from ..executors.base import BaseExecutor, ExecuteRequest
from ..prompts.renderer import render_judge_prompt
from .base import BaseAgent


class JudgeAgent(BaseAgent):
    """
    Judge role の実装。

    v0.1 では HumanExecutor を使い、人間への判断指示を出力する。
    CLIExecutor の場合は評価サマリを生成するが、最終判定は人間が行う。
    """

    def __init__(self, executor: BaseExecutor):
        super().__init__(role=Role.JUDGE, executor=executor)

    def run(self, context: RunContext) -> StepResult:
        goal_path = context.run_dir / "goal.md"
        review_path = context.run_dir / "review.md"
        judge_summary_path = context.run_dir / "judge_summary.md"

        review_content = self._read_file(review_path)
        if not review_content.strip():
            raise ValueError(f"review.md is empty or missing: {review_path}")

        prompt = render_judge_prompt(
            goal_content=self._read_file(goal_path),
            review_content=review_content,
        )
        workspace = context.run_dir.parent.parent / "workspaces" / "judge"

        request = ExecuteRequest(
            prompt=prompt,
            system=JUDGE_SYSTEM,
            input_files=[goal_path, review_path],
            working_dir=workspace if workspace.exists() else None,
        )

        try:
            response = self.executor.execute(request)
            if (
                response.success
                and response.content
                and self.executor.execution_type != ExecutionType.HUMAN
            ):
                self._write_file(judge_summary_path, response.content)

            human_note = (
                " — Human final decision required."
                if self.executor.execution_type == ExecutionType.HUMAN
                else " — AI summary generated. Human makes final call."
            )

            return StepResult(
                step="judge",
                role=self.role,
                success=response.success,
                output_path=judge_summary_path if judge_summary_path.exists() else None,
                execution_type=self.executor.execution_type,
                notes=f"Judge via {self.executor}{human_note}",
            )
        except Exception as e:
            return StepResult(
                step="judge", role=self.role, success=False, error=str(e)
            )


JUDGE_SYSTEM = """\
You are the Judge (AI assist). Summarize how well criteria are met.
Suggest: 'Continue (address X)' or 'Complete'.
The HUMAN makes the final decision. You assist, not decide.
"""
