from __future__ import annotations

from apsf.legacy.orchestration.rebuild_feedback import (
    build_review_needs_refresh,
    detect_human_owned_blocker,
    generate_build_review_from_review,
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


def test_detect_human_owned_blocker_is_cleared_by_judge_build_override() -> None:
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

    assert detect_human_owned_blocker(review) is None


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
