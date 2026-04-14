from __future__ import annotations

import asyncio
import shutil
import uuid
from pathlib import Path

import pytest

from apsf.legacy.storage.run_repository import RunRepository
from apsf.viewer import api


def _make_repo_local_temp_root() -> Path:
    base = Path.cwd() / ".tmp-specialist-writeback-tests"
    base.mkdir(exist_ok=True)
    root = base / f"case-{uuid.uuid4().hex}"
    root.mkdir()
    return root


def test_confirm_specialist_writes_to_exact_child_run_assignment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = _make_repo_local_temp_root()
    try:
        runs_dir = root / "runs"
        template_dir = runs_dir / "_template"
        template_dir.mkdir(parents=True, exist_ok=True)

        taxonomy = "fw-improvement"
        parent = "2026-04-05-900_fw-improvement_parent-run"
        child = "900c1_specialist-child-target"
        parent_dir = runs_dir / taxonomy / parent
        child_dir = parent_dir / child
        child_dir.mkdir(parents=True)
        parent_dir.mkdir(parents=True, exist_ok=True)

        (parent_dir / "execution-assignment.md").write_text(
            "# Execution Assignment\n\n## Optional Specialist Notes\n\n### Planner Specialist\n\n- Primary P-TYPE: P-01\n",
            encoding="utf-8",
        )
        (child_dir / "execution-assignment.md").write_text(
            "# Execution Assignment\n\n## Optional Specialist Notes\n\n### Planner Specialist\n\n- Primary P-TYPE:\n",
            encoding="utf-8",
        )

        monkeypatch.setattr(api, "PROJECT_ROOT", root)
        monkeypatch.setattr(api, "repo", RunRepository(runs_dir=runs_dir, template_dir=template_dir))

        response = asyncio.run(
            api.confirm_specialist(
                taxonomy,
                f"{parent}/{child}",
                api.ConfirmSpecialistRequest(
                    role="Planner",
                    specialist_code="P-06",
                    source="test-child-writeback",
                ),
            )
        )

        child_text = (child_dir / "execution-assignment.md").read_text(encoding="utf-8")
        parent_text = (parent_dir / "execution-assignment.md").read_text(encoding="utf-8")

        assert "P-TYPE: P-06" in child_text
        assert "P-TYPE: P-06" not in parent_text
        assert response.target_run_name == f"{parent}/{child}"
        expected = Path("runs") / taxonomy / parent / child / "execution-assignment.md"
        assert Path(response.artifact_path) == expected
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_confirm_specialist_updates_cli_target_and_model_assignment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = _make_repo_local_temp_root()
    try:
        runs_dir = root / "runs"
        template_dir = runs_dir / "_template"
        template_dir.mkdir(parents=True, exist_ok=True)

        taxonomy = "work"
        run_name = "2026-04-09-001_work_specialist-target-update"
        run_dir = runs_dir / taxonomy / run_name
        run_dir.mkdir(parents=True, exist_ok=True)

        (run_dir / "execution-assignment.md").write_text(
            "# Execution Assignment\n\n"
            "## Role Execution Assignments\n\n"
            "| Role | Execution Type | Tool / Method | Workspace | Notes |\n"
            "|---|---|---|---|---|\n"
            "| Planner | cli | claude | workspaces/planner/ | planning |\n",
            encoding="utf-8",
        )

        monkeypatch.setattr(api, "PROJECT_ROOT", root)
        monkeypatch.setattr(api, "repo", RunRepository(runs_dir=runs_dir, template_dir=template_dir))

        response = asyncio.run(
            api.confirm_specialist(
                taxonomy,
                run_name,
                api.ConfirmSpecialistRequest(
                    role="Planner",
                    specialist_code="P-13",
                    source="test-model-sync",
                    provider="openai",
                    model="gpt-5.4 / codex runtime",
                    apply_model_assignment=True,
                ),
            )
        )

        execution_text = (run_dir / "execution-assignment.md").read_text(encoding="utf-8")
        model_text = (run_dir / "model-assignment.md").read_text(encoding="utf-8")

        assert "| Planner | cli | codex | workspaces/planner/ | planning |" in execution_text
        assert "P-TYPE: P-13" in execution_text
        assert "| Planner | openai | gpt-5.4 / codex runtime | no |" in model_text
        assert response.model_artifact_path is not None
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_confirm_specialist_updates_four_column_execution_assignment_table(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = _make_repo_local_temp_root()
    try:
        runs_dir = root / "runs"
        template_dir = runs_dir / "_template"
        template_dir.mkdir(parents=True, exist_ok=True)

        taxonomy = "work"
        run_name = "2026-04-09-002_work_specialist-four-col"
        run_dir = runs_dir / taxonomy / run_name
        run_dir.mkdir(parents=True, exist_ok=True)

        (run_dir / "execution-assignment.md").write_text(
            "# Execution Assignment\n\n"
            "## Role Execution Assignments\n\n"
            "| Role | Execution Type | Tool / Method | Notes |\n"
            "|---|---|---|---|\n"
            "| Planner | cli | claude | planning |\n",
            encoding="utf-8",
        )

        monkeypatch.setattr(api, "PROJECT_ROOT", root)
        monkeypatch.setattr(api, "repo", RunRepository(runs_dir=runs_dir, template_dir=template_dir))

        asyncio.run(
            api.confirm_specialist(
                taxonomy,
                run_name,
                api.ConfirmSpecialistRequest(
                    role="Planner",
                    specialist_code="P-13",
                    source="test-four-col-sync",
                    provider="openai",
                    model="gpt-5.4 / codex runtime",
                    apply_model_assignment=True,
                ),
            )
        )

        execution_text = (run_dir / "execution-assignment.md").read_text(encoding="utf-8")
        assert "| Planner | cli | codex | planning |" in execution_text
    finally:
        shutil.rmtree(root, ignore_errors=True)
