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

import sys
from pathlib import Path

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

app = typer.Typer(
    name="apsf",
    help="AI Problem Solving Framework - CLI/Human-first, multi-model problem solving OS",
    add_completion=False,
)


@app.command("init-run")
def init_run(
    run_name: str = typer.Argument(..., help="Run name: YYYY-MM-DD_case-key_topic"),
    force: bool = typer.Option(False, "--force", "-f", help="Overwrite if exists"),
) -> None:
    """指定した名前で runs/ に新しい run ディレクトリを作成する。"""
    from ..config.settings import get_settings
    from ..storage.run_repository import RunRepository

    settings = get_settings()
    repo = RunRepository(runs_dir=settings.runs_dir, template_dir=settings.template_dir)

    if not repo.validate_run_name(run_name):
        typer.echo(
            f"[ERROR] Invalid run name: '{run_name}'\n"
            "   Expected: YYYY-MM-DD_case-key_topic\n"
            "   Example:  2026-03-15_sochi-blocks_sns-post-template",
            err=True,
        )
        raise typer.Exit(1)

    try:
        run_dir = repo.init_run(run_name, force=force)
        typer.echo(f"[OK] Run created: {run_dir}")
        typer.echo("\nNext steps:")
        typer.echo(f"  1. Edit {run_dir}/execution-assignment.md  <- how to execute each role")
        typer.echo(f"  2. Edit {run_dir}/model-assignment.md      <- which model to use (optional)")
        typer.echo(f"  3. Edit {run_dir}/goal.md                  <- what to solve")
        typer.echo(f"  4. Run: apsf show-execution-plan {run_name}")
    except (FileExistsError, FileNotFoundError) as e:
        typer.echo(f"[ERROR] {e}", err=True)
        raise typer.Exit(1)


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
    from ..domain.models import Role, ExecutionType

    settings = get_settings()
    run_dir = settings.runs_dir / run_name
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

    settings = get_settings()
    run_dir = settings.runs_dir / run_name
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

    settings = get_settings()
    run_dir = settings.runs_dir / run_name

    if not run_dir.exists():
        typer.echo(f"[ERROR] Run not found: {run_dir}", err=True)
        raise typer.Exit(1)

    # 参照ファイルの存在チェック
    source_files = [
        ("execution-assignment.md", "how to run"),
        ("goal.md",                 "what to solve"),
        ("plan.md",                 "how to approach"),
        ("handoff.md",              "what was passed between roles"),
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
        status = "[OK]     " if path.exists() else "[MISSING]"
        if not path.exists():
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
        ("Planning",              "plan.md + handoff.md",                "Problem Structure, Selected Approach, handoff summary"),
        ("Draft Generation",      "workspaces/junior_builder/",          "Number of drafts, categories, key decisions"),
        ("Build",                 "build.md + handoff.md",               "What was built, decisions made, deviations"),
        ("Review",                "review.md + handoff.md",              "Critical/Major/Minor count, overall assessment"),
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
        ..., help="Run name (date optional): case-key_topic or YYYY-MM-DD_case-key_topic"
    ),
    force: bool = typer.Option(False, "--force", "-f", help="Overwrite if exists"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview without creating"),
) -> None:
    """
    新しい run を作成する。日付プレフィックスがなければ今日の日付を自動付与する。

    例:
        apsf start-run sochi-blocks_new-feature
        # → 2026-03-17_sochi-blocks_new-feature として作成される

        apsf start-run 2026-03-17_sochi-blocks_new-feature
        # → 日付そのまま使用

        apsf start-run sochi-blocks_new-feature --dry-run
        # → 作成内容をプレビューするだけ（実際には作成しない）
    """
    import re
    from datetime import date

    from ..config.settings import get_settings
    from ..storage.run_repository import RunRepository

    _DATE_PREFIX_RE = re.compile(r"^\d{4}-\d{2}-\d{2}_")

    if not _DATE_PREFIX_RE.match(run_name):
        today = date.today().strftime("%Y-%m-%d")
        run_name = f"{today}_{run_name}"
        typer.echo(f"[INFO] Date auto-prepended: {run_name}")

    settings = get_settings()
    repo = RunRepository(runs_dir=settings.runs_dir, template_dir=settings.template_dir)

    if not repo.validate_run_name(run_name):
        typer.echo(
            f"[ERROR] Invalid run name: '{run_name}'\n"
            "   Expected: YYYY-MM-DD_case-key_topic\n"
            "   Example:  2026-03-15_sochi-blocks_sns-post-template",
            err=True,
        )
        raise typer.Exit(1)

    run_dir = settings.runs_dir / run_name

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
        typer.echo(f"\nRun `apsf start-run {run_name}` to create.")
        return

    try:
        created_dir = repo.init_run(run_name, force=force)

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

    settings = get_settings()
    run_dir = settings.runs_dir / run_name

    if not run_dir.exists():
        typer.echo(f"[ERROR] Run not found: {run_dir}", err=True)
        raise typer.Exit(1)

    info = PhaseDetector(run_dir).detect()
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

    settings = get_settings()
    run_dir = settings.runs_dir / run_name

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
    from .io import read_stdin_utf8

    settings = get_settings()
    run_dir = settings.runs_dir / run_name

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

    content = read_stdin_utf8()

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

    settings = get_settings()
    run_dir = settings.runs_dir / run_name

    if not run_dir.exists():
        typer.echo(f"[Error] Run not found: {run_dir}", err=True)
        raise typer.Exit(1)

    # --print-prompt / --dry-run はいずれも LLM を呼ばない
    resolve_dry = dry_run or print_prompt

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
        typer.echo(f"\n[Info] {result.stop_reason}")
        typer.echo(f"       Use: apsf act {run_name} --force")

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


if __name__ == "__main__":
    app()
