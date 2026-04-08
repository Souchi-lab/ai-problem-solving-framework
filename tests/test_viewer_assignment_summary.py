"""Tests for phase-aware assignment summary in the viewer API."""
from __future__ import annotations

from pathlib import Path

import pytest

from apsf.legacy.config import settings as settings_module
from apsf.legacy.config.settings import Settings
from apsf.viewer import api


@pytest.fixture(autouse=True)
def fixed_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    settings = Settings()
    settings.anthropic_api_key = "sk-ant-test"
    settings.openai_api_key = ""
    settings.gemini_api_key = ""
    settings.default_anthropic_model = "claude-sonnet-4-6"
    monkeypatch.setattr(settings_module, "_settings_instance", settings)


def test_non_assignment_phase_returns_not_applicable(tmp_path: Path) -> None:
    summary = api._resolve_assignment_summary(tmp_path, "RESULT_NEEDED")

    assert summary.role == ""
    assert summary.execution.mode == "not_applicable"
    assert summary.execution.execution_type == "not_applicable"
    assert summary.model.mode == "not_applicable"


def test_plan_phase_without_files_defaults_to_human_execution_and_unset_model(tmp_path: Path) -> None:
    summary = api._resolve_assignment_summary(tmp_path, "PLAN_NEEDED")

    assert summary.role == "planner"
    assert summary.execution.mode == "default"
    assert summary.execution.execution_type == "human"
    assert summary.execution.target == "human"
    # human execution → model selection is operator's responsibility, not auto-selected
    assert summary.model.mode == "unset"
    assert summary.model.provider == "unset"


def test_build_phase_reads_explicit_execution_and_model_assignments(tmp_path: Path) -> None:
    (tmp_path / "execution-assignment.md").write_text(
        "| Builder | cli | claude-code | workspaces/builder/ | - |\n",
        encoding="utf-8",
    )
    (tmp_path / "model-assignment.md").write_text(
        "| Builder | anthropic | claude-sonnet-4-6 | - | - |\n",
        encoding="utf-8",
    )

    summary = api._resolve_assignment_summary(tmp_path, "BUILD_NEEDED")

    assert summary.role == "builder"
    assert summary.execution.mode == "explicit"
    assert summary.execution.execution_type == "cli"
    assert summary.execution.target == "claude-code"
    assert summary.execution.workspace == "workspaces/builder/"
    assert summary.model.mode == "explicit"
    assert summary.model.provider == "anthropic"
    assert summary.model.model == "claude-sonnet-4-6"


def test_build_phase_cli_execution_without_model_assignment_returns_wrapper_backed(tmp_path: Path) -> None:
    (tmp_path / "execution-assignment.md").write_text(
        "| Builder | cli | claude-code | workspaces/builder/ | - |\n",
        encoding="utf-8",
    )
    # no model-assignment.md

    summary = api._resolve_assignment_summary(tmp_path, "BUILD_NEEDED")

    assert summary.role == "builder"
    assert summary.execution.execution_type == "cli"
    assert summary.model.mode == "wrapper-backed"
    assert summary.model.provider == "claude-code"


def test_review_phase_uses_provider_default_model_when_model_is_blank(tmp_path: Path) -> None:
    (tmp_path / "model-assignment.md").write_text(
        "| Critic | openai |  | - | - |\n",
        encoding="utf-8",
    )

    summary = api._resolve_assignment_summary(tmp_path, "REVIEW_NEEDED")

    assert summary.role == "critic"
    assert summary.model.mode == "default"
    assert summary.model.provider == "openai"
    assert summary.model.model == "gpt-4o"


def test_collect_run_detail_includes_assignment_summary(tmp_path: Path) -> None:
    run_dir = tmp_path / "run-090"
    run_dir.mkdir()
    (run_dir / "execution-assignment.md").write_text(
        "| Planner | cli | claude | workspaces/planner/ | - |\n",
        encoding="utf-8",
    )
    (run_dir / "goal.md").write_text(
        "Build the assignment visibility surface for the Agent OS tab.\n"
        "Focus on the Viewer API and frontend only.\n"
        "The existing specialist_visibility contract must not be broken.\n"
        "Non-goal: changing the wrapper or CLI.\n",
        encoding="utf-8",
    )

    detail = api._collect_run_detail("fw-improvement", "fw-improvement/run-090", run_dir)

    assert detail.assignment_summary.phase == detail.phase
    assert detail.assignment_summary.role == "planner"
    assert detail.assignment_summary.execution.execution_type in ("cli", "human", "future-api", "not_applicable")
    assert detail.assignment_summary.model.mode in ("explicit", "default", "human", "auto", "wrapper-backed", "unset", "not_applicable")
