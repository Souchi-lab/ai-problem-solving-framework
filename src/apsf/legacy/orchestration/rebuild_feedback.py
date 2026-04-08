from __future__ import annotations

import re
from pathlib import Path


def _has_builder_resume_override(review_text: str) -> bool:
    lowered = review_text.lower()
    has_build_needed = "build_needed" in lowered or "return to build" in lowered
    has_judge_marker = "judge" in lowered and ("判断" in lowered or "decision" in lowered)
    has_builder_instruction = (
        "builder への指示" in lowered
        or "builderへの指示" in lowered
        or "builder instructions" in lowered
    )
    has_review_resume = (
        "review に進める" in lowered
        or "proceed to review" in lowered
    )
    return has_build_needed and (has_judge_marker or has_builder_instruction or has_review_resume)


def _extract_review_verdict(review_text: str) -> str | None:
    patterns = [
        r"\*\*Verdict:\s*(.+?)\*\*",
        r"\*\*判定[:：]\s*(.+?)\*\*",
        r"\*\*推奨[:：]\s*(.+?)\*\*",
        r"^##\s+Verdict[:：]?\s*$\s*(.+)$",
        r"^##\s+Disposition\s*$\s*(?:\n|.)*?^\s*-\s*(Accept|Accepted|Adopt|Revise|Reject)\s*$",
        r"^\*\*(ACCEPT|ADOPT|REVISE|REJECT)\*\*",
    ]
    for pattern in patterns:
        match = re.search(pattern, review_text, flags=re.IGNORECASE | re.MULTILINE)
        if match:
            verdict = match.group(1).strip()
            return verdict[:240] if verdict else None
    return None


def _extract_issue_titles(review_text: str, heading: str) -> list[str]:
    section = re.search(
        rf"^###\s+{re.escape(heading)}\s+Issues\s*$\n(?P<body>.*?)(?=^###\s+|\Z)",
        review_text,
        flags=re.IGNORECASE | re.MULTILINE | re.DOTALL,
    )
    if not section:
        return []
    body = section.group("body")
    titles = [match.strip() for match in re.findall(r"^####\s+(.+)$", body, flags=re.MULTILINE)]
    if titles:
        return titles
    inline = re.findall(r"^\s*-\s+(.+)$", body, flags=re.MULTILINE)
    cleaned: list[str] = []
    for item in inline:
        text = item.strip().strip("*").strip()
        if not text or text.lower() == "none" or text in {"なし", "縺ｪ縺・", "‚È‚µ"}:
            continue
        cleaned.append(text)
    return cleaned


def _extract_human_actions(review_text: str) -> list[str]:
    actions: list[str] = []
    for option in re.findall(r"Option\s+\([a-z]\):\s*(.+)", review_text, flags=re.IGNORECASE):
        normalized = option.strip()
        if normalized:
            actions.append(normalized)

    for bullet in re.findall(r"^\s*-\s+(.+)$", review_text, flags=re.MULTILINE):
        normalized = bullet.strip()
        if any(token in normalized.lower() for token in ("api key", "goal-owner", "goal owner", "sign-off", "sign off", "j-quants", "tos", "register")):
            actions.append(normalized)

    deduped: list[str] = []
    for action in actions:
        if action not in deduped:
            deduped.append(action)
    return deduped


