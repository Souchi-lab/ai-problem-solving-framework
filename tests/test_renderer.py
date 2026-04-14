from apsf.legacy.prompts.renderer import render_plan_prompt, render_review_prompt


def test_render_plan_prompt_requires_raw_markdown_only() -> None:
    prompt = render_plan_prompt("Goal text")

    assert "Return ONLY the raw Markdown content for plan.md." in prompt
    assert "Start immediately with '# Plan'." in prompt
    assert "Do not include meta-commentary" in prompt
    assert "Execution Plan" in prompt


def test_render_review_prompt_includes_specialist_sections() -> None:
    prompt = render_review_prompt(
        "Goal text",
        "Build text",
        specialist_content="Critic guidance",
        specialist_selection_note="- Selected C-TYPE: C-01",
    )

    assert "Critic Specialist Selection" in prompt
    assert "Critic Specialist Guidance" in prompt
    assert "Return ONLY the raw Markdown content for review.md." in prompt
    assert "```apsf-judge-advisory```" in prompt
    assert "exactly one" in prompt
