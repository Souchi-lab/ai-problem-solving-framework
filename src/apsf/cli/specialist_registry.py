from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


_SPECIALIST_CODE_PATTERN = re.compile(r"\b([A-Z]-\d{2})\b", re.IGNORECASE)
_HEADING_PATTERN = re.compile(r"^##\s+(.+?)\s*$", re.MULTILINE)
_WORD_PATTERN = re.compile(r"[A-Za-z0-9_-]{3,}")
_STOPWORDS = {
    "and",
    "the",
    "for",
    "with",
    "that",
    "this",
    "from",
    "into",
    "when",
    "where",
    "what",
    "should",
    "would",
    "while",
    "only",
    "just",
    "than",
    "then",
    "them",
    "they",
    "their",
    "there",
    "here",
    "have",
    "has",
    "had",
    "are",
    "was",
    "were",
    "not",
    "without",
    "because",
    "rather",
    "being",
    "does",
    "doesnt",
    "dont",
    "over",
    "under",
    "between",
    "before",
    "after",
    "about",
    "mainly",
    "main",
    "task",
    "work",
    "plan",
    "planner",
    "review",
    "critic",
    "specialist",
}

PTYPE_TO_SPECIALIST: dict[str, str] = {
    "P-01": "framework/agents/planners/feature-planner.md",
    "P-02": "framework/agents/planners/bugfix-planner.md",
    "P-03": "framework/agents/planners/refactor-planner.md",
    "P-04": "framework/agents/planners/migration-planner.md",
    "P-05": "framework/agents/planners/docs-planner.md",
    "P-06": "framework/agents/planners/design-planner.md",
    "P-07": "framework/agents/planners/retro-planner.md",
    "P-08": "framework/agents/planners/research-planner.md",
    "P-09": "framework/agents/planners/integration-planner.md",
    "P-10": "framework/agents/planners/performance-planner.md",
    "P-11": "framework/agents/planners/test-strategy-planner.md",
    "P-12": "framework/agents/planners/dependency-upgrade-planner.md",
}

CTYPE_TO_SPECIALIST: dict[str, str] = {
    "C-01": "framework/agents/critics/ux-flow-critic.md",
    "C-02": "framework/agents/critics/copy-clarity-critic.md",
    "C-03": "framework/agents/critics/landing-page-critic.md",
    "C-04": "framework/agents/critics/empty-state-and-error-ux.md",
    "C-05": "framework/agents/critics/bilingual-ui.md",
    "C-06": "framework/agents/critics/information-architecture.md",
    "C-07": "framework/agents/critics/product-positioning-critic.md",
    "C-08": "framework/agents/critics/puzzle-difficulty-critic.md",
}


@dataclass(frozen=True)
class SpecialistSelection:
    ptype: str
    specialist_path: Path | None
    specialist_content: str
    mode: str  # explicit | inferred | unresolved
    reason: str
    score: int = 0


def normalize_specialist_code(raw: str) -> str:
    match = _SPECIALIST_CODE_PATTERN.search(raw or "")
    if not match:
        return ""
    return match.group(1).upper()


def normalize_ptype(raw: str) -> str:
    code = normalize_specialist_code(raw)
    return code if code.startswith("P-") else ""


def normalize_ctype(raw: str) -> str:
    code = normalize_specialist_code(raw)
    return code if code.startswith("C-") else ""


def extract_primary_specialist_code(text: str, prefix: str) -> str:
    marker = f"{prefix}-TYPE"
    for line in (text or "").splitlines():
        if marker not in line.upper():
            continue
        normalized = normalize_specialist_code(line)
        if normalized.startswith(f"{prefix}-"):
            return normalized
    return ""


def has_explicit_generic_specialist(text: str, prefix: str) -> bool:
    marker = f"{prefix}-TYPE"
    for line in (text or "").splitlines():
        upper = line.upper()
        if marker not in upper:
            continue
        if "NONE" in upper or "GENERIC" in upper:
            return True
    return False


