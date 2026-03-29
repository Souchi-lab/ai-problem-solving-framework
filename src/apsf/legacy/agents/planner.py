"""
PlannerAgent - planner role implementation
"""

from __future__ import annotations

from ..config.settings import get_settings
from ..cli.specialist_registry import resolve_planner_specialist
from ...core.domain.models import ExecutionType, Role, RunContext, StepResult
from ...core.executors.base import BaseExecutor, ExecuteRequest
from ..prompts.renderer import render_plan_prompt
from ...core.agents.base import AgentError, BaseAgent


class PlannerAgent(BaseAgent):
    def __init__(self, executor: BaseExecutor):
        super().__init__(role=Role.PLANNER, executor=executor)

    def run(self, context: RunContext) -> StepResult:
        goal_path = context.run_dir / "goal.md"
        assignment_path = context.run_dir / "execution-assignment.md"
        plan_review_path = context.run_dir / "plan_review.md"
        plan_path = context.run_dir / "plan.md"

        goal_content = self._read_file(goal_path)
        if not goal_content.strip():
            raise AgentError(
                f"goal.md is empty or missing: {goal_path}\n"
                "Please write goal.md before running Planner."
            )

        assignment_content = self._read_file(assignment_path)
        plan_review_content = self._read_file(plan_review_path)
        framework_root = get_settings().framework_root
        selection = resolve_planner_specialist(
            goal_text=goal_content,
            assignment_text=assignment_content,
            framework_root=framework_root,
        )
        selection_note = (
            f"- Mode: {selection.mode}\n"
            f"- Selected P-TYPE: {selection.ptype or '(none)'}\n"
            f"- Specialist Path: {selection.specialist_path.as_posix() if selection.specialist_path else '(none)'}\n"
            f"- Reason: {selection.reason}\n"
        )

        prompt = render_plan_prompt(
            goal_content=goal_content,
            specialist_content=selection.specialist_content,
            specialist_selection_note=selection_note,
            plan_review_content=plan_review_content,
        )
        workspace = context.run_dir.parent.parent / "workspaces" / "planner"
        input_files = [goal_path, assignment_path]
        if plan_review_path.exists():
            input_files.append(plan_review_path)

        request = ExecuteRequest(
            prompt=prompt,
            system=PLANNER_SYSTEM,
            input_files=input_files,
            working_dir=workspace if workspace.exists() else None,
        )

        try:
            response = self.executor.execute(request)
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
            return StepResult(step="plan", role=self.role, success=False, error=str(e))


PLANNER_SYSTEM = """\
You are the Planner in an AI Problem Solving Framework.

Break down the Goal into a structured plan.md.
Propose at least 2 options and select the best one with reasoning.
Write a concrete Execution Plan the Builder can follow directly.

You do NOT implement anything. Plan only.
"""
