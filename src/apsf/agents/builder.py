"""
BuilderAgent — 実装・具体化・統合を担当する agent

推奨 executor: CLIExecutor (Claude Code)
重要: この工程が最も高い付加価値を生む。最高性能ツールを集中投入する。
"""

from __future__ import annotations

from ..domain.models import Role, RunContext, StepResult, ExecutionType
from ..executors.base import BaseExecutor, ExecuteRequest
from ..prompts.renderer import render_build_prompt
from .base import AgentError, BaseAgent


class BuilderAgent(BaseAgent):
    """
    Builder role の実装。

    plan.md (+ build_draft.md) を読み込み、最終的な成果物と build.md を生成する。
    高品質なアウトプットが求められるため、最高性能ツールの使用を推奨。
    """

    def __init__(self, executor: BaseExecutor):
        super().__init__(role=Role.BUILDER, executor=executor)

    def run(self, context: RunContext) -> StepResult:
        plan_path = context.run_dir / "plan.md"
        handoff_path = context.run_dir / "handoff.md"
        draft_path = context.run_dir / "build_draft.md"
        build_review_path = context.run_dir / "build_review.md"
        build_path = context.run_dir / "build.md"

        plan_content = self._read_file(plan_path)
        if not plan_content.strip():
            raise AgentError(f"plan.md is empty or missing: {plan_path}")

        prompt = render_build_prompt(
            plan_content=plan_content,
            handoff_content=self._read_file(handoff_path),
            draft_content=self._read_file(draft_path),
            build_review_content=self._read_file(build_review_path),
        )
        workspace = context.run_dir.parent.parent / "workspaces" / "builder"

        request = ExecuteRequest(
            prompt=prompt,
            system=BUILDER_SYSTEM,
            input_files=[plan_path, handoff_path, build_review_path],
            working_dir=workspace if workspace.exists() else None,
        )

        try:
            response = self.executor.execute(request)
            if (
                response.success
                and response.content
                and self.executor.execution_type != ExecutionType.HUMAN
            ):
                self._write_file(build_path, response.content)

            return StepResult(
                step="build",
                role=self.role,
                success=response.success,
                output_path=build_path if build_path.exists() else None,
                execution_type=self.executor.execution_type,
                notes=f"Built via {self.executor}",
            )
        except Exception as e:
            return StepResult(
                step="build", role=self.role, success=False, error=str(e)
            )


BUILDER_SYSTEM = """\
You are the Builder. Implement the deliverable based on the Plan.
If a JuniorBuilder draft exists, use it as reference — judge, integrate, improve.
If build_review.md exists, treat it as structured rebuild feedback.
Record all decisions in build.md. Note deviations from Plan.
Keep build.md as a build record, not as a dump of the full deliverable.
This is the high-value step. Focus on quality.
"""