def detect_human_owned_blocker(review_text: str) -> dict[str, object] | None:
    if _has_builder_resume_override(review_text):
        return None

    verdict = _extract_review_verdict(review_text)
    if verdict and re.search(r'\b(pass|accept|adopt)\b', verdict, re.IGNORECASE):
        # Only skip if the verdict does not simultaneously assert a human-owned blocker.
        # "CONDITIONAL PASS — human-owned blocker persists" still requires blocker detection.
        if not re.search(r'blocker|human.owned', verdict, re.IGNORECASE):
            return None

    lower_text = review_text.lower()
    builder_can_resolve_markers = (
        "build artifact has not been updated",
        "artifact not updated",
        "must be updated to incorporate",
        "update `docs/data_contract",
        "update docs/data_contract",
        "update the contract",
        "update the build record",
        "must be materialized into the contract",
        "write the confirmed",
        "reconcile",
        "document any known",
    )
    if any(marker in lower_text for marker in builder_can_resolve_markers):
        narrowed_text = review_text
    else:
        narrowed_text = review_text

    evidence_patterns = [
        r"human-owned blocker persists",
        r"required action \(human-owned\)",
        r"next required action \(human-gated\)",
        r"neither option is builder-executable",
        r"no further builder action is warranted until",
        r"builder authority exhausted",
        r"goal-owner[^\n]{0,80}sign-?off",
        r"goal owner[^\n]{0,80}sign-?off",
    ]

    evidence: list[str] = []
    lowered = narrowed_text.lower()
    for pattern in evidence_patterns:
        match = re.search(pattern, lowered, flags=re.IGNORECASE)
        if match:
            evidence.append(match.group(0))

    if not evidence:
        return None

    if any(marker in lowered for marker in builder_can_resolve_markers):
        human_only_patterns = [
            r"register j-?quants",
            r"obtain api key",
            r"read tos",
            r"goal-owner[^\n]{0,80}sign-?off",
            r"goal owner[^\n]{0,80}sign-?off",
        ]
        human_only_evidence = [
            match.group(0)
            for pattern in human_only_patterns
            for match in re.finditer(pattern, lowered, flags=re.IGNORECASE)
        ]
        if not human_only_evidence:
            return None
        evidence = human_only_evidence

    actions = _extract_human_actions(review_text)
    if any(marker in lowered for marker in builder_can_resolve_markers):
        narrowed_actions: list[str] = []
        for action in actions:
            action_lower = action.lower()
            if any(
                phrase in action_lower
                for phrase in ("template", "unpopulated", "must be materialized", "described as", "artifact.")
            ):
                continue
            if any(
                token in action_lower
                for token in ("register", "api key", "goal-owner", "goal owner", "sign-off", "sign off", "read tos", "read the tos")
            ):
                narrowed_actions.append(action)
        actions = narrowed_actions
        if not actions:
            return None

    return {
        "summary": "Human-owned blocker detected; Builder rerun is unlikely to resolve the current gate.",
        "evidence": evidence,
        "actions": actions,
    }


def _strip_rerun_comments(text: str) -> str:
    """Remove all ## Rerun Comment sections from build_review.md text.

    Rerun Comments accumulate historical Judge/wrapper feedback and often contain
    patterns (e.g. "goal-owner sign-off", "BUILD_NEEDED") that trigger false-positive
    blocker detection. Only the static sections of build_review.md are authoritative
    for blocker analysis.
    """
    return re.sub(
        r"\n## Rerun Comment\n.*?(?=\n## Rerun Comment\n|\Z)",
        "",
        text,
        flags=re.DOTALL,
    ).strip()


def iter_build_blocker_sources(run_dir: Path) -> list[tuple[str, str]]:
    sources: list[tuple[str, str]] = []

    build_review = run_dir / "build_review.md"
    build_review_text: str | None = None
    if build_review.exists():
        raw = build_review.read_text(encoding="utf-8")
        build_review_text = _strip_rerun_comments(raw)
        sources.append((build_review.name, build_review_text))

    # If build_review.md (stripped) contains a Judge-issued build-resume override,
    # skip the review artifact check — the Judge decision supersedes the Critic.
    if build_review_text is not None and _has_builder_resume_override(build_review_text):
        return sources

    review_path = latest_review_artifact(run_dir)
    if review_path is not None:
        sources.append((review_path.name, review_path.read_text(encoding="utf-8")))

    return sources


def latest_review_artifact(run_dir: Path) -> Path | None:
    canonical = run_dir / "review.md"
    if canonical.exists():
        return canonical

    reruns = sorted(run_dir.glob("review_rerun_*.md"), key=lambda path: path.stat().st_mtime, reverse=True)
    return reruns[0] if reruns else None


