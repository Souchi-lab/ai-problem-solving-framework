"""
CLI - APSF コマンドラインインターフェース（v0.1: CLI/Human 前提）

コマンド:
    apsf init-run <run-name>          runs/_template から run を作成
    apsf start-run <run-name>         init-run の別名（日付を自動補完）
    apsf next <run-name> [--debug]    現在のフェーズを検出して次ロール向け指示を表示
    apsf transcript <run-name>        run から transcript.md を自動生成
    apsf show-structure               framework 構造を表示
    apsf dry-run <run-name>           pipeline の role/executor マッピングを表示
    apsf check-env                    環境変数の設定状況を確認（API は optional）
    apsf show-execution-plan <run>    execution-assignment.md の内容を表示
    apsf init-followup <slug>         followups/ に4ファイルのスケルトンを生成

使用例:
    apsf start-run sochi-blocks_sns-post-template   # 日付が自動付与される
    apsf init-run 2026-03-15_sochi-blocks_sns-post-template
    apsf next 2026-03-15_sochi-blocks_sns-post-template
    apsf next 2026-03-15_sochi-blocks_sns-post-template --debug
    apsf transcript 2026-03-15_sochi-blocks_sns-post-template
    apsf dry-run 2026-03-15_sochi-blocks_sns-post-template
    apsf show-execution-plan 2026-03-15_sochi-blocks_sns-post-template
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path
from typing import Optional

import typer


def _ensure_utf8_output() -> None:
    """Windows ターミナルで日本語が文字化けしないよう stdout/stderr を UTF-8 に再設定する。

    Python のデフォルトでは Windows の stdout は cp932 で開かれるため、
    日本語を含む CLI メッセージがターミナルで化ける。
    sys.stdout.reconfigure() で UTF-8 に切り替えることで解決する。

    CliRunner (テスト) は自前の StringIO を使うため影響しない。
    """
    if sys.platform == "win32":
        for stream in (sys.stdout, sys.stderr):
            if hasattr(stream, "reconfigure"):
                try:
                    stream.reconfigure(encoding="utf-8", errors="replace")
                except (AttributeError, TypeError):
                    pass


_ensure_utf8_output()


_TRANSPORT_LINE_RE = re.compile(
    r"^\s*(?:"
    r"\[APSF\]|\[Step \d+/\d+\]|\[Done\]|\[Note\]|\[FAIL\]|\[Error\]|\[Warn\]|"
    r"Do you want to allow|Allow this action|Permission required|Approval required"
    r")",
    re.IGNORECASE,
)


def _sanitize_phase_input(text: str) -> str:
    """
    LLM/CLI 出力に混ざる transport text を phase file 保存前に軽く正規化する。

    目的:
    - `claude -p` 由来の permission / status テキストが phase file に混入しないようにする
    - 先頭に混ざった wrapper/log 行を落として、実際の Markdown 本文から保存する

    方針:
    - 先頭側のみを対象にする
    - 最初の Markdown heading (`# ...`) が見つかったら、それ以前は落とす
    - それまでの行に transport 系ログがあれば落とす
    """
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = normalized.split("\n")

    first_heading_index: int | None = None
    for idx, line in enumerate(lines):
        if re.match(r"^\s*#\s+\S", line):
            first_heading_index = idx
            break

    if first_heading_index is not None and any(line.strip() for line in lines[:first_heading_index]):
        lines = lines[first_heading_index:]

    while lines:
        s = lines[0].strip()
        if not s:
            lines.pop(0)
            continue
        if _TRANSPORT_LINE_RE.match(s):
            lines.pop(0)
            continue
        break

    return "\n".join(lines).strip() + ("\n" if lines else "")


def _get_claude_timeout_sec() -> int:
    raw = os.environ.get("APSF_CLAUDE_TIMEOUT_SEC", "300")
    try:
        value = int(raw)
    except ValueError:
        return 300
    return max(30, value)

app = typer.Typer(
    name="apsf",
    help="AI Problem Solving Framework - CLI/Human-first, multi-model problem solving OS",
    add_completion=False,
)


@app.command("init-run")
def init_run(
    run_name: str = typer.Argument(
        ..., help="Run name: YYYY-MM-DD_case-key_topic or YYYY-MM-DD-NNN_case-key_topic"
    ),
    force: bool = typer.Option(False, "--force", "-f", help="Overwrite if exists"),
    taxonomy: str | None = typer.Option(
        None,
        "--taxonomy",
        help="Target taxonomy root: fw-improvement or work",
    ),
) -> None:
    """指定した名前で runs/ に新しい run ディレクトリを作成する。"""
    from ..config.settings import get_settings
    from ..legacy.storage.run_repository import RunRepository

    settings = get_settings()
    repo = RunRepository(runs_dir=settings.runs_dir, template_dir=settings.template_dir)

    if not repo.validate_run_name(run_name):
        typer.echo(
            f"[ERROR] Invalid run name: '{run_name}'\n"
            "   Expected: YYYY-MM-DD_case-key_topic or YYYY-MM-DD-NNN_case-key_topic\n"
            "   Example:  2026-03-15-001_sochi-blocks_sns-post-template",
            err=True,
        )
        raise typer.Exit(1)

    try:
        run_dir = repo.init_run(run_name, force=force, taxonomy=taxonomy)
        typer.echo(f"[OK] Run created: {run_dir}")
        typer.echo("\nNext steps:")
        typer.echo(f"  1. Edit {run_dir}/execution-assignment.md  <- how to execute each role")
        typer.echo(f"  2. Edit {run_dir}/goal.md                  <- what to solve")
        typer.echo("  3. If needed, create model-assignment.md from framework/templates/model-assignment.md")
        typer.echo("     Use it when model choice is mandatory/recommended for the run.")
        typer.echo(f"  4. Run: apsf show-execution-plan {run_name}")
    except (FileExistsError, FileNotFoundError) as e:
        typer.echo(f"[ERROR] {e}", err=True)
        raise typer.Exit(1)


# ── init-followup テンプレート定数 ──────────────────────────────────────────

_FOLLOWUP_GOAL_TEMPLATE = """\
# Goal

---

## Follow-up Context

- Parent series: <!-- どの実験系列か -->
- Previous result: <!-- 直前 result の一言まとめ -->
- New trigger: <!-- なぜこれをやるか -->
- Scope limit: <!-- 変更対象の上限 -->
- Non-goals: <!-- 今回やらないこと -->

---

## Goal Statement

<!-- 今回の主語を1文で固定する。何を確かめるか。二層目的がある場合は明示する。 -->

---

## Background

<!-- なぜこれをやるか。前回 result / 外部トリガーを記録する。 -->

---

## Success Criteria

1.
2.
3.

---

## Expected Outputs

-

---

## Non-Goals

-

---

## Constraints

- <!-- 対象を広げない条件 -->
- <!-- 必要な確認だけに絞る条件 -->
- <!-- 次 trigger に自然につながる条件 -->

---

## Notes For Planner

<!-- Planner が明確化すべきこと / トレードオフ / 優先順位判断 -->
"""

_FOLLOWUP_PLAN_TEMPLATE = """\
# Plan

---

## Follow-up Context

- Parent series:
- Previous result:
- New trigger:
- Scope limit:
- Non-goals:

---

## Run Metadata

- Follow-up:
- Goal:
- Output focus:
- Non-goal reminder:

---

## Goal Readiness Check

-
-

Decision: Proceed / Block

---

## Execution Intent

### 表層:

