"""
tests/test_completion_semantics.py

RunRepository の is_completed / is_child_completed が state-first で動作することを検証する。

- run_state.json が存在する場合: current_phase が COMPLETE / TRANSCRIPT_RECOMMENDED → True
- run_state.json が存在しない場合: result.md exists でフォールバック
"""

import json
import pytest
from pathlib import Path

from apsf.legacy.storage.run_repository import RunRepository, STANDARD_FILES


# ---------------------------------------------------------------------------
# fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def template_dir(tmp_path: Path) -> Path:
    t = tmp_path / "_template"
    t.mkdir()
    for f in ["goal.md", "plan.md", "model-assignment.md"]:
        (t / f).write_text(f"# {f}\n", encoding="utf-8")
    return t


@pytest.fixture
def repo(tmp_path: Path, template_dir: Path) -> RunRepository:
    runs_dir = tmp_path / "runs"
    return RunRepository(runs_dir=runs_dir, template_dir=template_dir)


RUN_NAME = "2026-01-01_apsf_completion-semantics"
CHILD_PARENT = "2026-01-01_apsf_parent-run"
CHILD_NAME   = "001c1_apsf_child-run"


def _write_run_state(run_dir: Path, phase: str) -> None:
    """run_dir に run_state.json を書き込む（最小フィールド）。"""
    state = {
        "run_id": run_dir.name,
        "current_phase": phase,
        "phase_status": "PENDING",
        "current_owner": "Human",
        "retry_count": 0,
        "last_error": "",
        "active_handoff_id": "",
        "gate_failures": [],
    }
    (run_dir / "run_state.json").write_text(json.dumps(state), encoding="utf-8")


# ---------------------------------------------------------------------------
# is_completed — top-level run
# ---------------------------------------------------------------------------

def test_is_completed_returns_true_when_run_state_complete(repo: RunRepository, tmp_path: Path) -> None:
    """run_state.COMPLETE → True（result.md がなくても）"""
    run_dir = tmp_path / "runs" / RUN_NAME
    run_dir.mkdir(parents=True)
    _write_run_state(run_dir, "COMPLETE")

    assert repo.is_completed(RUN_NAME) is True


def test_is_completed_returns_true_when_transcript_recommended(repo: RunRepository, tmp_path: Path) -> None:
    """run_state.TRANSCRIPT_RECOMMENDED → True"""
    run_dir = tmp_path / "runs" / RUN_NAME
    run_dir.mkdir(parents=True)
    _write_run_state(run_dir, "TRANSCRIPT_RECOMMENDED")

    assert repo.is_completed(RUN_NAME) is True


def test_is_completed_returns_false_when_run_state_not_complete(repo: RunRepository, tmp_path: Path) -> None:
    """run_state.PLAN_NEEDED → False（result.md があっても run_state が優先）"""
    run_dir = tmp_path / "runs" / RUN_NAME
    run_dir.mkdir(parents=True)
    _write_run_state(run_dir, "PLAN_NEEDED")
    (run_dir / "result.md").write_text("# Result\n", encoding="utf-8")

    assert repo.is_completed(RUN_NAME) is False


def test_is_completed_fallback_to_result_md_when_no_state(repo: RunRepository, tmp_path: Path) -> None:
    """run_state.json なし + result.md あり → True（legacy fallback）"""
    run_dir = tmp_path / "runs" / RUN_NAME
    run_dir.mkdir(parents=True)
    (run_dir / "result.md").write_text("# Result\n", encoding="utf-8")

    assert repo.is_completed(RUN_NAME) is True


def test_is_completed_false_without_result_or_state(repo: RunRepository, tmp_path: Path) -> None:
    """run_state.json なし + result.md なし → False"""
    run_dir = tmp_path / "runs" / RUN_NAME
    run_dir.mkdir(parents=True)

    assert repo.is_completed(RUN_NAME) is False


# ---------------------------------------------------------------------------
# is_child_completed — child run
# ---------------------------------------------------------------------------

def test_is_child_completed_state_first(repo: RunRepository, tmp_path: Path) -> None:
    """child run で run_state.COMPLETE → True"""
    child_dir = tmp_path / "runs" / CHILD_PARENT / CHILD_NAME
    child_dir.mkdir(parents=True)
    _write_run_state(child_dir, "COMPLETE")

    assert repo.is_child_completed(CHILD_PARENT, CHILD_NAME) is True


def test_is_child_completed_fallback(repo: RunRepository, tmp_path: Path) -> None:
    """child run で run_state なし + result.md → True"""
    child_dir = tmp_path / "runs" / CHILD_PARENT / CHILD_NAME
    child_dir.mkdir(parents=True)
    (child_dir / "result.md").write_text("# Result\n", encoding="utf-8")

    assert repo.is_child_completed(CHILD_PARENT, CHILD_NAME) is True
