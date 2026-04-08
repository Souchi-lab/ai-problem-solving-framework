"""Tests for _resolve_specialist_visibility in the viewer API.

run-083: specialist gap surfacing — verify that the visibility contract
(explicit / inferred / unresolved / not_applicable / has_gap) is correct.
run-088: Builder specialist surfacing — BUILD_NEEDED added to specialist phases.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from apsf.viewer import api

# Reuse the existing fixture framework root (has bugfix-planner.md and design-planner.md)
FIXTURE_FRAMEWORK = Path(__file__).parent / "fixtures" / "specialist_selection"


# ── not_applicable ────────────────────────────────────────────────────────────

@pytest.mark.parametrize("phase", ["ADOPT_NEEDED", "RESULT_NEEDED", "SETUP_NEEDED", "GOAL_NEEDED"])
def test_non_specialist_phases_return_not_applicable(tmp_path: Path, phase: str) -> None:
    vis = api._resolve_specialist_visibility(tmp_path, phase, FIXTURE_FRAMEWORK)
    assert vis.mode == "not_applicable"
    assert vis.has_gap is False


# ── unresolved (gap) ──────────────────────────────────────────────────────────

def test_plan_needed_with_no_files_returns_unresolved(tmp_path: Path) -> None:
    """No goal.md and no assignment → no specialist match → unresolved gap."""
    vis = api._resolve_specialist_visibility(tmp_path, "PLAN_NEEDED", FIXTURE_FRAMEWORK)
    assert vis.mode == "unresolved"
    assert vis.has_gap is True
    assert vis.specialist_code == ""


def test_review_needed_with_no_files_returns_unresolved(tmp_path: Path) -> None:
    vis = api._resolve_specialist_visibility(tmp_path, "REVIEW_NEEDED", FIXTURE_FRAMEWORK)
    assert vis.mode == "unresolved"
    assert vis.has_gap is True


# ── explicit ──────────────────────────────────────────────────────────────────

def test_explicit_ptype_in_assignment_returns_explicit(tmp_path: Path) -> None:
    """P-TYPE explicitly set in execution-assignment.md → mode=explicit, no gap."""
    (tmp_path / "goal.md").write_text("Fix a bug in the authentication flow.", encoding="utf-8")
    (tmp_path / "execution-assignment.md").write_text(
        "## Planner Specialist\n- Primary P-TYPE: P-02\n",
        encoding="utf-8",
    )
    vis = api._resolve_specialist_visibility(tmp_path, "PLAN_NEEDED", FIXTURE_FRAMEWORK)
    assert vis.mode == "explicit"
    assert vis.specialist_code == "P-02"
    assert vis.has_gap is False


def test_explicit_none_ptype_returns_explicit_no_gap(tmp_path: Path) -> None:
    """Explicit 'none/generic' assignment → explicit mode, no gap (intentional choice)."""
    (tmp_path / "execution-assignment.md").write_text(
        "## Planner Specialist\n- Primary P-TYPE: none\n",
        encoding="utf-8",
    )
    vis = api._resolve_specialist_visibility(tmp_path, "PLAN_NEEDED", FIXTURE_FRAMEWORK)
    assert vis.mode == "explicit"
    assert vis.has_gap is False


# ── inferred ──────────────────────────────────────────────────────────────────

def test_inferred_from_goal_keywords(tmp_path: Path) -> None:
    """Goal text with strong design keywords → inferred selection, no gap."""
    (tmp_path / "goal.md").write_text(
        "We need to compare options, define handoff, and decide the design direction.",
        encoding="utf-8",
    )
    vis = api._resolve_specialist_visibility(tmp_path, "PLAN_NEEDED", FIXTURE_FRAMEWORK)
    assert vis.mode == "inferred"
    assert vis.has_gap is False
    assert vis.specialist_code != ""


# ── has_gap: explicit + missing file ─────────────────────────────────────────

def test_explicit_with_missing_specialist_file_has_gap(tmp_path: Path) -> None:
    """Explicit P-TYPE that maps to a non-existent file → has_gap=True."""
    (tmp_path / "goal.md").write_text("Some goal.", encoding="utf-8")
    (tmp_path / "execution-assignment.md").write_text(
        "## Planner Specialist\n- Primary P-TYPE: P-99\n",  # P-99 not in registry
        encoding="utf-8",
    )
    # P-99 is not in PTYPE_TO_SPECIALIST, so specialist_path is None → content is ""
    vis = api._resolve_specialist_visibility(tmp_path, "PLAN_NEEDED", FIXTURE_FRAMEWORK)
    # P-99 is not registered → treated as unresolved by the registry (no mapping)
    # OR explicit with empty content — either way has_gap should be True
    assert vis.has_gap is True


# ── BUILD_NEEDED specialist visibility (run-088) ──────────────────────────────

def test_build_needed_with_no_files_returns_unresolved(tmp_path: Path) -> None:
    """BUILD_NEEDED with no goal.md / assignment → unresolved gap."""
    vis = api._resolve_specialist_visibility(tmp_path, "BUILD_NEEDED", Path("."))
    assert vis.mode == "unresolved"
    assert vis.has_gap is True
    assert vis.specialist_code == ""


def test_build_needed_explicit_btype_returns_explicit(tmp_path: Path) -> None:
    """Explicit B-TYPE in execution-assignment.md → mode=explicit, correct code."""
    (tmp_path / "goal.md").write_text("Polish the UI layout and improve responsiveness.", encoding="utf-8")
    (tmp_path / "execution-assignment.md").write_text(
        "## Builder Specialist\n- Primary B-TYPE: B-04\n",
        encoding="utf-8",
    )
    vis = api._resolve_specialist_visibility(tmp_path, "BUILD_NEEDED", Path("."))
    assert vis.mode == "explicit"
    assert vis.specialist_code == "B-04"
    assert vis.has_gap is False


def test_build_needed_explicit_none_returns_explicit_no_gap(tmp_path: Path) -> None:
    """Explicit 'none' B-TYPE → mode=explicit, no gap (intentional generic choice)."""
    (tmp_path / "execution-assignment.md").write_text(
        "## Builder Specialist\n- Primary B-TYPE: none\n",
        encoding="utf-8",
    )
    vis = api._resolve_specialist_visibility(tmp_path, "BUILD_NEEDED", Path("."))
    assert vis.mode == "explicit"
    assert vis.has_gap is False


def test_build_needed_inferred_from_goal_keywords(tmp_path: Path) -> None:
    """Goal text with build keywords → inferred B-TYPE, no gap."""
    (tmp_path / "goal.md").write_text(
        "Fix a reproducible regression where state mismatch causes a broken flow.",
        encoding="utf-8",
    )
    vis = api._resolve_specialist_visibility(tmp_path, "BUILD_NEEDED", Path("."))
    assert vis.mode == "inferred"
    assert vis.specialist_code != ""
    assert vis.has_gap is False


def test_build_needed_explicit_unknown_btype_has_gap(tmp_path: Path) -> None:
    """Explicit B-TYPE not in registry → has_gap=True."""
    (tmp_path / "goal.md").write_text("Some build task.", encoding="utf-8")
    (tmp_path / "execution-assignment.md").write_text(
        "## Builder Specialist\n- Primary B-TYPE: B-99\n",
        encoding="utf-8",
    )
    vis = api._resolve_specialist_visibility(tmp_path, "BUILD_NEEDED", Path("."))
    assert vis.has_gap is True


# ── run_detail integration ────────────────────────────────────────────────────

def test_collect_run_detail_includes_specialist_visibility(tmp_path: Path) -> None:
    """RunDetail includes specialist_visibility field."""
    run_dir = tmp_path / "run-083"
    run_dir.mkdir()
    (run_dir / "run_state.json").write_text(
        json.dumps({
            "run_id": "run-083",
            "current_phase": "PLAN_NEEDED",
            "phase_status": "pending",
            "current_owner": "Planner",
            "retry_count": 0,
            "last_error": "",
            "active_handoff_id": "",
            "gate_failures": [],
        }),
        encoding="utf-8",
    )
    (run_dir / "goal.md").write_text("Fix a bug in authentication.", encoding="utf-8")

    detail = api._collect_run_detail("fw-improvement", "fw-improvement/run-083", run_dir)

    assert hasattr(detail, "specialist_visibility")
    # phase matches what PhaseDetector reported for this run_dir
    assert detail.specialist_visibility.phase == detail.phase
    assert detail.specialist_visibility.mode in ("explicit", "inferred", "unresolved", "not_applicable")
    assert isinstance(detail.specialist_visibility.has_gap, bool)
