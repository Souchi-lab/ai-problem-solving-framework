from __future__ import annotations

from pathlib import Path

import pytest

from apsf.core.dependencies.run_dependencies import (
    IncompleteDependencyError,
    dependency_status_by_run,
    inject_dependency_context,
    parse_dependency_specs,
)


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


def test_parse_dependency_specs_supports_markdown_table() -> None:
    specs = parse_dependency_specs(
        """
# Execution Assignment

## Dependencies
| Run | Artifact | Reason |
|-----|----------|--------|
| 001c1_case_topic | `plan.md` | upstream plan |
"""
    )

    assert len(specs) == 1
    assert specs[0].run_id == "001c1_case_topic"
    assert specs[0].artifact == "plan.md"


def test_parse_dependency_specs_supports_bullet_format() -> None:
    specs = parse_dependency_specs(
        """
## depends_on
- run: 001c1_case_topic
  artifact: build.md#What was built
  reason: carry forward build context
"""
    )

    assert len(specs) == 1
    assert specs[0].artifact == "build.md#What was built"


def test_parse_dependency_specs_supports_utf8_bom_prefixed_heading() -> None:
    specs = parse_dependency_specs(
        "\ufeff## depends_on\n"
        "- run: 001c1_case_topic\n"
        "  artifact: build.md#Decisions made\n"
    )

    assert len(specs) == 1
    assert specs[0].run_id == "001c1_case_topic"
    assert specs[0].artifact == "build.md#Decisions made"


def test_inject_dependency_context_appends_complete_dependency(tmp_path: Path) -> None:
    project_root = tmp_path
    (project_root / "runs" / "_template").mkdir(parents=True)
    current_run = project_root / "runs" / "work" / "2026-04-09_parent_case" / "001c2_case_topic"
    current_run.mkdir(parents=True)
    dep_run = current_run.parent / "001c1_case_topic"
    dep_run.mkdir(parents=True)

    (current_run / "execution-assignment.md").write_text(
        "## Dependencies\n| Run | Artifact | Reason |\n|---|---|---|\n| 001c1_case_topic | `build.md` | upstream |\n",
        encoding="utf-8",
    )
    _write_run_state(dep_run, "COMPLETE")
    (dep_run / "build.md").write_text("# Build\n\nupstream artifact text\n", encoding="utf-8")

    prompt = inject_dependency_context(
        project_root=project_root,
        run_dir=current_run,
        prompt_text="base prompt",
    )

    assert "Dependency Inputs" in prompt
    assert "upstream artifact text" in prompt


def test_inject_dependency_context_reads_cp932_dependency_artifact(tmp_path: Path) -> None:
    project_root = tmp_path
    (project_root / "runs" / "_template").mkdir(parents=True)
    current_run = project_root / "runs" / "work" / "2026-04-09_parent_case" / "001c2_case_topic"
    current_run.mkdir(parents=True)
    dep_run = current_run.parent / "001c1_case_topic"
    dep_run.mkdir(parents=True)

    (current_run / "execution-assignment.md").write_text(
        "## Dependencies\n| Run | Artifact | Reason |\n|---|---|---|\n| 001c1_case_topic | `auto_loop.log` | upstream |\n",
        encoding="utf-8",
    )
    _write_run_state(dep_run, "COMPLETE")
    (dep_run / "auto_loop.log").write_bytes("自動ループ継続\n".encode("cp932"))

    prompt = inject_dependency_context(
        project_root=project_root,
        run_dir=current_run,
        prompt_text="base prompt",
    )

    assert "Dependency Inputs" in prompt
    assert "自動ループ継続" in prompt


def test_inject_dependency_context_blocks_incomplete_dependency(tmp_path: Path) -> None:
    project_root = tmp_path
    (project_root / "runs" / "_template").mkdir(parents=True)
    current_run = project_root / "runs" / "work" / "2026-04-09_parent_case" / "001c2_case_topic"
    current_run.mkdir(parents=True)
    dep_run = current_run.parent / "001c1_case_topic"
    dep_run.mkdir(parents=True)

    (current_run / "execution-assignment.md").write_text(
        "## depends_on\n- run: 001c1_case_topic\n  artifact: build.md\n",
        encoding="utf-8",
    )
    _write_run_state(dep_run, "IN_PROGRESS")
    (dep_run / "build.md").write_text("# Build\n", encoding="utf-8")

    with pytest.raises(IncompleteDependencyError, match="phase=IN_PROGRESS"):
        inject_dependency_context(
            project_root=project_root,
            run_dir=current_run,
            prompt_text="base prompt",
        )


def test_dependency_status_by_run_reports_missing_and_incomplete(tmp_path: Path) -> None:
    project_root = tmp_path
    (project_root / "runs" / "_template").mkdir(parents=True)
    run_dir = project_root / "runs" / "work" / "2026-04-09_parent_case" / "001c2_case_topic"
    run_dir.mkdir(parents=True)
    dep_run = run_dir.parent / "001c1_case_topic"
    dep_run.mkdir(parents=True)
    _write_run_state(dep_run, "REVIEW_NEEDED")
    (run_dir / "execution-assignment.md").write_text(
        "## depends_on\n- run: 001c1_case_topic\n  artifact: build.md\n- run: 001c9_missing_topic\n  artifact: plan.md\n",
        encoding="utf-8",
    )

    depends_on, phases, has_incomplete = dependency_status_by_run(
        project_root=project_root,
        run_dir=run_dir,
    )

    assert depends_on == ["001c1_case_topic", "001c9_missing_topic"]
    assert phases["001c1_case_topic"] == "REVIEW_NEEDED"
    assert phases["001c9_missing_topic"] == "MISSING"
    assert has_incomplete is True
