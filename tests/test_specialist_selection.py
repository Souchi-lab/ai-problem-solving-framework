from pathlib import Path

from apsf.cli.specialist_registry import (
    extract_section,
    resolve_critic_specialist,
    resolve_planner_specialist,
    selection_sections,
)


def test_extract_section_returns_expected_body() -> None:
    text = (
        "# Specialist\n\n"
        "## Scope\n\n"
        "bug fix expected actual\n\n"
        "## Out of Scope\n\n"
        "new feature\n"
    )
    assert "expected actual" in extract_section(text, "Scope")
    assert "new feature" in extract_section(text, "Out of Scope")


def test_selection_sections_extract_core_fields() -> None:
    text = (
        "## Scope\n\ncompare expected actual\n\n"
        "## Out of Scope\n\ndesign only\n\n"
        "## Evaluation Criteria\n\nroot cause localization\n"
    )
    sections = selection_sections(text)
    assert "expected actual" in sections["scope"]
    assert "design only" in sections["out_of_scope"]
    assert "root cause" in sections["evaluation_criteria"]


FIXTURES = Path(__file__).parent / "fixtures" / "specialist_selection"


def test_resolve_planner_specialist_prefers_explicit_ptype() -> None:
    assignment = "## Planner Specialist\n- Primary P-TYPE: P-02 Bug Fix\n"
    goal = "A bug fix plan should compare expected actual behavior and localize the cause."
    decision = resolve_planner_specialist(goal, assignment, FIXTURES)
    assert decision.mode == "explicit"
    assert decision.ptype == "P-02"
    assert "explicit Primary P-TYPE" in decision.reason


def test_resolve_planner_specialist_can_infer_when_missing() -> None:
    goal = "We need to compare options, define handoff, and decide the design direction."
    decision = resolve_planner_specialist(goal, "", FIXTURES)
    assert decision.mode == "inferred"
    assert decision.ptype == "P-06"


def test_resolve_planner_specialist_can_infer_performance_from_repo_files() -> None:
    goal = "We need profiling, bottleneck analysis, and regression checks to improve endpoint latency."
    decision = resolve_planner_specialist(goal, "", Path("."))
    assert decision.mode == "inferred"
    assert decision.ptype == "P-10"


def test_resolve_planner_specialist_can_infer_dependency_upgrade_from_repo_files() -> None:
    goal = "Plan a framework version upgrade with breaking-change analysis, rollback guidance, and validation gates."
    decision = resolve_planner_specialist(goal, "", Path("."))
    assert decision.mode == "inferred"
    assert decision.ptype == "P-12"


def test_resolve_critic_specialist_prefers_explicit_ctype() -> None:
    assignment = "## Critic Specialist\n- Primary C-TYPE: C-02 Copy Clarity\n"
    goal = "Review labels, helper text, and status wording for consistency."
    decision = resolve_critic_specialist(goal, assignment, FIXTURES)
    assert decision.mode == "explicit"
    assert decision.ptype == "C-02"
    assert "explicit Primary C-TYPE" in decision.reason


def test_resolve_critic_specialist_can_infer_when_missing() -> None:
    goal = "Review the hero, CTA hierarchy, onboarding clarity, and section order."
    decision = resolve_critic_specialist(goal, "", FIXTURES)
    assert decision.mode == "inferred"
    assert decision.ptype == "C-01"


def test_resolve_critic_specialist_can_infer_bilingual_from_repo_files() -> None:
    goal = "Review Japanese and English switching, label width differences, and bilingual CTA balance in the UI."
    decision = resolve_critic_specialist(goal, "", Path("."))
    assert decision.mode == "inferred"
    assert decision.ptype == "C-05"


def test_resolve_critic_specialist_can_infer_empty_state_from_repo_files() -> None:
    goal = "Review empty lists, loading confusion, error recovery guidance, and next-step clarity after failed fetch."
    decision = resolve_critic_specialist(goal, "", Path("."))
    assert decision.mode == "inferred"
    assert decision.ptype == "C-04"


def test_resolve_critic_specialist_can_infer_product_positioning_from_repo_files() -> None:
    goal = (
        "Review whether the 2D mode should be a standalone product, onboarding layer, "
        "or companion, and whether its roadmap protects the current fun core."
    )
    decision = resolve_critic_specialist(goal, "", Path("."))
    assert decision.mode == "inferred"
    assert decision.ptype == "C-07"


def test_resolve_critic_specialist_can_infer_puzzle_difficulty_from_repo_files() -> None:
    goal = (
        "Review whether the puzzle difficulty curve is fair, whether players can feel "
        "they solved it before clicking, and whether answer checking preserves the payoff."
    )
    decision = resolve_critic_specialist(goal, "", Path("."))
    assert decision.mode == "inferred"
    assert decision.ptype == "C-08"
