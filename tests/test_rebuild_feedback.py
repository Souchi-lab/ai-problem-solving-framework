from __future__ import annotations

import pytest

from apsf.core.ownership import (
    BlockerOwnership,
    CanonicalOwnershipResolver,
    OwnershipResolutionState,
    TransitionOutcomeCorrupt,
    TransitionOutcomeMissing,
    TransitionOutcomeSuperseded,
    TransitionOutcomeRecord,
    TransitionType,
    write_transition_outcome,
)
from apsf.core.state.transition_service import TransitionService
from apsf.legacy.orchestration.rebuild_feedback import (
    build_review_needs_refresh,
    detect_human_owned_blocker,
    generate_build_review_from_review,
    get_build_gate_decision,
    get_blocker_ownership_decision,
    iter_build_blocker_sources,
)


def test_detect_human_owned_blocker_returns_actions() -> None:
    review = "\n".join(
        [
            "**Verdict: CONDITIONAL PASS — Critical human-owned blocker persists**",
            "",
            "**Required action (human-owned):**",
            "Option (a): Register J-Quants free account and run a live API test.",
            "Option (b): Goal-owner formal sign-off for design-confirmed closure.",
            "",
            "Neither option is Builder-executable.",
            "No further Builder action is warranted until a human-owned prerequisite is completed.",
        ]
    )

    blocker = detect_human_owned_blocker(review)

    assert blocker is not None
    assert "Human-owned blocker detected" in blocker["summary"]
    assert any("builder-executable" in evidence for evidence in blocker["evidence"])
    assert len(blocker["actions"]) == 2


def test_generate_build_review_from_review_includes_human_blocker_and_major_issues() -> None:
    review = "\n".join(
        [
            "**Verdict: CONDITIONAL PASS — Critical human-owned blocker persists; contract structurally sound**",
            "",
            "### CRITICAL Issues",
            "#### C-1 — Criterion 3 Formally Unconfirmed",
            "**Required action (human-owned):**",
            "Option (a): Register J-Quants free account.",
            "Option (b): Goal-owner sign-off.",
            "Neither option is Builder-executable.",
            "",
            "### MAJOR Issues",
            "#### M-1 — 3rd ETF Is Provisional",
            "#### M-2 — Universe Selection Is Provisional",
            "",
            "### Minor Issues",
            "#### m-1 — AdjustedClose fallback is untested",
        ]
    )

    build_review = generate_build_review_from_review(review)

    assert "Review verdict: CONDITIONAL PASS" in build_review
    assert "Human-owned blocker is present" in build_review
    assert "C-1 — Criterion 3 Formally Unconfirmed" in build_review
    assert "M-1 — 3rd ETF Is Provisional" in build_review
    assert "Human follow-up: Register J-Quants free account." in build_review
    assert "Write the canonical build record to build.md." in build_review


def test_build_review_needs_refresh_for_default_template_with_rerun_comment() -> None:
    existing = "\n".join(
        [
            "# Build Review",
            "",
            "## Summary",
            "",
            "- ",
            "",
            "## Requested Revisions",
            "",
            "1. ",
            "2. ",
            "3. ",
            "",
            "## Findings",
            "",
            "### Critical",
            "",
            "- None",
            "",
            "### Major",
            "",
            "- ",
            "",
            "### Minor",
            "",
            "- ",
            "",
            "## Rerun Comment",
            "",
            "Judge advisory: Revise -> Judge and Return to Build",
        ]
    )

    assert build_review_needs_refresh(existing) is True


def test_detect_human_owned_blocker_text_parser_no_longer_treats_judge_override_as_authority() -> None:
    review = "\n".join(
        [
            "**Verdict: CONDITIONAL PASS - Critical human-owned blocker persists**",
            "",
            "Neither option is Builder-executable.",
            "",
            "## Rerun Comment",
            "<!-- 2026-04-07 Judge decision -->",
            "",
            "**Judge 判断: BUILD_NEEDED**",
            "",
            "Builder への指示:",
            "1. v2 endpoint に統一",
            "2. contract を更新",
            "",
            "これらが完了すれば Critical は解消し、Review に進める。",
        ]
    )

    assert detect_human_owned_blocker(review) is not None


