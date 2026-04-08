from pathlib import Path

from apsf.legacy.cli.specialist_registry import (
    extract_section,
    resolve_builder_specialist,
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


# ── Builder specialist selection ──────────────────────────────────────────────

def test_resolve_builder_specialist_prefers_explicit_btype() -> None:
    assignment = "## Builder Specialist\n- Primary B-TYPE: B-04 Frontend / UX Polish\n"
    goal = "Polish the viewer layout and improve spacing consistency."
    decision = resolve_builder_specialist(goal, assignment, FIXTURES)
    assert decision.mode == "explicit"
    assert decision.ptype == "B-04"
    assert "explicit Primary B-TYPE" in decision.reason


def test_resolve_builder_specialist_explicit_b02() -> None:
    assignment = "## Builder Specialist\n- Primary B-TYPE: B-02 Bug Fix\n"
    goal = "Fix the broken authentication flow regression."
    decision = resolve_builder_specialist(goal, assignment, Path("."))
    assert decision.mode == "explicit"
    assert decision.ptype == "B-02"


def test_resolve_builder_specialist_infers_bugfix_from_repo_files() -> None:
    goal = (
        "Fix a reproducible regression where state mismatch causes a broken flow. "
        "Localize the defect, apply a minimal correction, and add a regression test."
    )
    decision = resolve_builder_specialist(goal, "", Path("."))
    assert decision.mode == "inferred"
    assert decision.ptype == "B-02"


def test_resolve_builder_specialist_infers_refactor_from_repo_files() -> None:
    goal = (
        "Refactor the import structure, move files to their canonical locations, "
        "and consolidate duplicated logic into a single module."
    )
    decision = resolve_builder_specialist(goal, "", Path("."))
    assert decision.mode == "inferred"
    assert decision.ptype == "B-03"


def test_resolve_builder_specialist_infers_frontend_polish_from_repo_files() -> None:
    goal = (
        "Polish the UI layout: adjust spacing, fix typography inconsistencies, "
        "and improve responsive breakpoint behavior on mobile."
    )
    decision = resolve_builder_specialist(goal, "", Path("."))
    assert decision.mode == "inferred"
    assert decision.ptype == "B-04"


def test_resolve_builder_specialist_infers_deploy_from_repo_files() -> None:
    goal = (
        "Deploy the preview build to the staging environment and confirm the artifact "
        "is accessible at the expected URL."
    )
    decision = resolve_builder_specialist(goal, "", Path("."))
    assert decision.mode == "inferred"
    assert decision.ptype == "B-05"


def test_resolve_builder_specialist_infers_validation_probe_from_repo_files() -> None:
    goal = (
        "Run smoke tests and probe the round-trip validation sequence. "
        "Record results and make minimal corrective changes based on probe findings."
    )
    decision = resolve_builder_specialist(goal, "", Path("."))
    assert decision.mode == "inferred"
    assert decision.ptype == "B-06"


def test_resolve_builder_specialist_infers_content_static_from_repo_files() -> None:
    goal = (
        "Update the static HTML copy, revise documentation content, "
        "and fix formatting in the generated asset manifest."
    )
    decision = resolve_builder_specialist(goal, "", Path("."))
    assert decision.mode == "inferred"
    assert decision.ptype == "B-07"


def test_resolve_builder_specialist_explicit_none_returns_generic() -> None:
    assignment = "## Builder Specialist\n- Primary B-TYPE: none\n"
    goal = "Some build task."
    decision = resolve_builder_specialist(goal, assignment, Path("."))
    assert decision.mode == "explicit"
    assert decision.ptype == ""