def build_review_needs_refresh(existing_text: str) -> bool:
    text = existing_text.strip()
    if not text:
        return True

    text = re.sub(
        r"\n## Rerun Comment\n.*?(?=\n## Rerun Comment\n|\Z)",
        "",
        text,
        flags=re.DOTALL,
    ).strip()

    if "## Requested Revisions" not in text:
        return False

    def _section_body(heading: str) -> str:
        match = re.search(
            rf"^##\s+{re.escape(heading)}\s*$\n(?P<body>.*?)(?=^##\s+|\Z)",
            text,
            flags=re.MULTILINE | re.DOTALL,
        )
        return match.group("body").strip() if match else ""

    summary_body = _section_body("Summary")
    revisions_body = _section_body("Requested Revisions")
    findings_body = _section_body("Findings")

    summary_lines = [line.strip() for line in summary_body.splitlines() if line.strip() and line.strip() != "---"]
    summary_is_placeholder = not summary_lines or summary_lines == ["-"]

    revision_lines = [line.strip() for line in revisions_body.splitlines() if line.strip() and line.strip() != "---"]
    revisions_are_placeholder = all(line in {"1.", "2.", "3."} for line in revision_lines) if revision_lines else True

    finding_lines = [line.strip() for line in findings_body.splitlines() if line.strip() and line.strip() != "---"]
    substantive_findings = [
        line for line in finding_lines
        if line.startswith("- ")
        and line not in {"- None", "- なし", "- 縺ｪ縺・", "- ‚È‚µ", "-"}
    ]

    return summary_is_placeholder and revisions_are_placeholder and not substantive_findings


def generate_build_review_from_review(review_text: str) -> str:
    verdict = _extract_review_verdict(review_text) or "Review findings require Builder follow-up."
    critical = _extract_issue_titles(review_text, "CRITICAL")
    major = _extract_issue_titles(review_text, "MAJOR")
    minor = _extract_issue_titles(review_text, "Minor")
    blocker = detect_human_owned_blocker(review_text)

    summary_lines = [
        f"- Review verdict: {verdict}",
    ]
    if blocker is not None:
        summary_lines.append("- Human-owned blocker is present. Do not fabricate closure in build.md.")
    if critical:
        summary_lines.append(f"- Highest blocker: {critical[0]}")
    elif major:
        summary_lines.append(f"- Primary Builder follow-up: {major[0]}")

    requested_revisions: list[str] = []
    if blocker is not None:
        requested_revisions.append("Do not attempt to close the human-owned gate in Builder output. Stop and surface the blocker explicitly in build.md.")
    if major:
        requested_revisions.append("Address the remaining Builder-executable major gaps called out by review: " + "; ".join(major[:3]))
    elif minor:
        requested_revisions.append("Address the remaining minor contract/documentation gaps called out by review: " + "; ".join(minor[:3]))
    requested_revisions.append("Write the canonical build record to build.md. Do not leave the build result only in build_rerun_*.md.")

    findings_lines = {
        "Critical": critical or (["None"] if blocker is None else ["Human-owned blocker persists."]),
        "Major": major or ["None"],
        "Minor": minor or ["None"],
    }

    notes = [
        "- Keep `build.md` as a build record, not as a dump of deliverable contents.",
        "- Put implementation and durable artifacts in real files.",
        "- Record verification commands and outcomes explicitly.",
        "- Narrow the rebuild scope to the unresolved review gaps.",
    ]
    if blocker is not None:
        notes.append("- Human-owned blocker detected. Prefer surfacing the blocker over speculative Builder rewrites.")
        for action in blocker["actions"][:3]:
            notes.append(f"- Human follow-up: {action}")

    lines = [
        "# Build Review",
        "",
        "---",
        "",
        "## Purpose",
        "",
        "Feedback for revising `build.md` and the underlying build outputs before the Builder rebuilds them.",
        "This is a supporting note, not a canonical APSF phase artifact.",
        "",
        "---",
        "",
        "## Summary",
        "",
        *summary_lines,
        "",
        "---",
        "",
        "## Requested Revisions",
        "",
    ]

    for index, revision in enumerate(requested_revisions[:3], start=1):
        lines.append(f"{index}. {revision}")
    while len([line for line in lines if re.match(r"^\d+\.\s", line)]) < 3:
        index = len([line for line in lines if re.match(r"^\d+\.\s", line)]) + 1
        lines.append(f"{index}. ")

    lines.extend(
        [
            "",
            "---",
            "",
            "## Findings",
            "",
        ]
    )
    for heading in ("Critical", "Major", "Minor"):
        lines.append(f"### {heading}")
        lines.append("")
        for item in findings_lines[heading]:
            lines.append(f"- {item}")
        lines.append("")

    lines.extend(
        [
            "---",
            "",
            "## Notes To Builder",
            "",
            *notes,
            "",
        ]
    )
    return "\n".join(lines)
