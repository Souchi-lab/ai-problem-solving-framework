"""
JuniorBuilderAgent — 候補出し・下書き・整理を担当する agent

推奨 executor: CLIExecutor (Gemini CLI など軽量・高速ツール)
目的: Builder への素材提供。高コストツールの投入を Build 本番に集中させる。
"""

from __future__ import annotations

from ..core.domain.models import Role, RunContext, StepResult, ExecutionType
from ..core.executors.base import BaseExecutor, ExecuteRequest
from ..legacy.prompts.renderer import render_junior_build_prompt
from ..core.agents.base import AgentError, BaseAgent


class JuniorBuilderAgent(BaseAgent):
    """
    JuniorBuilder role の実装。

    plan.md + handoff.md を読み込み、複数の候補案を生成する。
    Builder が判断・統合・品質向上を行う前提でよい。
    """

    def __init__(self, executor: BaseExecutor):
        super().__init__(role=Role.JUNIOR_BUILDER, executor=executor)

    def run(self, context: RunContext) -> StepResult:
        plan_path = context.run_dir / "plan.md"
        handoff_path = context.run_dir / "handoff.md"
        draft_path = context.run_dir / "build_draft.md"

        plan_content = self._read_file(plan_path)
        if not plan_content.strip():
            raise AgentError(f"plan.md is empty or missing: {plan_path}")

        prompt = render_junior_build_prompt(
            plan_content=plan_content,
            handoff_content=self._read_file(handoff_path),
        )
        workspace = context.run_dir.parent.parent / "workspaces" / "junior_builder"

        request = ExecuteRequest(
            prompt=prompt,
            system=JUNIOR_BUILDER_SYSTEM,
            input_files=[plan_path],
            working_dir=workspace if workspace.exists() else None,
        )

        try:
            response = self.executor.execute(request)
            if (
                response.success
                and response.content
                and self.executor.execution_type != ExecutionType.HUMAN
            ):
                self._write_file(draft_path, response.content)

            return StepResult(
                step="junior_build",
                role=self.role,
                success=response.success,
                output_path=draft_path if draft_path.exists() else None,
                execution_type=self.executor.execution_type,
                notes=f"Draft via {self.executor}",
            )
        except Exception as e:
            return StepResult(
                step="junior_build", role=self.role, success=False, error=str(e)
            )


JUNIOR_BUILDER_SYSTEM = """\
You are the JuniorBuilder. Generate 2-3 candidate options based on the Plan.
Show tradeoffs clearly. Do NOT finalize — the Builder decides and integrates.
Speed and diversity over quality.
"""
