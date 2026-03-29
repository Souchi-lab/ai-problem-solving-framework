"""
Pipeline — Planner → JuniorBuilder → Builder → Critic → Judge の実行骨格

v0.1: dry-run 中心。role / executor のマッピングを表示する。
将来: run_all() で全ステップを順次実行する。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from ...core.domain.models import Role, RunContext, StepResult, ExecutionType
from ...core.executors.base import BaseExecutor
from ...core.agents.base import BaseAgent


@dataclass
class PipelineStep:
    name: str
    role: Role
    agent: Optional[BaseAgent] = None
    description: str = ""


class Pipeline:
    """
    問題解決ループの実行管理。

    dry_run(): role / executor のマッピングを確認する
    run_step(): 1 ステップだけ実行する
    run_all(): 全ステップを順次実行する（v0.1 では human step で一時停止）
    """

    def __init__(self, context: RunContext):
        self._context = context
        self._steps: list[PipelineStep] = []
        self._results: list[StepResult] = []

    def add_step(
        self,
        name: str,
        role: Role,
        agent: Optional[BaseAgent] = None,
        description: str = "",
    ) -> "Pipeline":
        self._steps.append(PipelineStep(name=name, role=role, agent=agent, description=description))
        return self

    def dry_run(self) -> list[dict]:
        """実際には実行せず、各ステップの role / executor マッピングを返す"""
        summary = []
        for step in self._steps:
            if step.agent:
                executor_info = str(step.agent.executor)
                exec_type = step.agent.executor.execution_type.value
            else:
                executor_info = "HumanExecutor — manual action required"
                exec_type = "human"

            summary.append({
                "step": step.name,
                "role": step.role.value,
                "executor": executor_info,
                "execution_type": exec_type,
                "description": step.description,
            })
        return summary

    def run_step(self, step_name: str) -> StepResult:
        """指定したステップだけを実行する"""
        step = next((s for s in self._steps if s.name == step_name), None)
        if step is None:
            raise ValueError(f"Step not found: {step_name}")
        if step.agent is None:
            raise ValueError(f"Step '{step_name}' has no agent. Assign one first.")

        result = step.agent.run(self._context)
        self._results.append(result)
        return result

    def run_all(self) -> list[StepResult]:
        """
        全ステップを順次実行する。
        Human executor のステップは一時停止して確認を求める。

        TODO(v0.2): 人間確認をより洗練されたUIで実装する
        """
        results = []
        for step in self._steps:
            if step.agent is None or step.agent.executor.execution_type == ExecutionType.HUMAN:
                print(f"\n[PAUSE]  [{step.name}] Human step — please complete manually.")
                print(f"   Workspace: workspaces/{step.role.value}/")
                print(f"   Output:    {self._context.run_dir / (step.name + '.md')}")
                input("   Press Enter when done...")
                results.append(StepResult(
                    step=step.name,
                    role=step.role,
                    success=True,
                    execution_type=ExecutionType.HUMAN,
                    notes="Human step — manually completed",
                ))
                continue

            print(f"\n[RUN]  [{step.name}] Running via {step.agent.executor} ...")
            result = step.agent.run(self._context)
            results.append(result)
            self._results.append(result)

            if not result.success:
                print(f"[ERROR] [{step.name}] Failed: {result.error}")
                break
            else:
                print(f"[OK] [{step.name}] → {result.output_path}")

        return results

    @property
    def results(self) -> list[StepResult]:
        return list(self._results)