def test_iter_build_blocker_sources_prefers_build_review(tmp_path) -> None:
    run_dir = tmp_path / "run-001"
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "build_review.md").write_text("build review", encoding="utf-8")
    (run_dir / "review_rerun_20260407_211934.md").write_text("review rerun", encoding="utf-8")

    sources = iter_build_blocker_sources(run_dir)

    assert [name for name, _ in sources] == [
        "build_review.md",
        "review_rerun_20260407_211934.md",
    ]


def test_canonical_resolver_raises_when_transition_record_is_missing(tmp_path) -> None:
    run_dir = tmp_path / "run-missing"
    run_dir.mkdir(parents=True, exist_ok=True)

    with pytest.raises(TransitionOutcomeMissing):
        CanonicalOwnershipResolver().resolve(run_dir)


def test_canonical_resolver_raises_when_transition_record_is_corrupt(tmp_path) -> None:
    run_dir = tmp_path / "run-corrupt"
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "transition_outcome.json").write_text("{not-json}", encoding="utf-8")

    with pytest.raises(TransitionOutcomeCorrupt):
        CanonicalOwnershipResolver().resolve(run_dir)


def test_canonical_resolver_raises_when_transition_record_is_superseded_by_current_phase(tmp_path) -> None:
    run_dir = tmp_path / "run-superseded"
    run_dir.mkdir(parents=True, exist_ok=True)
    TransitionService().bootstrap(
        run_dir,
        run_id=run_dir.name,
        initial_phase="RESULT_NEEDED",
        actor="system",
        reason="bootstrap test",
    )
    write_transition_outcome(
        run_dir,
        TransitionOutcomeRecord(
            run_id=run_dir.name,
            transition_type=TransitionType.HUMAN_BLOCKED,
            transitioned_at="2026-04-09T00:00:00+00:00",
            transitioned_by="Judge",
            blocker_owner=BlockerOwnership.HUMAN,
            source_phase="IMPROVE_NEEDED",
            target_phase="IMPROVE_NEEDED",
        ),
    )

    with pytest.raises(TransitionOutcomeSuperseded):
        CanonicalOwnershipResolver().resolve(run_dir)


def test_detect_human_owned_blocker_is_cleared_by_system_transition_record(tmp_path) -> None:
    run_dir = tmp_path / "run-system-owned"
    run_dir.mkdir(parents=True, exist_ok=True)
    write_transition_outcome(
        run_dir,
        TransitionOutcomeRecord(
            run_id=run_dir.name,
            transition_type=TransitionType.BUILD_NEEDED,
            transitioned_at="2026-04-09T00:00:00+00:00",
            transitioned_by="Judge",
            blocker_owner=BlockerOwnership.SYSTEM,
            source_phase="REVIEW_NEEDED",
            target_phase="BUILD_NEEDED",
        ),
    )

    review = "\n".join(
        [
            "**Verdict: CONDITIONAL PASS - Critical human-owned blocker persists**",
            "",
            "**Required action (human-owned):**",
            "Option (a): Register J-Quants free account and run a live API test.",
            "Neither option is Builder-executable.",
        ]
    )

    assert detect_human_owned_blocker(review, run_dir=run_dir) is None


def test_detect_human_owned_blocker_returns_canonical_human_blocker_without_text_heuristic(tmp_path) -> None:
    run_dir = tmp_path / "run-human-canonical-only"
    run_dir.mkdir(parents=True, exist_ok=True)
    write_transition_outcome(
        run_dir,
        TransitionOutcomeRecord(
            run_id=run_dir.name,
            transition_type=TransitionType.HUMAN_BLOCKED,
            transitioned_at="2026-04-09T00:00:00+00:00",
            transitioned_by="Judge",
            blocker_owner=BlockerOwnership.HUMAN,
            source_phase="IMPROVE_NEEDED",
            target_phase="IMPROVE_NEEDED",
        ),
    )

    blocker = detect_human_owned_blocker("Judge requested manual approval.\n- Goal-owner sign-off", run_dir=run_dir)

    assert blocker is not None
    assert blocker["summary"] == "Human-owned blocker detected from the canonical transition outcome record."
    assert blocker["evidence"] == ["transition_outcome.json:blocker_owner=HUMAN"]


