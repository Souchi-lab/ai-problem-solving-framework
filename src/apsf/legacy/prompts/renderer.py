"""
renderer — 複数の入力ファイルを agent 向けプロンプト文字列に組み立てる

設計:
- 過剰なテンプレートエンジンは使わない（v0.1 はシンプルな文字列結合）
- 各 render_* 関数は 1 agent の 1 ステップに対応する
- TODO(v0.2): Jinja2 or 独自テンプレートエンジンへの移行を検討
"""

from __future__ import annotations


def _section(title: str, content: str) -> str:
    """セクションブロックを作成するヘルパー"""
    if not content.strip():
        return ""
    return f"## {title}\n\n{content.strip()}\n\n"


def render_setup_prompt(goal_content: str) -> str:
    """
    Planner 向けプロンプト（execution-assignment.md 生成用）。
    goal.md の内容を受け取り、execution-assignment.md 生成指示を組み立てる。
    """
    return (
        "You are a Planner. Create an execution-assignment.md based on the following Goal.\n\n"
        + _section("Goal", goal_content)
        + "---\n\n"
        "Output format: Return ONLY the raw Markdown content for execution-assignment.md.\n"
        "Start immediately with '# Execution Assignment'. Do not include meta-commentary,\n"
        "file paths, save locations, code fences, or explanatory text before or after the Markdown.\n"
        "Do not use any tools. Respond directly with the Markdown content.\n"
        "CRITICAL CONTRACT: You must strictly adhere to the APSF execution-assignment.md template structure.\n"
        "Do NOT rename, add, or remove section headers. Under '## Role Execution Assignments',\n"
        "the table MUST have exactly the columns: `| Role | Execution Type | Tool / Method | Workspace | Notes |`\n"
        "and MUST include rows for exactly these 4 base roles: `Planner`, `Builder`, `Critic`, `Judge`.\n"
        "Include: Run Name, Goal Summary, Scope Definition (In Scope / Out of Scope table),\n"
        "Phase Discussion Points (L-1, L-2, ... format, minimum 2 items),\n"
        "Deliverables table (Target / Output Type / Done Criteria),\n"
        "and Handoff Notes for Planner (recommended approach, caveats).\n"
    )


def render_plan_prompt(
    goal_content: str,
    specialist_content: str = "",
    specialist_selection_note: str = "",
    plan_review_content: str = "",
) -> str:
    """
    Planner 向けプロンプト。
    goal.md の内容を受け取り、plan.md 生成指示を組み立てる。
    """
    prompt = (
        "Produce the final contents of plan.md as markdown text only, based on the following Goal.\n\n"
        + _section("Goal", goal_content)
    )
    if specialist_selection_note:
        prompt += _section("Planner Specialist Selection", specialist_selection_note)
    if specialist_content:
        prompt += _section("Planner Specialist Guidance", specialist_content)
    if plan_review_content:
        prompt += _section("Plan Review Feedback", plan_review_content)
    prompt += (
        "---\n\n"
        "Output format: Return ONLY the raw Markdown content for plan.md.\n"
        "Start immediately with '# Plan'. Do not include meta-commentary, file paths, save locations,\n"
        "code fences, or explanatory text before or after the Markdown.\n"
        "If Plan Review Feedback is provided, reflect it in the revised plan.md while still returning the full final document.\n"
        "Required sections: Goal Readiness Check, Problem Structure, Hypotheses,\n"
        "Options (minimum 2), Selected Approach with reasoning,\n"
        "Implementation Readiness, Execution Plan, Assumptions & Open Questions.\n"
    )
    return prompt


def render_junior_build_prompt(plan_content: str, handoff_content: str = "") -> str:
    """
    JuniorBuilder 向けプロンプト。
    候補案を複数生成して Builder が選びやすい形にする。
    """
    prompt = (
        "Generate 2-3 candidate options based on the following Plan.\n"
        "Present each option with clear tradeoffs.\n\n"
        + _section("Plan", plan_content)
    )
    if handoff_content:
        prompt += _section("Handoff from Planner", handoff_content)
    prompt += (
        "---\n\n"
        "Output: List each candidate with tradeoffs. "
        "End with a memo for the Builder about key decisions needed.\n"
    )
    return prompt


