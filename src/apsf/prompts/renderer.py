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


def render_plan_prompt(goal_content: str) -> str:
    """
    Planner 向けプロンプト。
    goal.md の内容を受け取り、plan.md 生成指示を組み立てる。
    """
    return (
        "Please create a plan.md based on the following Goal.\n\n"
        + _section("Goal", goal_content)
        + "---\n\n"
        "Output format: Follow the plan.md template.\n"
        "Include: Problem Structure, Hypotheses, Options (min 2), "
        "Selected Approach with reasoning, Execution Plan.\n"
    )


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
    if draft_content:
        prompt += _section("JuniorBuilder Draft (for reference)", draft_content)
    prompt += (
        "---\n\n"
        "Output: The actual deliverable + build.md.\n"
        "build.md must include: What was built, Inputs received, "
        "Decisions made, Deviations from Plan, Open Issues.\n"
    )
    return prompt


def render_review_prompt(
    goal_content: str,
    build_content: str,
    handoff_content: str = "",
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
    prompt += (
        "---\n\n"
        "Output format: Follow the review.md template.\n"
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