def test_get_blocker_ownership_decision_returns_unrecorded_without_review_text_fallback(tmp_path) -> None:
    run_dir = tmp_path / "run-unrecorded"
    run_dir.mkdir(parents=True, exist_ok=True)

    decision = get_blocker_ownership_decision(
        "**Verdict: CONDITIONAL PASS - Critical human-owned blocker persists**",
        run_dir=run_dir,
    )

    assert decision["owner"] == OwnershipResolutionState.UNRECORDED.value
    assert decision["blocker"] is None


def test_get_blocker_ownership_decision_returns_corrupt_without_review_text_fallback(tmp_path) -> None:
    run_dir = tmp_path / "run-corrupt-status"
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "transition_outcome.json").write_text("{bad json}", encoding="utf-8")

    decision = get_blocker_ownership_decision(
        "**Required action (human-owned):**\nOption (a): Goal-owner sign-off.",
        run_dir=run_dir,
    )

    assert decision["owner"] == OwnershipResolutionState.CORRUPT.value
    assert decision["blocker"] is None


def test_get_blocker_ownership_decision_returns_superseded_without_review_text_fallback(tmp_path) -> None:
    run_dir = tmp_path / "run-superseded-status"
    run_dir.mkdir(parents=True, exist_ok=True)
    TransitionService().bootstrap(
        run_dir,
        run_id=run_dir.name,
        initial_phase="BUILD_NEEDED",
        actor="system",
        reason="bootstrap test",
    )
    write_transition_outcome(
        run_dir,
        TransitionOutcomeRecord(
            run_id=run_dir.name,
            transition_type=TransitionType.HUMAN_BLOCKED,
            transitioned_at="2026-04-09T00:00:00+00:00",
            transitioned_by="Judge",
            blocker_owner=BlockerOwnership.HUMAN,
            source_phase="REVIEW_NEEDED",
            target_phase="REVIEW_NEEDED",
        ),
    )

    decision = get_blocker_ownership_decision(
        "**Required action (human-owned):**\nOption (a): Goal-owner sign-off.",
        run_dir=run_dir,
    )

    assert decision["owner"] == OwnershipResolutionState.SUPERSEDED.value
    assert decision["blocker"] is None


def test_get_build_gate_decision_fails_closed_for_unrecorded_authority(tmp_path) -> None:
    run_dir = tmp_path / "run-build-gate-unrecorded"
    run_dir.mkdir(parents=True, exist_ok=True)

    decision = get_build_gate_decision(run_dir)

    assert decision["status"] == OwnershipResolutionState.UNRECORDED.value
    assert decision["policy"] == "FAIL_CLOSED"
    assert decision["allow_build"] is False
    assert "unrecorded" in str(decision["summary"]).lower()


def test_get_build_gate_decision_fails_closed_for_corrupt_authority(tmp_path) -> None:
    run_dir = tmp_path / "run-build-gate-corrupt"
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "transition_outcome.json").write_text("{bad json}", encoding="utf-8")

    decision = get_build_gate_decision(run_dir)

    assert decision["status"] == OwnershipResolutionState.CORRUPT.value
    assert decision["policy"] == "FAIL_CLOSED"
    assert decision["allow_build"] is False
    assert "corrupt" in str(decision["summary"]).lower()


def test_get_build_gate_decision_returns_superseded_as_explicit_proceed_state(tmp_path) -> None:
    run_dir = tmp_path / "run-build-gate-superseded"
    run_dir.mkdir(parents=True, exist_ok=True)
    TransitionService().bootstrap(
        run_dir,
        run_id=run_dir.name,
        initial_phase="BUILD_NEEDED",
        actor="system",
        reason="bootstrap test",
    )
    write_transition_outcome(
        run_dir,
        TransitionOutcomeRecord(
            run_id=run_dir.name,
            transition_type=TransitionType.HUMAN_BLOCKED,
            transitioned_at="2026-04-09T00:00:00+00:00",
            transitioned_by="Judge",
            blocker_owner=BlockerOwnership.HUMAN,
            source_phase="REVIEW_NEEDED",
            target_phase="REVIEW_NEEDED",
        ),
    )

    decision = get_build_gate_decision(run_dir)

    assert decision["status"] == OwnershipResolutionState.SUPERSEDED.value
    assert decision["policy"] == "PROCEED"
    assert decision["allow_build"] is True