### 裏層:

---

## Problem Structure

<!-- 問題の構造分解 -->

---

## Selected Approach

Approach:

Reasoning:

---

## Scope Policy

この follow-up に含めるもの:

-

この follow-up に含めないもの:

-

---

## Deliverables

-

---

## Review Checklist

-

---

## Planned Output Shape

<!-- result の構成を先に定義する -->

---

## Assumptions & Open Questions

Assumptions:

-

Open questions:

-

---

## What This Follow-up Decides

-

---

## What This Follow-up Does Not Decide

-
"""

_FOLLOWUP_REVIEW_TEMPLATE = """\
# Review

---

## Follow-up Context

- Follow-up:
- Plan decision:

---

## Gate Questions

1. <!-- 二層目的は崩れていないか -->

2. <!-- scope が広がっていないか -->

3. <!-- result で判断できる状態になっているか -->

---

## Decision

Proceed / Block / Revise

---

## Notes

<!-- review での気づき・修正点 -->
"""

_FOLLOWUP_RESULT_TEMPLATE = """\
# Result

---

## Status

<!-- Completed / Partial / Blocked -->

---

## 1. 実装差分サマリー

<!-- 変更ファイル・変更量 -->

---

## 2. 評価

<!-- goal の Success Criteria に対して -->

---

## 3. 採用判断

<!-- 採用 / 非採用 / 条件付き採用 -->

---

## 4. 形式評価

<!-- 4点セットの今回タスクへの適合度 -->

---

## 5. Closing

### Stable Baseline

<!-- この follow-up で確定したこと -->

### Open Conditional

<!-- 条件次第で変わりうること -->

### Next Trigger

<!-- 次の follow-up を起動するとしたら何か -->
"""

_FOLLOWUP_FILES: dict[str, str] = {
    "goal.md":   _FOLLOWUP_GOAL_TEMPLATE,
    "plan.md":   _FOLLOWUP_PLAN_TEMPLATE,
    "review.md": _FOLLOWUP_REVIEW_TEMPLATE,
    "result.md": _FOLLOWUP_RESULT_TEMPLATE,
}

_FOLLOWUPS_DIR = Path("framework") / "experimental" / "redesign" / "followups"


@app.command("init-followup")
def init_followup(
    slug: str = typer.Argument(..., help="Follow-up name (e.g. twitter-tag-improvement)"),
    force: bool = typer.Option(False, "--force", "-f", help="Overwrite existing files"),
) -> None:
    """framework/experimental/redesign/followups/<slug>/ に4ファイルのスケルトンを生成する。"""
    from ..config.settings import get_settings

    settings = get_settings()
    followup_dir = settings.framework_root / _FOLLOWUPS_DIR / slug

    if followup_dir.exists() and not force:
        typer.echo(
            f"[ERROR] Already exists: {followup_dir}\n"
            "  Use --force to overwrite.",
            err=True,
        )
        raise typer.Exit(1)

    followup_dir.mkdir(parents=True, exist_ok=True)

    created: list[str] = []
    skipped: list[str] = []

    for filename, content in _FOLLOWUP_FILES.items():
        filepath = followup_dir / filename
        if filepath.exists() and not force:
            skipped.append(filename)
            continue
        filepath.write_text(content, encoding="utf-8")
        created.append(filename)

    typer.echo(f"[OK] Follow-up initialized: {followup_dir}")
    if created:
        typer.echo(f"  Created: {', '.join(created)}")
    if skipped:
        typer.echo(f"  Skipped (already exists): {', '.join(skipped)}")
    typer.echo("\nNext steps:")
    typer.echo("  0. Run: apsf list-followups        <- check existing series & previous results")
    typer.echo(f"  1. Edit {followup_dir}/goal.md   <- what to confirm")
    typer.echo(f"  2. Edit {followup_dir}/plan.md   <- how to approach it")
    typer.echo(f"  3. Build, then fill {followup_dir}/result.md")


@app.command("list-followups")
def list_followups() -> None:
    """framework/experimental/redesign/followups/ 配下の follow-up 一覧を表示する。"""
    from ..config.settings import get_settings

    settings = get_settings()
    followups_dir = settings.framework_root / _FOLLOWUPS_DIR

    if not followups_dir.exists():
        typer.echo(f"[ERROR] Follow-ups directory not found: {followups_dir}", err=True)
        raise typer.Exit(1)

    followup_dirs = sorted(
        [path for path in followups_dir.iterdir() if path.is_dir()],
        key=lambda path: path.name.lower(),
    )

    if not followup_dirs:
        typer.echo(f"[INFO] No follow-ups found in: {followups_dir}")
        return

    expected_files = ("goal.md", "plan.md", "review.md", "result.md")

    def _followup_status(d: Path) -> str:
        has_result = (d / "result.md").exists()
        has_review = (d / "review.md").exists()
        if has_result and has_review:
            return "complete"
        if has_result:
            return "complete (review-skipped)"
        return "in-progress"

    typer.echo(f"Follow-ups: {followups_dir}")
    typer.echo("=" * 72)

    for followup_dir in followup_dirs:
        present = [name for name in expected_files if (followup_dir / name).exists()]
        missing = [name for name in expected_files if name not in present]
        status = _followup_status(followup_dir)

        typer.echo(f"- {followup_dir.name}  [{status}]")
        typer.echo(f"  Files: {', '.join(present) if present else '(none)'}")
        if missing and status == "in-progress":
            typer.echo(f"  Missing: {', '.join(missing)}")


@app.command("show-structure")
def show_structure() -> None:
    """framework / cases / runs / workspaces / src の役割を表示する。"""
    typer.echo("""
AI Problem Solving Framework (APSF) - Directory Structure
==========================================================

framework/              Design assets (domain-independent)
  overview.md           Full framework overview
  operating-model.md    Multi-model operating model
  execution-model.md    CLI/Human execution model  <- v0.1 focus
  workflow/v0.1.md      Step-by-step workflow
  agents/               Role definitions & prompt drafts
  templates/            Original templates (do not write directly)

cases/                  Domain-specific knowledge
  sochi-blocks/         First validation case

runs/                   Execution logs (1 folder = 1 problem solving cycle)
  _template/            Copy this to start a new run
  YYYY-MM-DD_*/         Each run (completed or in-progress)

workspaces/             Working space per role (temporary, not permanent storage)
  planner/              Planner's working directory
  junior_builder/       JuniorBuilder's working directory
  builder/              Builder's working directory  <- high-value, use best tool here
  critic/               Critic's working directory   <- use different tool from Builder
  judge/                Judge's working directory    <- human in v0.1

src/apsf/               Python execution infrastructure
  executors/            How to execute: CLI / Human / future-API
  agents/               What to do: role implementations
  orchestration/        Pipeline / AssignmentService / ExecutionAssignmentService
  storage/              Markdown R/W & run directory management
  cli/                  This CLI

Key principle: role ≠ executor
  BuilderAgent uses CLIExecutor("claude")      [OK]
  ClaudeBuilder                                 [ERROR] (never do this)
  CriticAgent uses HumanExecutor()             [OK] (different from Builder)
