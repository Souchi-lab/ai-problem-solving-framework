from __future__ import annotations

import asyncio
from pathlib import Path

from apsf.legacy.storage.run_repository import RunRepository
from apsf.viewer import api


def _write_run_state(run_dir: Path, phase: str) -> None:
    (run_dir / "run_state.json").write_text(
        (
            "{"
            f"\"run_id\":\"{run_dir.name}\","
            f"\"current_phase\":\"{phase}\","
            "\"phase_status\":\"pending\","
            "\"current_owner\":\"Builder\","
            "\"retry_count\":0,"
            "\"last_error\":\"\","
            "\"active_handoff_id\":\"\","
            "\"gate_failures\":[]"
            "}"
        ),
        encoding="utf-8",
    )


def test_build_child_summaries_includes_dependency_status(monkeypatch, tmp_path: Path) -> None:
    project_root = tmp_path
    template_dir = project_root / "runs" / "_template"
    template_dir.mkdir(parents=True)
    for name in ("goal.md", "plan.md", "build.md"):
        (template_dir / name).write_text(f"# {name}\n", encoding="utf-8")

    repo = RunRepository(project_root / "runs", template_dir)
    parent_dir = project_root / "runs" / "work" / "2026-04-09_parent_case"
    child_dir = parent_dir / "001c2_case_topic"
    dep_dir = parent_dir / "001c1_case_topic"
    child_dir.mkdir(parents=True)
    dep_dir.mkdir(parents=True)
    _write_run_state(child_dir, "BUILD_NEEDED")
    _write_run_state(dep_dir, "IN_PROGRESS")
    (child_dir / "execution-assignment.md").write_text(
        "## Dependencies\n| Run | Artifact | Reason |\n|---|---|---|\n| 001c1_case_topic | `build.md` | upstream |\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(api, "PROJECT_ROOT", project_root)
    monkeypatch.setattr(api, "repo", repo)

    summaries = api.build_child_summaries("2026-04-09_parent_case", "work")

    target = next(summary for summary in summaries if summary.child_name == "001c2_case_topic")
    assert target.depends_on == ["001c1_case_topic"]
    assert target.dependency_phases["001c1_case_topic"] == "IN_PROGRESS"
    assert target.has_incomplete_dependencies is True
    assert summaries[0].child_name == "001c2_case_topic"


def test_create_child_run_route_creates_directory(monkeypatch, tmp_path: Path) -> None:
    project_root = tmp_path
    template_dir = project_root / "runs" / "_template"
    template_dir.mkdir(parents=True)
    for name in ("goal.md", "plan.md", "build.md"):
        (template_dir / name).write_text(f"# {name}\n", encoding="utf-8")

    repo = RunRepository(project_root / "runs", template_dir)
    parent_dir = project_root / "runs" / "work" / "2026-04-09_parent_case"
    parent_dir.mkdir(parents=True)

    monkeypatch.setattr(api, "PROJECT_ROOT", project_root)
    monkeypatch.setattr(api, "repo", repo)

    response = asyncio.run(
        api.create_child_run(
            "work",
            "2026-04-09_parent_case",
            api.CreateChildRunRequest(
                run_id="001c3_case_topic",
                taxonomy="work",
                title="Viewer Child",
                goal="Create a child run from the viewer route.",
            ),
        )
    )

    assert response.status == "created"
    child_dir = parent_dir / "001c3_case_topic"
    assert child_dir.exists()
    assert "Create a child run from the viewer route." in (child_dir / "goal.md").read_text(encoding="utf-8")
