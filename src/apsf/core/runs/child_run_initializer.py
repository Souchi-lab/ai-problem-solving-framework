from __future__ import annotations

from pathlib import Path

from apsf.core.state.transition_service import TransitionService
from apsf.legacy.storage.run_repository import RunRepository


def initialize_child_run(
    *,
    repo: RunRepository,
    parent_run: str,
    child_run: str,
    taxonomy: str | None,
    title: str,
    goal_text: str,
    force: bool = False,
) -> Path:
    child_dir = repo.init_child_run(
        parent_run,
        child_run,
        force=force,
        taxonomy=taxonomy,
    )
    TransitionService().bootstrap(
        child_dir,
        child_run,
        "GOAL_NEEDED",
        actor="system",
        reason="initialize_child_run: create canonical child run state",
        current_owner="Human",
    )
    (child_dir / "goal.md").write_text(
        _render_goal_markdown(
            goal_text=goal_text,
            title=title,
            parent_run=parent_run,
            child_run=child_run,
        ),
        encoding="utf-8",
    )
    return child_dir


def _render_goal_markdown(
    *,
    goal_text: str,
    title: str,
    parent_run: str,
    child_run: str,
) -> str:
    clean_goal = goal_text.strip() or "(goal not provided)"
    clean_title = title.strip() or child_run
    return (
        "# Goal\n\n"
        "## Goal Statement\n\n"
        f"{clean_goal}\n\n"
        "## Background\n\n"
        f"- Parent Run: `{parent_run}`\n"
        f"- Child Run: `{child_run}`\n"
        f"- Title: {clean_title}\n\n"
        "## Success Criteria\n\n"
        "- [ ] Goal statement is concrete enough for planning.\n"
        "- [ ] Deliverables and constraints are clarified during planning.\n"
        "- [ ] Parent/child context is preserved for downstream roles.\n\n"
        "## Notes\n\n"
        "- Initialized via `apsf init-child-run`.\n"
    )