""")


@app.command("dry-run")
def dry_run_cmd(
    run_name: str = typer.Argument(..., help="Run name to inspect"),
) -> None:
    """
    指定 run の execution-assignment.md を読み込み、
    pipeline の role/executor マッピングを表示する。実行はしない。
    """
    from ..config.settings import get_settings
    from ..orchestration.execution_assignment_service import ExecutionAssignmentService
    from ..core.domain.models import Role, ExecutionType
    from ..legacy.storage.run_repository import RunRepository

    settings = get_settings()
    repo = RunRepository(runs_dir=settings.runs_dir, template_dir=settings.template_dir)
    run_dir = repo.get_run_dir(run_name)
    assignment_path = run_dir / "execution-assignment.md"

    if not run_dir.exists():
        typer.echo(f"[ERROR] Run not found: {run_dir}", err=True)
        raise typer.Exit(1)

    has_assignment = assignment_path.exists()
    service = ExecutionAssignmentService(settings=settings)
    context = service.load_from_file(assignment_path, run_dir)

    typer.echo(f"\nDry Run: {run_name}")
    typer.echo("=" * 72)
    typer.echo(
        f"  {'Step':<10} {'Role':<16} {'Type':<10} {'Tool':<18} Workspace"
    )
    typer.echo("  " + "─" * 68)

    steps = [
        ("goal",          Role.HUMAN,          "Human defines Goal (manual)"),
        ("plan",          Role.PLANNER,        "Planner breaks down problem"),
        ("junior_build",  Role.JUNIOR_BUILDER, "JuniorBuilder creates draft candidates"),
        ("build",         Role.BUILDER,        "Builder refines into final artifact"),
        ("review",        Role.CRITIC,         "Critic reviews output"),
        ("improve",       Role.JUDGE,          "Judge decides next action"),
        ("result",        Role.HUMAN,          "Human writes result.md (manual)"),
    ]

    notes = []
    for step_name, role, description in steps:
        # HUMAN role (goal/result) は常に human 固定
        if role == Role.HUMAN:
            exec_type = "human"
            tool = "-"
            workspace = "-"
        else:
            assignment = context.get_execution_assignment(role)
            if assignment:
                exec_type = assignment.execution_type.value
                tool = assignment.tool or "-"
                workspace = assignment.workspace or "-"
                # 注釈収集
                if role == Role.BUILDER and assignment.execution_type == ExecutionType.CLI:
                    notes.append(f"  {'build':<10} ★ high-value step - use your best tool here")
                if role == Role.CRITIC and assignment.execution_type == ExecutionType.CLI:
                    notes.append(f"  {'review':<10} use a different tool from Builder")
            else:
                exec_type = "human"
                tool = "-"
                workspace = "-"
                notes.append(f"  {step_name:<10} [WARN]  no assignment found -> defaulting to human")

        # 行出力
        type_str = f"[{exec_type}]"
        typer.echo(
            f"  {step_name:<10} {role.value:<16} {type_str:<10} {tool:<18} {workspace}"
        )

    typer.echo("")

    if notes:
        typer.echo("Notes:")
        for note in notes:
            typer.echo(note)
        typer.echo("")

    if not has_assignment:
        typer.echo("[WARN]  execution-assignment.md not found - showing defaults.")
        typer.echo(f"   Create it at: {assignment_path}")
        typer.echo(f"   Template:     framework/templates/execution-assignment.md")
    else:
        typer.echo(f"Source: {assignment_path}")


@app.command("show-execution-plan")
def show_execution_plan(
    run_name: str = typer.Argument(..., help="Run name"),
) -> None:
    """
    execution-assignment.md を読み込んで実行計画を表示する。

    各 role の実行手順・ツール・workspace を確認できる。
    """
    from ..config.settings import get_settings
    from ..orchestration.execution_assignment_service import ExecutionAssignmentService
    from ..legacy.storage.run_repository import RunRepository

    settings = get_settings()
    repo = RunRepository(runs_dir=settings.runs_dir, template_dir=settings.template_dir)
    run_dir = repo.get_run_dir(run_name)
    assignment_path = run_dir / "execution-assignment.md"

    if not run_dir.exists():
        typer.echo(f"[ERROR] Run not found: {run_dir}", err=True)
        raise typer.Exit(1)

    if not assignment_path.exists():
        typer.echo(f"[WARN]  execution-assignment.md not found: {assignment_path}")
        typer.echo("   Create it from the template:")
        typer.echo(f"   framework/templates/execution-assignment.md")
        raise typer.Exit(1)

    service = ExecutionAssignmentService(settings=settings)
    context = service.load_from_file(assignment_path, run_dir)
    summary = service.summarize(context)

    typer.echo(f"\nExecution Plan: {run_name}")
    typer.echo("=" * 60)
    for item in summary:
        typer.echo(
            f"  {item['role']:<18} [{item['execution_type']:<12}]"
            f"  tool={item['tool'] or '-':<15}  workspace={item['workspace'] or '-'}"
        )

    typer.echo(f"\nFull plan: {assignment_path}")


@app.command("generate-transcript")
def generate_transcript(
    run_name: str = typer.Argument(..., help="Run name"),
) -> None:
    """
    transcript.md 生成ガイドを表示する。

    指定 run の各ファイルの存在を確認し、
    transcript.md の各セクションに何を書くかを表示する。
    実際の生成は人間（または AI）が行う。
    """
    from ..config.settings import get_settings
    from ..legacy.storage.run_repository import RunRepository

    settings = get_settings()
    repo = RunRepository(runs_dir=settings.runs_dir, template_dir=settings.template_dir)
    run_dir = repo.get_run_dir(run_name)

    if not run_dir.exists():
        typer.echo(f"[ERROR] Run not found: {run_dir}", err=True)
        raise typer.Exit(1)

    # 参照ファイルの存在チェック
    source_files = [
        ("execution-assignment.md", "how to run"),
        ("goal.md",                 "what to solve"),
        ("plan_review.md",          "optional re-plan feedback"),
        ("build_review.md",         "optional re-build feedback"),
        ("review_review.md",        "optional re-review feedback"),
        ("improve_review.md",       "optional re-improve feedback"),
        ("plan.md",                 "how to approach"),
        ("handoff.md",              "optional transfer context between roles"),
        ("build.md",                "what was made"),
        ("review.md",               "what was found"),
        ("improve.md",              "what was decided"),
        ("result.md",               "what was learned"),
    ]

    transcript_path = run_dir / "transcript.md"
    template_path   = settings.template_dir / "transcript.md"

    typer.echo(f"\nGenerate Transcript: {run_name}")
    typer.echo("=" * 72)
    typer.echo("")
    typer.echo("Step 1: Check source files")
    typer.echo("  " + "-" * 60)

    missing = []
    for filename, description in source_files:
        path = run_dir / filename
        is_optional = filename in {"plan_review.md", "build_review.md", "review_review.md", "improve_review.md", "handoff.md"}
        status = "[OK]     " if path.exists() else ("[OPTIONAL]" if is_optional else "[MISSING]")
        if not path.exists() and not is_optional:
            missing.append(filename)
        typer.echo(f"  {status} {filename:<30} -- {description}")

    typer.echo("")
    if missing:
        typer.echo(f"[WARN] {len(missing)} file(s) missing. Complete them before generating transcript.")
        for f in missing:
            typer.echo(f"         - {f}")
        typer.echo("")

    # transcript.md の状態
    typer.echo("Step 2: transcript.md status")
    typer.echo("  " + "-" * 60)
    if transcript_path.exists():
        typer.echo(f"  [EXISTS]  {transcript_path}")
        typer.echo("            Edit it to complete the transcript.")
    else:
        typer.echo(f"  [NEW]     {transcript_path}")
        if template_path.exists():
            typer.echo(f"  Template: {template_path}")
            typer.echo(f"  Copy it:  cp \"{template_path}\" \"{transcript_path}\"")
        else:
            typer.echo("  Template: runs/_template/transcript.md")

    # セクション別記入ガイド
    typer.echo("")
    typer.echo("Step 3: Section writing guide")
    typer.echo("  " + "-" * 60)

    sections = [
        ("Run Overview",          "execution-assignment.md",             "Execution table: role / tool / type"),
        ("Goal",                  "goal.md",                             "Goal Statement, Background, Success Criteria, Notes"),
        ("Planning",              "plan.md + optional handoff.md (+ plan_review.md if present)", "Problem Structure, Selected Approach, re-plan feedback, handoff summary when used"),
        ("Build Feedback",        "build_review.md (optional)",          "Re-build requests, unresolved build gaps"),
        ("Review Feedback",       "review_review.md (optional)",         "Re-review requests and reviewer corrections"),
        ("Judge Feedback",        "improve_review.md (optional)",        "Re-improve requests and judgment clarifications"),
        ("Draft Generation",      "workspaces/junior_builder/",          "Number of drafts, categories, key decisions"),
        ("Build",                 "build.md + optional handoff.md",      "What was built, decisions made, deviations"),
        ("Review",                "review.md + optional handoff.md",     "Critical/Major/Minor count, overall assessment"),
        ("Judge Decision",        "improve.md",                          "Decision (adopt/revise/reject), reason, next scope"),
        ("Result",                "result.md",                           "Outcome, success criteria table, overall verdict"),
        ("Generalization Notes",  "result.md (Generalization section)",  "Key patterns, reusable insights"),
        ("Framework Notes",       "result.md (Framework Feedback)",      "Framework improvements noted"),
    ]

    for section, source, guidance in sections:
        typer.echo(f"  [{section}]")
        typer.echo(f"    Source  : {source}")
        typer.echo(f"    Write   : {guidance}")
        typer.echo("")

    typer.echo("Step 4: Writing style")
    typer.echo("  " + "-" * 60)
    typer.echo("  Use conversation blocks per role:")
    typer.echo("")
    typer.echo('  **Planner**: [summary of plan.md in 2-3 sentences]')
    typer.echo('  **Builder**: [summary of build.md in 2-3 sentences]')
    typer.echo('  **Critic**:  [summary of review.md in 2-3 sentences]')
    typer.echo('  **Judge**:   [decision from improve.md + reason]')
    typer.echo("")
    typer.echo("  Rules:")
    typer.echo("  - Facts only. Do not add information not in source files.")
    typer.echo("  - Keep each block to 3-5 lines.")
    typer.echo("  - transcript.md is a secondary artifact, not the official record.")
    typer.echo("")
    typer.echo(f"Output: {transcript_path}")


@app.command("start-run")
def start_run_cmd(
    run_name: str = typer.Argument(
        ...,
        help=(
            "Run name (date optional): case-key_topic, "
            "YYYY-MM-DD_case-key_topic, or YYYY-MM-DD-NNN_case-key_topic"
        ),
    ),
    force: bool = typer.Option(False, "--force", "-f", help="Overwrite if exists"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview without creating"),
    taxonomy: str | None = typer.Option(
        None,
        "--taxonomy",
        help="Target taxonomy root: fw-improvement or work",
    ),
) -> None:
    """
    新しい run を作成する。日付プレフィックスがなければ今日の日付を自動付与する。

    例:
        apsf start-run sochi-blocks_new-feature
        # → 2026-03-17-001_sochi-blocks_new-feature として作成される

        apsf start-run 2026-03-17_sochi-blocks_new-feature
        # → 日付そのまま使用

        apsf start-run sochi-blocks_new-feature --dry-run
        # → 作成内容をプレビューするだけ（実際には作成しない）
    """
    import re
    from datetime import date

    from ..config.settings import get_settings
    from ..legacy.storage.run_repository import RunRepository

    settings = get_settings()
    repo = RunRepository(runs_dir=settings.runs_dir, template_dir=settings.template_dir)
    _DATE_PREFIX_RE = re.compile(r"^\d{4}-\d{2}-\d{2}(?:-\d+)?_")

    if not _DATE_PREFIX_RE.match(run_name):
        today = date.today().strftime("%Y-%m-%d")
        if "_" not in run_name:
            typer.echo(
                f"[ERROR] Invalid run name: '{run_name}'\n"
                "   Expected: case-key_topic when date is omitted\n"
                "   Example:  apsf_start-run-sequential-naming",
                err=True,
            )
            raise typer.Exit(1)
        case_key, topic = run_name.split("_", 1)
        seq = repo.next_run_seq(today, taxonomy=taxonomy)
        run_name = repo.format_run_name(today, case_key, topic, seq=seq)
        typer.echo(f"[INFO] Date auto-prepended: {run_name}")

    if not repo.validate_run_name(run_name):
        typer.echo(
            f"[ERROR] Invalid run name: '{run_name}'\n"
            "   Expected: YYYY-MM-DD_case-key_topic or YYYY-MM-DD-NNN_case-key_topic\n"
            "   Example:  2026-03-15-001_sochi-blocks_sns-post-template",
            err=True,
        )
        raise typer.Exit(1)

    run_dir = repo.get_run_dir(run_name, taxonomy=taxonomy)

    # --dry-run: テンプレートのファイル一覧を表示して終了
    if dry_run:
        typer.echo(f"[DRY-RUN] Would create: {run_dir}")
        typer.echo(f"\nFiles to be copied from: {settings.template_dir}")
        if settings.template_dir.exists():
            for f in sorted(settings.template_dir.iterdir()):
                if f.is_file() and not f.name.startswith("."):
                    typer.echo(f"  {f.name}")
        else:
            typer.echo("  [WARN] Template directory not found")
        taxonomy_arg = f" --taxonomy {taxonomy}" if taxonomy else ""
        typer.echo(f"\nRun `apsf start-run {run_name}{taxonomy_arg}` to create.")
        return

    try:
        created_dir = repo.init_run(run_name, force=force, taxonomy=taxonomy)

        typer.echo(f"[OK] Run created: {created_dir}")
        typer.echo("\nGenerated files:")
        for f in sorted(created_dir.iterdir()):
            if f.is_file() and not f.name.startswith("."):
                typer.echo(f"  {f.name}")

        typer.echo("\nNext step:")
        typer.echo(f"  1. Open {run_name}/execution-assignment.md  <- how to execute each role")
        typer.echo(f"  2. Open {run_name}/goal.md                  <- write what you want to solve")
        typer.echo(f"\n  apsf next {run_name}   # check progress at any time")
    except (FileExistsError, FileNotFoundError) as e:
        typer.echo(f"[ERROR] {e}", err=True)
        raise typer.Exit(1)


@app.command("next")
def next_cmd(
    run_name: str = typer.Argument(..., help="Run name"),
    debug: bool = typer.Option(False, "--debug", help="Show phase detection details"),
    phase_only: bool = typer.Option(False, "--phase-only", help="Print only the phase value (machine-readable)"),
) -> None:
    """
    run の現在フェーズを検出して、次ロールにそのまま渡せる指示を表示する。

    ファイルの存在・充填状態をもとにフェーズを推定するため、
    出力はあくまで推定です。迷ったら直接ファイルを確認してください。
    --debug を付けると判定根拠（examined files / decision reason）も表示します。
    """
    from ..config.settings import get_settings
    from ..orchestration.phase_detector import PhaseDetector
    from ..orchestration.next_instruction_builder import NextInstructionBuilder
    from ..legacy.storage.run_repository import RunRepository

    settings = get_settings()
    repo = RunRepository(runs_dir=settings.runs_dir, template_dir=settings.template_dir)
    run_dir = repo.get_run_dir(run_name)

    if not run_dir.exists():
        typer.echo(f"[ERROR] Run not found: {run_dir}", err=True)
        raise typer.Exit(1)

    info = PhaseDetector(run_dir).detect()

    if phase_only:
        typer.echo(info.phase.value)
        raise typer.Exit(0)

    instruction = NextInstructionBuilder().build(info, run_name)

    sep = "=" * 60
    typer.echo(f"\n{sep}")
    typer.echo(f"Run   : {run_name}")
    typer.echo(f"Phase : {info.phase.value}")
    typer.echo(sep)

    typer.echo(f"\nNext Role : {instruction.next_role}")
    typer.echo(f"Write     : {instruction.target_file}")
    if info.files_to_read:
        typer.echo(f"Read      : {', '.join(info.files_to_read)}")
    if info.handoff_hint:
        typer.echo(f"Handoff   : {info.handoff_hint}")

    typer.echo(f"\n[{instruction.short_instruction}]")
    typer.echo(f"\nFor full AI-ready instructions:")
    typer.echo(f"  apsf write-phase {run_name} --print-prompt")

    if debug:
        typer.echo("\n--- Debug ---")
        typer.echo(f"Decision  : {info.decision_reason}")
        typer.echo(f"Existing  : {', '.join(info.existing_files) or '(none)'}")
        typer.echo(f"Filled    : {', '.join(info.filled_files) or '(none)'}")
        typer.echo(f"Unfilled  : {', '.join(info.unfilled_files) or '(none)'}")

    typer.echo(f"{sep}\n")


@app.command("transcript")
def transcript_cmd(
    run_name: str = typer.Argument(..., help="Run name"),
    overwrite: bool = typer.Option(False, "--overwrite", "-y", help="Overwrite without confirmation"),
) -> None:
    """
    run ディレクトリ内の md ファイルから transcript.md を自動生成する。

    一次記録ファイル（execution-assignment.md / goal.md / plan.md / build.md /
    review.md / handoff.md / improve.md / result.md）を所定順に連結して
    transcript.md を生成します。

    transcript は二次成果物です。正確な情報は一次記録を参照してください。
    """
    from ..config.settings import get_settings
    from ..orchestration.transcript_generator import TranscriptGenerator
    from ..legacy.storage.run_repository import RunRepository

    settings = get_settings()
    repo = RunRepository(runs_dir=settings.runs_dir, template_dir=settings.template_dir)
    run_dir = repo.get_run_dir(run_name)

    if not run_dir.exists():
        typer.echo(f"[ERROR] Run not found: {run_dir}", err=True)
        raise typer.Exit(1)

    gen = TranscriptGenerator()
    output_path = run_dir / "transcript.md"

    # ソースファイルの状況を表示
    sources = gen.list_sources(run_dir)
    found = [(f, exists) for f, exists in sources if exists]
    missing = [(f, exists) for f, exists in sources if not exists]

    typer.echo(f"\nTranscript: {run_name}")
    typer.echo(f"Sources ({len(found)}/{len(sources)} files found):")
    for filename, exists in sources:
        status = "[OK]    " if exists else "[skip]  "
        typer.echo(f"  {status} {filename}")

    if missing:
        typer.echo(f"\n[INFO] {len(missing)} file(s) will be skipped (not found).")

    if output_path.exists() and not overwrite:
        typer.echo(f"\n[WARN] transcript.md already exists: {output_path}")
        confirm = typer.confirm("Overwrite?", default=False)
        if not confirm:
            typer.echo("Cancelled.")
            raise typer.Exit(0)

    output = gen.write(run_dir, run_name)
    typer.echo(f"\n[OK] Generated: {output}")


@app.command("write-phase")
def write_phase_cmd(
    run_name: str = typer.Argument(..., help="Run name"),
    print_prompt: bool = typer.Option(
        False, "--print-prompt",
        help="Print the phase instruction only; do not read input or save",
    ),
    use_stdin: bool = typer.Option(
        False, "--stdin",
        help="Read content from stdin (piped/redirected). Suppresses interactive prompt.",
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run",
        help="Show what would be written without saving",
    ),
    force: bool = typer.Option(
        False, "--force", "-f",
        help="Overwrite target file even if it already has meaningful content",
    ),
) -> None:
    """
    現在の phase に対応する md ファイルへコンテンツを保存する。

    フェーズを自動判定し、対象ファイルを特定して保存します。
    判断は行いません。Human または外部 AI が生成したコンテンツを
    正しいファイルへ着地させる "台車" として機能します。

    使用例 (bash / Unix):
      apsf write-phase <run>                  # 対話的貼り付けモード
      apsf write-phase <run> --print-prompt   # instruction だけ stdout 出力
      apsf write-phase <run> --stdin < f.md   # ファイルから読み込み
      apsf write-phase <run> --dry-run        # 保存先を確認（保存しない）

    パイプ連携 (API なし / dogfood):
      apsf act <run> --print-prompt | claude | apsf write-phase <run> --stdin
      apsf act <run> --print-prompt | codex  | apsf write-phase <run> --stdin

    stdout/stderr 責務分離:
      stdout: instruction テキスト（--print-prompt / 対話モード）
      stderr: ステータス・ヘッダー・[Saved] などすべての UI メッセージ

    使用例 (PowerShell / Windows):
      apsf write-phase <run> --stdin          # Ctrl+Z で EOF
      Get-Content f.md | apsf write-phase <run> --stdin
      @'
      ... content ...
      '@ | apsf write-phase <run> --stdin

    注意 (PowerShell 5.1 / Windows PowerShell):
      パイプ出力が UTF-8 になるよう $OutputEncoding を設定してください:
        $OutputEncoding = [System.Text.Encoding]::UTF8
      PowerShell 7+ (pwsh) ではデフォルトで UTF-8 のため不要です。
    """
    import sys

    from ..config.settings import get_settings
    from ..orchestration.next_instruction_builder import NextInstructionBuilder
    from ..orchestration.phase_detector import Phase, PhaseDetector
    from ..legacy.storage.run_repository import RunRepository
    from .io import read_stdin_utf8

    settings = get_settings()
    repo = RunRepository(runs_dir=settings.runs_dir, template_dir=settings.template_dir)
    run_dir = repo.get_run_dir(run_name)

    if not run_dir.exists():
        typer.echo(f"[Error] Run not found: {run_dir}", err=True)
        raise typer.Exit(1)

    # ── Phase detection ─────────────────────────────────────────────────────
    detector = PhaseDetector(run_dir)
    info = detector.detect()
    instruction = NextInstructionBuilder().build(info, run_name)

    # ── Header → stderr (UI metadata) ───────────────────────────────────────
    sep = "=" * 60
    typer.echo(sep, err=True)
    typer.echo(f"Run   : {run_name}", err=True)
    typer.echo(f"Phase : {info.phase.value}", err=True)
    typer.echo(f"Role  : {instruction.next_role}", err=True)
    typer.echo(f"Write : {instruction.target_file}", err=True)
    typer.echo(sep, err=True)

    # ── Special phases ───────────────────────────────────────────────────────
    if info.phase == Phase.COMPLETE:
        typer.echo("This run is complete. Nothing to write.", err=True)
        raise typer.Exit(0)

    if info.phase == Phase.TRANSCRIPT_RECOMMENDED:
        typer.echo("transcript.md is a secondary artifact.", err=True)
        typer.echo(f"Use: apsf transcript {run_name}", err=True)
        raise typer.Exit(0)

    target_file = instruction.target_file
    if target_file == "(none)":
        typer.echo("[Info] No file to write for the current phase.", err=True)
        raise typer.Exit(0)

    target_path = run_dir / target_file

    # ── Role-boundary guard (hard-stop) ──────────────────────────────────────
    # write-phase is the final enforcement point for role-boundary rules.
    # Infer the canonical role from the current phase and check against
    # the ROLE_FORBIDDEN table in role_rules.py.
    # Reference: framework/responsibility-matrix.md
    from .role_rules import GuardSeverity, check_role_boundary, role_from_phase

    _guard_role = role_from_phase(info.phase.value)
    if _guard_role is not None:
        _guard_v = check_role_boundary(_guard_role, target_file, force=force)
        if _guard_v is not None:
            typer.echo(_guard_v.message, err=True)
            typer.echo(_guard_v.override_hint, err=True)
            if _guard_v.severity == GuardSeverity.HARD_STOP:
                raise typer.Exit(2)
            # WARNING: log and continue

    # ── Instruction display ──────────────────────────────────────────────────
    # stdout: instruction テキスト（有用なコンテンツ → パイプ先 AI / ユーザーが読む）
    # stderr: "--- Instruction ---" ラベルなど UI メタデータ
    # --stdin: instruction 省略（apsf act --print-prompt でプロンプト取得済みのため）
    if not use_stdin:
        typer.echo("\n--- Instruction ---", err=True)
        typer.echo(instruction.detailed_instruction)  # stdout

    # ── --print-prompt: instruction のみ stdout 出力して終了 ─────────────────
    if print_prompt:
        raise typer.Exit(0)

    # ── --dry-run ────────────────────────────────────────────────────────────
    if dry_run:
        typer.echo(f"\n[DRY-RUN] Would write to: {target_path}", err=True)
        raise typer.Exit(0)

    # ── Overwrite protection (before reading stdin) ───────────────────────────
    # _has_any_content（1行以上）で判定: 部分記入のファイルも保護する
    if not force and detector._has_any_content(target_file):
        if use_stdin:
            typer.echo(
                f"[Error] {target_file} already has content. Refusing to overwrite.",
                err=True,
            )
            typer.echo(f"  Path : {target_path}", err=True)
            typer.echo(
                f"  To overwrite: apsf write-phase {run_name} --stdin --force",
                err=True,
            )
            raise typer.Exit(1)
        else:
            typer.echo(f"\n[Warn] {target_file} already has content: {target_path}", err=True)
            confirmed = typer.confirm("Overwrite existing content?", default=False)
            if not confirmed:
                typer.echo("Cancelled.", err=True)
                raise typer.Exit(0)

    # ── Force overwrite notice → stderr ──────────────────────────────────────
    # --force --stdin で既存コンテンツを上書きするとき、誤上書きを防ぐための警告
    if force and use_stdin and detector._has_any_content(target_file):
        typer.echo(
            f"[Warn] Overwriting {target_file} (current phase target)", err=True
        )

    # ── Write target notice → stderr ─────────────────────────────────────────
    # 保存直前に保存先を明示してミス・迷いを防ぐ
    dash = "-" * 60
    if use_stdin:
        # --stdin: instruction を省略した分、ここで保存先を明示
        typer.echo(f"\n{dash}", err=True)
        typer.echo(f"  Saving to : {target_file}", err=True)
        typer.echo(f"  Phase     : {info.phase.value}", err=True)
        typer.echo(f"  Run       : {run_name}", err=True)
        typer.echo(dash, err=True)
    else:
        # interactive: instruction の後にも保存先をリマインド
        typer.echo(f"\n{dash}", err=True)
        typer.echo(f"  Write to  : {target_file}", err=True)
        typer.echo(f"  Phase     : {info.phase.value}", err=True)
        typer.echo(dash, err=True)
        typer.echo(f"  Paste content below. Finish with EOF:", err=True)
        typer.echo(f"    Windows: Ctrl+Z then Enter", err=True)
        typer.echo(f"    Unix   : Ctrl+D", err=True)
        typer.echo("", err=True)

    raw_content = read_stdin_utf8()
    content = _sanitize_phase_input(raw_content)

    # ── Validation: empty / template-only input ──────────────────────────────
    if not PhaseDetector.is_meaningful_text(content):
        typer.echo(
            "[Error] Input is empty or contains only template scaffolding. Nothing saved.",
            err=True,
        )
        raise typer.Exit(1)

    # ── Save ─────────────────────────────────────────────────────────────────
    target_path.write_text(content, encoding="utf-8")

    typer.echo(f"\n{sep}", err=True)
    typer.echo(f"[Saved] {target_file}", err=True)
    typer.echo(f"  Path : {target_path}", err=True)
    typer.echo(f"[Next]  apsf next {run_name}", err=True)
    typer.echo(sep, err=True)


@app.command("generate-setup")
def generate_setup_cmd(
    run_name: str = typer.Argument(..., help="Run name"),
    print_prompt: bool = typer.Option(
        False, "--print-prompt",
        help="Print the generation prompt only to stdout (for pipe use)",
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run",
        help="Show what would be written without saving (no API key needed)",
    ),
    force: bool = typer.Option(
        False, "--force", "-f",
        help="Overwrite execution-assignment.md even if it already has content",
    ),
) -> None:
    """
    goal.md を読んで execution-assignment.md を自動生成する。

    goal.md が記入済みで execution-assignment.md が未記入の場合のみ実行する。
    HUMAN_OWNED_PHASES は変更しない。apsf act は引き続き SETUP_NEEDED で停止する。

    使用例 (API あり):
      apsf generate-setup <run>                # API で自動生成・保存
      apsf generate-setup <run> --force        # 既存コンテンツを上書き

    使用例 (API なし / dogfood):
      apsf generate-setup <run> --print-prompt # プロンプトのみ stdout 出力
      apsf generate-setup <run> --dry-run      # 保存なし（確認のみ）

    パイプ連携:
      apsf generate-setup <run> --print-prompt | claude | apsf write-phase <run> --stdin
    """
    from ..config.settings import get_settings
    from ..orchestration.act_service import ActError, ActService
    from ..orchestration.phase_detector import Phase, PhaseDetector
    from ..prompts.renderer import render_setup_prompt
    from ..core.providers.base import GenerateRequest, ProviderError
    from ..legacy.storage.run_repository import RunRepository

    settings = get_settings()
    repo = RunRepository(runs_dir=settings.runs_dir, template_dir=settings.template_dir)
    run_dir = repo.get_run_dir(run_name)

    if not run_dir.exists():
        typer.echo(f"[Error] Run not found: {run_dir}", err=True)
        raise typer.Exit(1)

    detector = PhaseDetector(run_dir)

    # goal.md が未記入なら停止（Human が先に書く必要がある）
    if not detector._is_filled("goal.md"):
        typer.echo(
            "[Error] goal.md must be filled before generating setup.\n"
            f"   Path: {run_dir / 'goal.md'}",
            err=True,
        )
        raise typer.Exit(1)

    # execution-assignment.md が記入済みなら上書き保護
    if not force and detector._has_any_content("execution-assignment.md"):
        typer.echo(
            "[Info] execution-assignment.md already has content. Use --force to overwrite.\n"
            f"   Path: {run_dir / 'execution-assignment.md'}",
            err=True,
        )
        raise typer.Exit(0)

    goal_content = (run_dir / "goal.md").read_text(encoding="utf-8")
    prompt = render_setup_prompt(goal_content)

    # --print-prompt: プロンプトのみ stdout 出力して終了
    if print_prompt:
        typer.echo(prompt)
        raise typer.Exit(0)

    sep = "=" * 60
    typer.echo(sep, err=True)
    typer.echo(f"Run  : {run_name}", err=True)
    typer.echo(f"Phase: SETUP_NEEDED", err=True)
    typer.echo(f"Write: execution-assignment.md", err=True)
    typer.echo(sep, err=True)

    # --dry-run: 保存なし
    if dry_run:
        typer.echo(f"\n[DRY-RUN] Would generate: execution-assignment.md")
        typer.echo(f"\n--- Prompt ---")
        typer.echo(prompt)
        raise typer.Exit(0)

    # Provider 取得（ActService._get_provider を PLAN_NEEDED phase 経由で呼ぶ。
    # _PHASE_TO_ROLE[PLAN_NEEDED] = Role.PLANNER なので model-assignment.md の
    # Planner 設定が参照される）
    service = ActService()
    try:
        provider = service._get_provider(Phase.PLAN_NEEDED, run_dir, settings)
    except ActError as exc:
        typer.echo(f"[Error] {exc}", err=True)
        raise typer.Exit(1)

    # LLM 実行
    try:
        response = provider.generate(GenerateRequest(prompt=prompt))
    except ProviderError as exc:
        typer.echo(f"[Error] LLM generation failed: {exc}", err=True)
        raise typer.Exit(1)

    content = response.content.strip()
    if not PhaseDetector.is_meaningful_text(content):
        typer.echo(
            "[Error] LLM returned empty or template-only content. Nothing saved.",
            err=True,
        )
        raise typer.Exit(1)

    target_path = run_dir / "execution-assignment.md"
    target_path.write_text(content, encoding="utf-8")

    typer.echo(f"\n[Saved] execution-assignment.md")
    typer.echo(f"  Path : {target_path}")
    typer.echo(f"[Next]  apsf next {run_name}", err=True)


@app.command("act")
def act_cmd(
    run_name: str = typer.Argument(..., help="Run name"),
    force: bool = typer.Option(
        False, "--force", "-f",
        help="Overwrite target file even if it already has content",
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run",
        help="Show phase info and full prompt without saving (no API key needed)",
    ),
    print_prompt: bool = typer.Option(
        False, "--print-prompt",
        help="Print the generation prompt only to stdout (for Claude Code / Codex CLI / pipe)",
    ),
    executor: Optional[str] = typer.Option(
        None, "--executor",
        help="Executor for the phase. 'claude-cli' pipes prompt through claude CLI subprocess.",
    ),
) -> None:
    """
    現在の phase を判定し、phase 文書を自動生成・保存する。

    Human 担当の phase（goal.md / judge 判断等）では停止し、何も生成しない。
    Auto 担当の phase（plan.md / build.md / review.md）のみ実行する。

    1 回の実行で 1 phase だけを処理する（v0）。

    使用例 (API あり):
      apsf act <run>               # LLM を呼び出して自動生成・保存
      apsf act <run> --force       # 既存コンテンツを上書き

    使用例 (API なし / dogfood):
      apsf act <run> --dry-run     # phase 情報 + プロンプト全文を確認
      apsf act <run> --print-prompt              # プロンプトのみ stdout 出力
      apsf act <run> --print-prompt > prompt.md  # ファイルに保存
      apsf act <run> --print-prompt | claude     # CLI に直接パイプ

    API キー設定 (自動実行時のみ必要):
      ANTHROPIC_API_KEY / OPENAI_API_KEY / GEMINI_API_KEY のいずれか
      model-assignment.md が存在する場合はそこで指定したモデルを優先する
    """
    from ..config.settings import get_settings
    from ..orchestration.act_service import ActError, ActService
    from ..legacy.storage.run_repository import RunRepository

    settings = get_settings()
    repo = RunRepository(runs_dir=settings.runs_dir, template_dir=settings.template_dir)
    run_dir = repo.get_run_dir(run_name)

    if not run_dir.exists():
        typer.echo(f"[Error] Run not found: {run_dir}", err=True)
        raise typer.Exit(1)

    # ── --executor claude-cli: subprocess パイプで claude CLI 経由実行 ────────
    if executor == "claude-cli":
        import shutil as _shutil
        import subprocess

        if not _shutil.which("claude"):
            typer.echo(
                "[Error] 'claude' not found in PATH. Install Claude Code CLI.",
                err=True,
            )
            raise typer.Exit(1)

        timeout_sec = _get_claude_timeout_sec()

        typer.echo("[1/3] generate prompt...", err=True)
        prompt_result = subprocess.run(
            ["apsf", "act", run_name, "--print-prompt"],
            capture_output=True, text=True, encoding="utf-8",
        )
        if prompt_result.returncode != 0:
            typer.echo(
                f"[FAIL] apsf act --print-prompt (exit={prompt_result.returncode})",
                err=True,
            )
            raise typer.Exit(prompt_result.returncode)

        typer.echo("[2/3] invoke claude -p...", err=True)
        try:
            claude_result = subprocess.run(
                ["claude", "-p", "--no-tools"],
                input=prompt_result.stdout,
                capture_output=True,
                text=True,
                encoding="utf-8",
                timeout=timeout_sec,
            )
        except subprocess.TimeoutExpired:
            typer.echo(
                f"[FAIL] claude -p timed out after {timeout_sec}s",
                err=True,
            )
            typer.echo(
                f"       Run remains unchanged. Check: apsf next {run_name}",
                err=True,
            )
            raise typer.Exit(124)
        if claude_result.stderr:
            typer.echo(claude_result.stderr, err=True)
        if claude_result.returncode != 0:
            typer.echo(
                f"[FAIL] claude -p (exit={claude_result.returncode})",
                err=True,
            )
            raise typer.Exit(claude_result.returncode)

        typer.echo("[3/3] write phase...", err=True)
        write_result = subprocess.run(
            ["apsf", "write-phase", run_name, "--stdin"],
            input=claude_result.stdout,
            capture_output=True, text=True, encoding="utf-8",
        )
        if write_result.stdout:
            typer.echo(write_result.stdout)
        if write_result.stderr:
            typer.echo(write_result.stderr, err=True)
        raise typer.Exit(write_result.returncode)

    # --print-prompt / --dry-run はいずれも LLM を呼ばない
    resolve_dry = dry_run or print_prompt

    # ── Role-boundary preflight ───────────────────────────────────────────────
    # Emit a warning before invoking the AI if the current phase/role would
    # be writing a forbidden artifact. Hard-stops are enforced by write-phase;
    # act emits a preflight warning to catch issues as early as possible.
    if not resolve_dry:
        from .role_rules import GuardSeverity, check_role_boundary, role_from_phase
        from ..orchestration.phase_detector import PhaseDetector as _PreflightDetector

        _pf_info = _PreflightDetector(run_dir).detect()
        _pf_role = role_from_phase(_pf_info.phase.value)
        if _pf_role is not None:
            _pf_v = check_role_boundary(_pf_role, _pf_info.file_to_write, force=force)
            if _pf_v is not None:
                typer.echo(f"[Preflight] {_pf_v.message}", err=True)
                typer.echo(_pf_v.override_hint, err=True)
                if _pf_v.severity == GuardSeverity.HARD_STOP:
                    raise typer.Exit(2)
                # WARNING: log and continue

    sep = "=" * 60

    try:
        result = ActService().execute(
            run_dir=run_dir,
            run_name=run_name,
            force=force,
            dry_run=resolve_dry,
            settings=settings,
        )
    except ActError as exc:
        typer.echo(f"[Error] {exc}", err=True)
        raise typer.Exit(1)

    # ── --print-prompt: プロンプトのみ stdout 出力（パイプ・リダイレクト用）──
    if print_prompt:
        if result.mode in ("human", "complete"):
            typer.echo(f"[Stop] Human phase ({result.phase.value}): {result.stop_reason}", err=True)
            raise typer.Exit(0)
        typer.echo(result.prompt)
        raise typer.Exit(0)

    # ── ヘッダー表示 ─────────────────────────────────────────────────────────
    typer.echo(sep)
    typer.echo(f"Run  : {run_name}")
    typer.echo(f"Phase: {result.phase.value}")
    typer.echo(f"Mode : {result.mode}")
    typer.echo(sep)

    # ── 結果別表示 ────────────────────────────────────────────────────────────
    if result.mode in ("human", "complete"):
        typer.echo(f"\n[Stop] {result.stop_reason}")
        if result.mode == "human" and result.target_file not in ("(none)", ""):
            typer.echo(f"  --> Open: {run_dir / result.target_file}")
            typer.echo(f"  --> Then: apsf act {run_name}")

    elif result.mode == "already_filled":
        typer.echo(f"\n[Info] {result.stop_reason}", err=True)
        typer.echo(f"       Use: apsf act {run_name} --force", err=True)

    elif result.mode == "auto":
        if result.files_read:
            typer.echo(f"\nRead : {', '.join(result.files_read)}")
        typer.echo(f"Write: {result.target_file}")

        if dry_run:
            typer.echo(f"\n[DRY-RUN] Would generate: {result.target_file}")
            typer.echo(f"\n--- Prompt ---")
            typer.echo(result.prompt)
        elif result.generated:
            typer.echo(f"\n[Saved] {run_dir / result.target_file}")
            typer.echo(f"[Next]  Run: apsf next {run_name}")


@app.command("check-env")
def check_env() -> None:
    """
    環境変数の設定状況を確認する。

    v0.1 では API キーは optional（CLI/Human 実行には不要）。
    """
    from ..config.settings import get_settings

    settings = get_settings()

    typer.echo("\nEnvironment Check")
    typer.echo("=" * 50)
    typer.echo(f"  Framework root:    {settings.framework_root}")
    typer.echo(f"  Runs dir:          {settings.runs_dir}")
    typer.echo(f"  Workspaces dir:    {settings.workspaces_dir}")
    typer.echo(f"  Template dir:      {settings.template_dir}")
    typer.echo("")
    typer.echo("  API Keys (optional - not required for CLI/Human execution):")

    for provider in ["openai", "anthropic", "gemini"]:
        status = "[SET]" if settings.has_api_key(provider) else "  not set"
        typer.echo(f"    {provider.upper():<12} {status}")

    configured = settings.configured_api_providers()
    typer.echo("")
    if configured:
        typer.echo(f"  Configured API providers: {', '.join(configured)}")
    else:
        typer.echo(
            "  No API keys set - that's OK for v0.1 CLI/Human execution.\n"
            "  For future-api executor: add keys to .env and run:\n"
            "    pip install 'apsf[api]'"
        )


@app.command("view")
def view_cmd(
    port: int = typer.Option(8000, "--port", "-p", help="Port to run the viewer on"),
    host: str = typer.Option("127.0.0.1", "--host", help="Host to bind for the viewer"),
) -> None:
    """
    APSF Viewer (軽量 GUI) を起動する。

    ブラウザで runs/ ディレクトリの状態を可視化し、
    次に何をすべきかを確認できます。
    """
    import webbrowser

    import uvicorn

    from ..viewer.api import app

    url = f"http://{host}:{port}"
    typer.echo(f"\n[OK] Starting APSF Viewer at {url}")
    typer.echo("Press Ctrl+C to stop.")

    # Try to open browser
    try:
        webbrowser.open(url)
    except Exception:
        pass

    uvicorn.run(app, host=host, port=port)


@app.command("build")
def build_cmd(
    run_name: str = typer.Argument(..., help="Run name"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview command without running"),
) -> None:
    """
    BUILD_NEEDED フェーズ向けのビルド実行ガイドを表示する。

    Builder は filesystem tool access が必要なため、apsf-claude-act.ps1 (tools disabled)
    ではなく apsf-claude-build.ps1 を使う。

    Phase Routing Table:
      PLAN_NEEDED    → apsf act          → apsf-claude-act.ps1  (tools: disabled)
      REVIEW_NEEDED  → apsf act          → apsf-claude-act.ps1  (tools: disabled)
      BUILD_NEEDED   → apsf build        → apsf-claude-build.ps1 (tools: ENABLED)
    """
    from ..config.settings import get_settings
    from ..orchestration.phase_detector import PhaseDetector
    from ..legacy.storage.run_repository import RunRepository

    settings = get_settings()
    repo = RunRepository(runs_dir=settings.runs_dir, template_dir=settings.template_dir)
    run_dir = repo.get_run_dir(run_name)

    if not run_dir.exists():
        typer.echo(f"[ERROR] Run not found: {run_dir}", err=True)
        raise typer.Exit(1)

    info = PhaseDetector(run_dir).detect()
    phase = info.phase.value

    # Locate the build script
    scripts_dir = settings.framework_root / "scripts"
    build_script = scripts_dir / "apsf-claude-build.ps1"

    sep = "=" * 60
    typer.echo(f"\n{sep}")
    typer.echo(f"Run   : {run_name}")
    typer.echo(f"Phase : {phase}")
    typer.echo(sep)

    if phase != "BUILD_NEEDED":
        typer.echo(f"\n[Warn] Phase is '{phase}', not BUILD_NEEDED.", err=True)
        typer.echo(f"       Use 'apsf act {run_name}' for PLAN_NEEDED / REVIEW_NEEDED.", err=True)

    typer.echo(f"\nBuilder requires filesystem tool access.")
    typer.echo(f"Use the dedicated build script:\n")
    typer.echo(f"  PowerShell:")
    typer.echo(f"    $run = \"{run_name}\"")
    typer.echo(f"    .\\scripts\\apsf-claude-build.ps1 $run")
    typer.echo(f"")
    typer.echo(f"  Dry-run (preview assembled prompt):")
    typer.echo(f"    .\\scripts\\apsf-claude-build.ps1 $run -DryRun")
    typer.echo(f"")

    if not build_script.exists():
        typer.echo(f"[Warn] Build script not found: {build_script}", err=True)
    else:
        typer.echo(f"Script: {build_script}")

    typer.echo(f"\nFallback (direct claude with tools, interactive):")
    typer.echo(f"  claude --tools Bash,Edit,Glob,Grep,Read,Write")
    typer.echo(f"")
    typer.echo(f"[Note] Builder writes files directly to disk.")
    typer.echo(f"       build.md is an optional log artifact the Builder should also create.")
    typer.echo(f"{sep}\n")


if __name__ == "__main__":
    app()