def extract_primary_ptype(text: str) -> str:
    return extract_primary_specialist_code(text, "P")


def extract_primary_ctype(text: str) -> str:
    return extract_primary_specialist_code(text, "C")


def specialist_path_for_code(
    code: str,
    framework_root: Path,
    mapping: dict[str, str],
) -> Path | None:
    normalized = normalize_specialist_code(code)
    rel_path = mapping.get(normalized)
    if not rel_path:
        return None
    return framework_root / rel_path


def specialist_path_for_ptype(ptype: str, framework_root: Path) -> Path | None:
    return specialist_path_for_code(ptype, framework_root, PTYPE_TO_SPECIALIST)


def specialist_path_for_ctype(ctype: str, framework_root: Path) -> Path | None:
    return specialist_path_for_code(ctype, framework_root, CTYPE_TO_SPECIALIST)


def load_specialist_content(
    code: str,
    framework_root: Path,
    mapping: dict[str, str] | None = None,
) -> str:
    if mapping is None:
        normalized = normalize_specialist_code(code)
        mapping = PTYPE_TO_SPECIALIST if normalized.startswith("P-") else CTYPE_TO_SPECIALIST
    path = specialist_path_for_code(code, framework_root, mapping)
    if path is None or not path.exists():
        return ""
    return path.read_text(encoding="utf-8").strip()


def extract_section(markdown: str, section_name: str) -> str:
    text = markdown or ""
    matches = list(_HEADING_PATTERN.finditer(text))
    if not matches:
        return ""

    target = section_name.strip().lower()
    for index, match in enumerate(matches):
        heading = match.group(1).strip().lower()
        if heading != target:
            continue
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        return text[start:end].strip()
    return ""


def _extract_first_matching_section(markdown: str, names: list[str]) -> str:
    for name in names:
        content = extract_section(markdown, name)
        if content:
            return content
    return ""


def selection_sections(markdown: str) -> dict[str, str]:
    return {
        "scope": extract_section(markdown, "Scope"),
        "out_of_scope": extract_section(markdown, "Out of Scope"),
        "evaluation_criteria": extract_section(markdown, "Evaluation Criteria"),
        "use_this_specialist_when": _extract_first_matching_section(
            markdown,
            ["Use This Specialist When", "Use This Planner When", "Use This Critic When"],
        ),
        "do_not_use_this_specialist_when": _extract_first_matching_section(
            markdown,
            ["Do Not Use This Specialist When", "Do Not Use This Planner When", "Do Not Use This Critic When"],
        ),
        "nearby_specialist_distinctions": _extract_first_matching_section(
            markdown,
            ["Nearby Specialist Distinctions", "Nearby Planner Distinctions", "Nearby Critic Distinctions"],
        ),
    }


def _keywords(text: str) -> set[str]:
    return {
        word
        for match in _WORD_PATTERN.finditer(text or "")
        if (word := match.group(0).lower()) not in _STOPWORDS
    }