def test_get_build_gate_decision_distinguishes_system_from_invalid_states(tmp_path) -> None:
    system_run = tmp_path / "run-build-gate-system"
    system_run.mkdir(parents=True, exist_ok=True)
    write_transition_outcome(
        system_run,
        TransitionOutcomeRecord(
            run_id=system_run.name,
            transition_type=TransitionType.BUILD_NEEDED,
            transitioned_at="2026-04-09T00:00:00+00:00",
            transitioned_by="Judge",
            blocker_owner=BlockerOwnership.SYSTEM,
            source_phase="REVIEW_NEEDED",
            target_phase="BUILD_NEEDED",
        ),
    )
    invalid_run = tmp_path / "run-build-gate-invalid"
    invalid_run.mkdir(parents=True, exist_ok=True)

    system_decision = get_build_gate_decision(system_run)
    invalid_decision = get_build_gate_decision(invalid_run)

    assert system_decision["status"] == OwnershipResolutionState.SYSTEM.value
    assert system_decision["policy"] == "PROCEED"
    assert system_decision["allow_build"] is True
    assert invalid_decision["status"] == OwnershipResolutionState.UNRECORDED.value
    assert invalid_decision["policy"] == "FAIL_CLOSED"
    assert invalid_decision["allow_build"] is False


def test_canonical_resolver_returns_human_owner(tmp_path) -> None:
    run_dir = tmp_path / "run-human-owned"
    run_dir.mkdir(parents=True, exist_ok=True)
    write_transition_outcome(
        run_dir,
        TransitionOutcomeRecord(
            run_id=run_dir.name,
            transition_type=TransitionType.HUMAN_BLOCKED,
            transitioned_at="2026-04-09T00:00:00+00:00",
            transitioned_by="human",
            blocker_owner=BlockerOwnership.HUMAN,
            source_phase="REVIEW_NEEDED",
            target_phase="REVIEW_NEEDED",
        ),
    )

    assert CanonicalOwnershipResolver().resolve(run_dir) is BlockerOwnership.HUMAN


def test_detect_human_owned_blocker_is_re_evaluated_after_human_blocked_returns_to_review(tmp_path) -> None:
    run_dir = tmp_path / "run-review-cycle-reset"
    run_dir.mkdir(parents=True, exist_ok=True)
    service = TransitionService()
    service.bootstrap(
        run_dir,
        run_id=run_dir.name,
        initial_phase="REVIEW_NEEDED",
        actor="system",
        reason="bootstrap test",
    )
    write_transition_outcome(
        run_dir,
        TransitionOutcomeRecord(
            run_id=run_dir.name,
            transition_type=TransitionType.HUMAN_BLOCKED,
            transitioned_at="2026-04-09T00:00:00+00:00",
            transitioned_by="Judge",
            blocker_owner=BlockerOwnership.HUMAN,
            source_phase="REVIEW_NEEDED",
            target_phase="REVIEW_NEEDED",
        ),
    )

    review = "\n".join(
        [
            "**Verdict: CONDITIONAL PASS - Critical human-owned blocker persists**",
            "",
            "**Required action (human-owned):**",
            "Option (a): Goal-owner sign-off.",
        ]
    )
    assert detect_human_owned_blocker(review, run_dir=run_dir) is not None

    service.transition(
        run_dir,
        to_phase="BUILD_NEEDED",
        actor="Judge",
        reason="return to build",
    )
    assert detect_human_owned_blocker(review, run_dir=run_dir) is None

    service.transition(
        run_dir,
        to_phase="REVIEW_NEEDED",
        actor="Builder",
        reason="review cycle restarted",
    )
    decision = get_blocker_ownership_decision(review, run_dir=run_dir)

    assert decision["owner"] == OwnershipResolutionState.UNRECORDED.value
    assert decision["blocker"] is None