def render_build_prompt(
    plan_content: str,
    handoff_content: str = "",
    draft_content: str = "",
    build_review_content: str = "",
) -> str:
    """
    Builder 向けプロンプト。
    plan.md + (handoff.md) + (build_draft.md from JuniorBuilder) を受け取る。
    """
    prompt = (
        "Create the final deliverable and build.md based on the following inputs.\n\n"
        + _section("Plan", plan_content)
    )
    if handoff_content:
        prompt += _section("Handoff", handoff_content)
    if build_review_content:
        prompt += _section("Build Review Feedback", build_review_content)
    if draft_content:
        prompt += _section("JuniorBuilder Draft (for reference)", draft_content)
    prompt += (
        "---\n\n"
        "Output format: Return ONLY the raw Markdown content for build.md.\n"
        "Start immediately with '# Build'. Do not include meta-commentary, code fences around the document, or explanatory text before or after the Markdown.\n"
        "If Build Review Feedback is provided, reflect it in the revised build while still returning the full final document.\n"
        "Do not dump the full deliverable into build.md. Put real implementation in real files and use build.md as the build record.\n"
        "build.md must include: What was built, Inputs received, "
        "Decisions made, Deviations from Plan, Open Issues.\n"
    )
    return prompt


def render_review_prompt(
    goal_content: str,
    build_content: str,
    handoff_content: str = "",
    specialist_content: str = "",
    specialist_selection_note: str = "",
    review_review_content: str = "",
) -> str:
    """
    Critic 向けプロンプト。
    goal.md + build.md を受け取り、Critical/Major/Minor 分類レビューを生成する。
    """
    prompt = (
        "Review the Build output against the Goal's success criteria.\n"
        "Classify issues as Critical / Major / Minor.\n\n"
        + _section("Goal", goal_content)
        + _section("Build Record", build_content)
    )
    if handoff_content:
        prompt += _section("Handoff from Builder", handoff_content)
    if review_review_content:
        prompt += _section("Re-review Feedback", review_review_content)
    if specialist_selection_note:
        prompt += _section("Critic Specialist Selection", specialist_selection_note)
    if specialist_content:
        prompt += _section("Critic Specialist Guidance", specialist_content)
    prompt += (
        "---\n\n"
        "Output format: Follow the review.md template.\n"
        "Return ONLY the raw Markdown content for review.md.\n"
        "Include exactly one ```apsf-judge-advisory``` JSON block in review.md.\n"
        "Zero blocks or multiple blocks are invalid.\n"
        'The block must contain {"recommendation": "Return to Build" | "Return to Plan" | "Accept", "human_owned_blocker": true|false}.\n'
        "This block is the canonical structured recommendation source for the current review completion flow.\n"
        "Do not infer it from free-form prose; state the recommendation directly in the block.\n"
        "Do not include meta-commentary, file paths, or explanatory text before or after the Markdown.\n"
        "If Re-review Feedback is provided, address its requested revisions while still producing a full independent review.\n"
        "Provide specific, actionable improvement suggestions for each issue.\n"
    )
    return prompt


def render_judge_prompt(goal_content: str, review_content: str) -> str:
    """
    Judge 向けプロンプト（AI がサマリを作成し、人間の判断を補助する）。
    """
    return (
        "Summarize whether the Goal's success criteria are met based on the Review.\n"
        "Assist the human Judge in making the final decision.\n\n"
        + _section("Goal", goal_content)
        + _section("Review", review_content)
        + "---\n\n"
        "Output: For each Success Criterion, state Met / Partially met / Not met.\n"
        "End with a recommendation: 'Continue (address X)' or 'Complete'.\n"
        "Note: The HUMAN makes the final call.\n"
    )