def _score_goal_against_sections(goal_text: str, sections: dict[str, str]) -> tuple[int, list[str]]:
    goal_words = _keywords(goal_text)
    if not goal_words:
        return 0, []

    scope_words = _keywords(sections.get("scope", ""))
    eval_words = _keywords(sections.get("evaluation_criteria", ""))
    out_words = _keywords(sections.get("out_of_scope", ""))
    use_words = _keywords(sections.get("use_this_specialist_when", ""))
    avoid_words = _keywords(sections.get("do_not_use_this_specialist_when", ""))
    nearby_words = _keywords(sections.get("nearby_specialist_distinctions", ""))

    scope_hits = sorted(goal_words & scope_words)
    eval_hits = sorted(goal_words & eval_words)
    out_hits = sorted(goal_words & out_words)
    use_hits = sorted(goal_words & use_words)
    avoid_hits = sorted(goal_words & avoid_words)
    nearby_hits = sorted(goal_words & nearby_words)

    score = (
        (len(scope_hits) * 3)
        + (len(eval_hits) * 2)
        + (len(use_hits) * 3)
        + len(nearby_hits)
        - (len(out_hits) * 3)
        - (len(avoid_hits) * 3)
    )
    reasons: list[str] = []
    if scope_hits:
        reasons.append(f"scope hits: {', '.join(scope_hits[:4])}")
    if eval_hits:
        reasons.append(f"evaluation hits: {', '.join(eval_hits[:4])}")
    if use_hits:
        reasons.append(f"use hits: {', '.join(use_hits[:4])}")
    if nearby_hits:
        reasons.append(f"nearby hits: {', '.join(nearby_hits[:4])}")
    if out_hits:
        reasons.append(f"out-of-scope hits: {', '.join(out_hits[:4])}")
    if avoid_hits:
        reasons.append(f"avoid hits: {', '.join(avoid_hits[:4])}")
    return score, reasons


def _resolve_specialist(
    goal_text: str,
    assignment_text: str,
    framework_root: Path,
    prefix: str,
    mapping: dict[str, str],
    explicit_label: str,
) -> SpecialistSelection:
    explicit_code = extract_primary_specialist_code(assignment_text, prefix)
    if explicit_code:
        path = specialist_path_for_code(explicit_code, framework_root, mapping)
        content = load_specialist_content(explicit_code, framework_root, mapping)
        sections = selection_sections(content)
        score, reasons = _score_goal_against_sections(goal_text, sections)
        reason = explicit_label
        if reasons:
            reason += f"; {'; '.join(reasons)}"
        return SpecialistSelection(
            ptype=explicit_code,
            specialist_path=path,
            specialist_content=content,
            mode="explicit",
            reason=reason,
            score=score,
        )

    if has_explicit_generic_specialist(assignment_text, prefix):
        return SpecialistSelection(
            ptype="",
            specialist_path=None,
            specialist_content="",
            mode="explicit",
            reason=f"{explicit_label}: none (use generic Critic/Planner)",
            score=0,
        )

    best: SpecialistSelection | None = None
    for code in sorted(mapping):
        path = specialist_path_for_code(code, framework_root, mapping)
        content = load_specialist_content(code, framework_root, mapping)
        if not content:
            continue
        sections = selection_sections(content)
        score, reasons = _score_goal_against_sections(goal_text, sections)
        reason = "inferred from specialist markdown"
        if reasons:
            reason += f"; {'; '.join(reasons)}"
        candidate = SpecialistSelection(
            ptype=code,
            specialist_path=path,
            specialist_content=content,
            mode="inferred",
            reason=reason,
            score=score,
        )
        if best is None or candidate.score > best.score:
            best = candidate

    if best is not None and best.score > 0:
        return best

    return SpecialistSelection(
        ptype="",
        specialist_path=None,
        specialist_content="",
        mode="unresolved",
        reason=f"no explicit {prefix}-TYPE and no specialist markdown produced a positive match",
        score=0,
    )


def resolve_planner_specialist(
    goal_text: str,
    assignment_text: str,
    framework_root: Path,
) -> SpecialistSelection:
    return _resolve_specialist(
        goal_text=goal_text,
        assignment_text=assignment_text,
        framework_root=framework_root,
        prefix="P",
        mapping=PTYPE_TO_SPECIALIST,
        explicit_label="explicit Primary P-TYPE",
    )


def resolve_critic_specialist(
    goal_text: str,
    assignment_text: str,
    framework_root: Path,
) -> SpecialistSelection:
    return _resolve_specialist(
        goal_text=goal_text,
        assignment_text=assignment_text,
        framework_root=framework_root,
        prefix="C",
        mapping=CTYPE_TO_SPECIALIST,
        explicit_label="explicit Primary C-TYPE",
    )
