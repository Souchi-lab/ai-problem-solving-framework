"""
Canonical advisory helpers for review -> improve auto-reroute.

The canonical judge advisory is durable structured state stored in
judge_advisory.json. It is written as part of the normal review completion
flow, not inferred later from free-form review prose.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

JUDGE_ADVISORY_FILE = "judge_advisory.json"
CANONICAL_JUDGE_ADVISORY_SOURCE = "judge_structured"
JUDGE_ADVISORY_RECOMMENDATIONS = frozenset({"Return to Build", "Return to Plan", "Accept"})
ADVISORY_SOURCE_CYCLE_START = "improve_cycle_started"
REVIEW_ADVISORY_BLOCK_PATTERN = re.compile(
    r"```apsf-judge-advisory\s+(?P<payload>\{.*?\})\s+```",
    flags=re.IGNORECASE | re.DOTALL,
)


def parse_review_judge_advisory(review_text: str) -> dict[str, Any]:
    """Extract the required structured advisory block from review.md content."""
    matches = list(REVIEW_ADVISORY_BLOCK_PATTERN.finditer(review_text))
    if len(matches) == 0:
        raise ValueError(
            "review.md must include exactly one ```apsf-judge-advisory``` JSON block "
            "with recommendation and human_owned_blocker."
        )
    if len(matches) != 1:
        raise ValueError(
            "review.md must include exactly one ```apsf-judge-advisory``` JSON block; "
            "multiple blocks are not allowed."
        )
    match = matches[0]
    try:
        payload = json.loads(match.group("payload"))
    except json.JSONDecodeError as exc:
        raise ValueError("review.md advisory block must contain valid JSON.") from exc
    if not isinstance(payload, dict):
        raise ValueError("review.md advisory block must decode to a JSON object.")

    recommendation = payload.get("recommendation")
    if not isinstance(recommendation, str) or not recommendation.strip():
        raise ValueError("review.md advisory block must include string recommendation.")
    recommendation = recommendation.strip()
    if recommendation not in JUDGE_ADVISORY_RECOMMENDATIONS:
        raise ValueError(
            "review.md advisory recommendation must be one of: "
            "Return to Build, Return to Plan, Accept."
        )

    if "human_owned_blocker" not in payload:
        raise ValueError("review.md advisory block must include boolean human_owned_blocker.")
    human_owned_blocker = payload.get("human_owned_blocker")
    if not isinstance(human_owned_blocker, bool):
        raise ValueError("review.md advisory human_owned_blocker must be true or false.")

    return {
        "recommendation": recommendation,
        "human_owned_blocker": human_owned_blocker,
    }


def canonical_judge_advisory_payload(
    run_dir: Path,
    *,
    recommendation: str | None,
    human_owned_blocker: bool | None,
    advisory_source: str,
    phase: str,
    generated_at: str | None = None,
    source: str | None = None,
    ownership_status: str | None = None,
    ownership_detail: str | None = None,
    run_id: str | None = None,
    freshness_token: str | None = None,
    human_owned_blocker_state: str | None = None,
) -> dict[str, Any]:
    return {
        "recommendation": recommendation,
        "human_owned_blocker": human_owned_blocker,
        "human_owned_blocker_state": human_owned_blocker_state,
        "advisory_source": advisory_source,
        "run_id": run_id or run_dir.name,
        "generated_at": generated_at or datetime.now(timezone.utc).isoformat(),
        "phase": phase,
        "ownership_status": ownership_status,
        "ownership_detail": ownership_detail,
        "source": source,
        "freshness_token": freshness_token,
    }


def write_canonical_judge_advisory(
    run_dir: Path,
    *,
    recommendation: str | None,
    human_owned_blocker: bool | None,
    phase: str,
    source: str,
    advisory_source: str = CANONICAL_JUDGE_ADVISORY_SOURCE,
    ownership_status: str | None = None,
    ownership_detail: str | None = None,
    freshness_token: str | None = None,
) -> dict[str, Any]:
    if recommendation is not None and recommendation not in JUDGE_ADVISORY_RECOMMENDATIONS:
        raise ValueError(f"unsupported judge advisory recommendation: {recommendation!r}")
    if advisory_source != CANONICAL_JUDGE_ADVISORY_SOURCE:
        raise ValueError(f"unsupported advisory_source for canonical judge advisory: {advisory_source!r}")
    if human_owned_blocker is not None and not isinstance(human_owned_blocker, bool):
        raise ValueError("human_owned_blocker must be a boolean or None.")

    payload = canonical_judge_advisory_payload(
        run_dir,
        recommendation=recommendation,
        human_owned_blocker=human_owned_blocker,
        human_owned_blocker_state="valid" if isinstance(human_owned_blocker, bool) else None,
        advisory_source=advisory_source,
        phase=phase,
        source=source,
        ownership_status=ownership_status,
        ownership_detail=ownership_detail,
        freshness_token=freshness_token,
    )
    (run_dir / JUDGE_ADVISORY_FILE).write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return payload


def write_improve_cycle_stub(run_dir: Path, phase_entered_at: str) -> None:
    """Legacy helper kept for compatibility in tests and manual recovery flows."""
    payload = canonical_judge_advisory_payload(
        run_dir,
        recommendation=None,
        human_owned_blocker=None,
        human_owned_blocker_state=None,
        advisory_source=ADVISORY_SOURCE_CYCLE_START,
        phase="IMPROVE_NEEDED",
        freshness_token=phase_entered_at,
        source=f"{JUDGE_ADVISORY_FILE}:cycle-start",
    )
    (run_dir / JUDGE_ADVISORY_FILE).write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
