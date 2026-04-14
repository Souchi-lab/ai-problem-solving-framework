<#
.SYNOPSIS
    APSF Build wrapper — runs claude with file-system tool access for BUILD_NEEDED phase.

.DESCRIPTION
    Invokes: claude -p --tools <toolset> < <assembled prompt>

    Unlike apsf-claude-act.ps1 (which disables tools for PLAN/REVIEW phases),
    this script enables filesystem tool access so Builder can read, edit, and
    create real project files.

    Contract:
      - Builder writes files DIRECTLY to disk.
      - Builder MUST also write the canonical build record to build.md.
      - Do not write only build_rerun_*.md or other timestamped substitutes.
      - This script does NOT capture stdout and save a Markdown artifact.
      - build_review.md (if present) is prepended to the assembled prompt.

    Dependency policy for A1 (validated):
      claude -p --tools "Bash,Edit,Glob,Grep,Read,Write" is supported.

    Invocation modes:
      apsf-claude-build.ps1 <run>                    # standard: auto-assemble context
      apsf-claude-build.ps1 <run> -DryRun            # preview assembled prompt, no exec
      apsf-claude-build.ps1 <run> -PromptFile <path> # use custom prompt file

.PARAMETER Run
    Run name (e.g. "2026-03-23-001_fw-improvement_rebuild-builder-execution-path")

.PARAMETER DryRun
    Print assembled prompt and exit — no claude invocation.

.PARAMETER PromptFile
    Path to a custom prompt file. If omitted, auto-assembled from plan.md + build_review.md.

.PARAMETER MaxTurns
    Maximum number of agentic turns for claude. Default: 10.

.PARAMETER Tools
    Comma-separated tool names to pass to claude. Default enables all standard tools.

.EXAMPLE
    $run = "2026-03-23-001_fw-improvement_rebuild-builder-execution-path"
    .\scripts\apsf-claude-build.ps1 $run
    .\scripts\apsf-claude-build.ps1 $run -DryRun
#>

param(
    [Parameter(Mandatory = $true, Position = 0)]
    [string]$Run,

    [switch]$DryRun,

    [string]$PromptFile = "",

    [int]$MaxTurns = 10,

    [string]$Tools = "Bash,Edit,Glob,Grep,Read,Write,mcp__filesystem__read_file,mcp__filesystem__write_file,mcp__filesystem__list_directory"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# ── Guards ───────────────────────────────────────────────────────────────

if (-not (Get-Command "apsf" -ErrorAction SilentlyContinue)) {
    Write-Host "[Error] 'apsf' not found. Run: pip install -e ." -ForegroundColor Red
    exit 1
}
if (-not (Get-Command "claude" -ErrorAction SilentlyContinue)) {
    Write-Host "[Error] 'claude' not found. Install Claude Code CLI." -ForegroundColor Red
    exit 1
}

# ── Resolve run directory ─────────────────────────────────────────────────

$projectRoot = Split-Path $PSScriptRoot -Parent
$runsRoot = Join-Path $projectRoot "runs"
$resolvedRunPath = @"
import sys
from pathlib import Path
from apsf.legacy.storage.run_repository import RunRepository

sys.stdout.reconfigure(encoding="utf-8")

project_root = Path(r"$projectRoot")
repo = RunRepository(
    runs_dir=project_root / "runs",
    template_dir=project_root / "runs" / "_template",
)
run_name = r"$Run"
parts = [part for part in run_name.split("/") if part]
if len(parts) == 3 and parts[0] in {"work", "fw-improvement"}:
    print(repo.get_child_run_dir(parts[1], parts[2], taxonomy=parts[0]))
elif len(parts) == 2 and parts[0] in {"work", "fw-improvement"}:
    print(repo.get_run_dir(parts[1], taxonomy=parts[0]))
elif len(parts) == 2:
    parent, child = parts
    direct = project_root / "runs" / parent / child
    if direct.is_dir():
        print(direct)
    else:
        for taxonomy in ("fw-improvement", "work"):
            candidate = project_root / "runs" / taxonomy / parent / child
            if candidate.is_dir():
                print(candidate)
                break
        else:
            print(repo.get_child_run_dir(parent, child))
else:
    print(repo.get_run_dir(run_name))
"@ | python -

if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($resolvedRunPath)) {
    Write-Host "[Error] Run not found: $Run" -ForegroundColor Red
    Write-Host "  Searched under: $runsRoot" -ForegroundColor DarkGray
    exit 1
}

$runPath = $resolvedRunPath.Trim()
if (-not (Test-Path -LiteralPath $runPath -PathType Container)) {
    Write-Host "[Error] Run not found: $Run" -ForegroundColor Red
    Write-Host "  Resolved path does not exist: $runPath" -ForegroundColor DarkGray
    exit 1
}
Write-Host "[APSF] run:       $Run" -ForegroundColor Cyan
Write-Host "[APSF] run path:  $runPath" -ForegroundColor Cyan
Write-Host "[APSF] mode:      BUILD (tool-enabled)" -ForegroundColor Cyan

# ── Phase guard ──────────────────────────────────────────────────────────

$currentPhase = @"
from pathlib import Path
import sqlite3
from apsf.core.manifest.manifest_repository import ManifestRepository
from apsf.core.state.run_state import PhaseStatus, RunState
from apsf.core.state.run_state_repository import RunStateRepository
from apsf.legacy.orchestration.phase_detector import PhaseDetector
from apsf.legacy.orchestration.act_service import _phase_to_owner

project_root = Path(r"$projectRoot")
run_dir = Path(r"$runPath")
run_name = r"$Run"

state_repo = RunStateRepository(run_dir)
state = state_repo.load()
phase = state.current_phase if state is not None and state.current_phase else PhaseDetector(run_dir).detect().phase.value

conn = None
try:
    conn = sqlite3.connect(str(project_root / "viewer.db"))
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT result_status, command, stdout_summary FROM action_executions WHERE run_name = ? ORDER BY id DESC LIMIT 5",
        (run_name,),
    ).fetchall()
    for row in rows:
        result_status = str(row["result_status"] or "").strip().upper()
        command = str(row["command"] or "").strip().lower()
        stdout_summary = str(row["stdout_summary"] or "").strip()
        if "apsf-wrapper-build.ps1" not in command:
            continue
        if result_status in ("PARTIAL", "FAILED") and "not BUILD_NEEDED" in stdout_summary:
            continue
        if result_status == "PARTIAL" and phase != "BUILD_NEEDED":
            phase = "BUILD_NEEDED"
            if state is None:
                state = RunState(
                    run_id=run_dir.name,
                    current_phase=phase,
                    phase_status=PhaseStatus.PENDING.value,
                    current_owner=_phase_to_owner(phase),
                    retry_count=0,
                    last_error="",
                    active_handoff_id="",
                    gate_failures=[],
                )
            else:
                state.current_phase = phase
                state.phase_status = PhaseStatus.PENDING.value
                state.current_owner = _phase_to_owner(phase)
                state.retry_count = 0
                state.last_error = ""
                state.active_handoff_id = ""
                state.gate_failures = []
            state_repo.save(state)
            ManifestRepository(run_dir).remove_entries(["build.md"])
        break
finally:
    if conn is not None:
        conn.close()

print(phase)
"@ | python -
Write-Host "[APSF] phase:     $currentPhase" -ForegroundColor Cyan

if ($currentPhase -ne "BUILD_NEEDED" -and $currentPhase -ne "UNKNOWN") {
    Write-Host ""
    Write-Host "[Warn] Current phase is '$currentPhase', not BUILD_NEEDED." -ForegroundColor Yellow
    Write-Host "       This script is designed for BUILD_NEEDED only." -ForegroundColor DarkGray
    Write-Host "       For PLAN_NEEDED / REVIEW_NEEDED, use apsf-claude-act.ps1" -ForegroundColor DarkGray
    Write-Host "       Suggested next step:" -ForegroundColor DarkGray
    Write-Host "         .\\scripts\\apsf-wrapper-act.ps1 $Run -Backend claude-cli" -ForegroundColor DarkGray
    exit 2
}

# ── Model Assignment (Builder) ────────────────────────────────────────────
# model-assignment.md が存在すれば Builder の assignment を読んで尊重する。
# ファイルなし / 行なし → provider=unset として通常通り実行。

$assignmentLines = @(apsf model-assignment $Run --role Builder 2>$null)
$assignmentProvider = ($assignmentLines | Where-Object { $_ -match "^provider=(.+)" } | Select-Object -First 1) -replace "^provider=", ""
$assignmentModel    = ($assignmentLines | Where-Object { $_ -match "^model=(.+)"    } | Select-Object -First 1) -replace "^model=", ""
$assignmentHuman    = ($assignmentLines | Where-Object { $_ -eq "human=true"        } | Measure-Object).Count -gt 0

if ($assignmentHuman) {
    Write-Host ""
    Write-Host "[Stop] model-assignment.md: Builder is human-assigned." -ForegroundColor Yellow
    Write-Host "       Perform this build phase manually." -ForegroundColor DarkGray
    Write-Host "       check: apsf next $Run" -ForegroundColor DarkGray
    exit 0
}

if (-not [string]::IsNullOrWhiteSpace($assignmentProvider) -and $assignmentProvider -ne "unset") {
    Write-Host "[APSF] builder:   provider=$assignmentProvider$(if ($assignmentModel) { " model=$assignmentModel" })" -ForegroundColor Cyan
    if ($assignmentProvider -ne "anthropic") {
        Write-Host "[Warn] model-assignment.md specifies provider=$assignmentProvider, but build wrapper uses Claude CLI (anthropic only)." -ForegroundColor Yellow
        Write-Host "       Proceeding with Claude CLI default model." -ForegroundColor DarkGray
        $assignmentModel = ""
    }
} else {
    Write-Host "[APSF] builder:   (no model-assignment.md — using claude default)" -ForegroundColor DarkGray
}

# ── Builder Specialist (B-TYPE) ───────────────────────────────────────────
# execution-assignment.md の B-TYPE を解決し、specialist content があれば prompt に注入する。
# gap の場合は warning を出し、generic Builder のまま続行する（停止しない）。

$specialistLines  = @(apsf builder-specialist $Run 2>$null)
$specialistCode   = ($specialistLines | Where-Object { $_ -match "^code=(.+)" }  | Select-Object -First 1) -replace "^code=",  ""
$specialistMode   = ($specialistLines | Where-Object { $_ -match "^mode=(.+)" }  | Select-Object -First 1) -replace "^mode=",  ""
$specialistGap    = ($specialistLines | Where-Object { $_ -eq "gap=true" }        | Measure-Object).Count -gt 0
$specialistContent = $null

if ($specialistGap) {
    Write-Host "[Warn] Builder specialist gap: no B-TYPE match. Using generic Builder." -ForegroundColor Yellow
} elseif (-not [string]::IsNullOrWhiteSpace($specialistCode)) {
    Write-Host "[APSF] specialist: $specialistCode ($specialistMode)" -ForegroundColor Cyan
    $rawContent = @(apsf builder-specialist $Run --print-content 2>$null)
    if ($rawContent.Count -gt 0) {
        $specialistContent = $rawContent -join [Environment]::NewLine
    }
} else {
    Write-Host "[APSF] specialist: (none — generic Builder)" -ForegroundColor DarkGray
}

# ── Assemble prompt ───────────────────────────────────────────────────────

function Read-RunFile {
    param([string]$FileName)
    $path = Join-Path $runPath $FileName
    if (Test-Path -LiteralPath $path) {
        return Get-Content -LiteralPath $path -Raw -Encoding UTF8
    }
    return $null
}

function Inject-DependencyPromptContext {
    param(
        [string]$ProjectRoot,
        [string]$RunDir,
        [string]$PromptText
    )

    $inputPath = [System.IO.Path]::GetTempFileName()
    $outputPath = [System.IO.Path]::GetTempFileName()
    try {
        [System.IO.File]::WriteAllText($inputPath, $PromptText, [System.Text.Encoding]::UTF8)
        @"
import sys
from pathlib import Path
from apsf.core.dependencies.run_dependencies import (
    ArtifactNotFoundError,
    DependencyNotFoundError,
    IncompleteDependencyError,
    inject_dependency_context,
)

project_root = Path(r"$ProjectRoot")
run_dir = Path(r"$RunDir")
input_path = Path(r"$inputPath")
output_path = Path(r"$outputPath")
prompt_text = input_path.read_text(encoding="utf-8")

try:
    result = inject_dependency_context(
        project_root=project_root,
        run_dir=run_dir,
        prompt_text=prompt_text,
    )
except IncompleteDependencyError as exc:
    print(str(exc), file=sys.stderr)
    raise SystemExit(3)
except (DependencyNotFoundError, ArtifactNotFoundError) as exc:
    print(str(exc), file=sys.stderr)
    raise SystemExit(1)

output_path.write_text(result, encoding="utf-8")
"@ | python -
        $injectExitCode = $LASTEXITCODE
        if ($injectExitCode -eq 0) {
            return Get-Content -LiteralPath $outputPath -Raw -Encoding UTF8
        }
        if ($injectExitCode -eq 3) {
            Write-Host "[STOP] Build blocked by incomplete dependency." -ForegroundColor Yellow
            exit 3
        }
        Write-Host "[Error] Dependency prompt injection failed." -ForegroundColor Red
        exit 1
    } finally {
        foreach ($path in @($inputPath, $outputPath)) {
            if ($path -and (Test-Path -LiteralPath $path)) {
                Remove-Item -LiteralPath $path -Force -ErrorAction SilentlyContinue
            }
        }
    }
}

$planPath = Join-Path $runPath "plan.md"

if (-not [string]::IsNullOrWhiteSpace($PromptFile)) {
    # Custom prompt file
    if (-not (Test-Path -LiteralPath $PromptFile)) {
        Write-Host "[Error] PromptFile not found: $PromptFile" -ForegroundColor Red
        exit 1
    }
    $assembledPrompt = Get-Content -LiteralPath $PromptFile -Raw -Encoding UTF8
    Write-Host "[APSF] prompt:    $PromptFile (custom)" -ForegroundColor Cyan
} else {
    # ── Context passing policy ────────────────────────────────────────────
    # 参照渡し (Builder が Read ツールで直接読む):
    #   plan.md        — メインの build 指示。内容をここに埋め込まない。
    # 埋め込み (プロンプト文字列に含める):
    #   builder.md     — ロールガイダンス。ツールで読めないシステムプロンプト相当。
    #   build_review.md — 再ビルド修正指示。Builder が着手前に内容を知る必要がある。
    # ─────────────────────────────────────────────────────────────────────

    # plan.md の存在だけ確認する（内容は Builder が Read ツールで直接読む）
    $planPath = Join-Path $runPath "plan.md"
    if (-not (Test-Path -LiteralPath $planPath)) {
        Write-Host "[Error] plan.md not found at: $planPath" -ForegroundColor Red
        Write-Host "  plan.md is required before BUILD_NEEDED." -ForegroundColor DarkGray
        exit 1
    }

    $buildReviewContent = Read-RunFile "build_review.md"
    $hasBuildReview = $null -ne $buildReviewContent -and -not [string]::IsNullOrWhiteSpace($buildReviewContent)

    # Read builder system prompt
    $builderMdPath = Join-Path (Split-Path $PSScriptRoot -Parent) "framework\agents\builder.md"
    $builderGuidance = if (Test-Path -LiteralPath $builderMdPath) {
        Get-Content -LiteralPath $builderMdPath -Raw -Encoding UTF8
    } else {
        "You are a Builder agent. Read plan.md, implement the required changes to real files, and record your decisions in build.md."
    }

    $assembledPrompt = @"
## Builder Role Guidance

$builderGuidance

---

## Builder Specialist

$(if (-not [string]::IsNullOrWhiteSpace($specialistContent)) { $specialistContent } else { "(none — generic Builder)" })

---

## Run

$Run

Run directory: $runPath

---

## Task

**Step 1 — Read plan.md.**
Use the Read tool to open ``plan.md`` in the run directory above.
If the file does not exist or cannot be read, stop and report the error. Do not proceed.

**Step 2 — Confirm read (required output).**
After reading, output exactly this line:
  plan.md has been read

Then immediately output a 2-3 line summary of the build objective:
  Summary: <what is being built, key constraints, expected output>

Do not begin any file edits until this output is complete.

**Step 3 — Execute the build.**
Implement the changes described in ``plan.md``.
Write all output files directly to disk using your tools.
Record your decisions and deviations in ``build.md``.
``build.md`` is required for APSF phase advancement.
Do not create a timestamped substitute such as ``build_rerun_YYYYMMDD_HHMMSS.md`` instead of ``build.md``.
"@

    if ($hasBuildReview) {
        $assembledPrompt += @"

---

## Re-build Feedback (build_review.md)

The following feedback was recorded after the previous build attempt.
Address these issues before proceeding.

$buildReviewContent
"@
    }

    $inputsLabel = "plan.md (via Read tool)"
    if ($hasBuildReview)       { $inputsLabel += " + build_review.md" }
    if ($specialistContent)    { $inputsLabel += " + specialist=$specialistCode" }
    Write-Host "[APSF] inputs:    $inputsLabel" -ForegroundColor Cyan
}

$assembledPrompt = Inject-DependencyPromptContext -ProjectRoot $projectRoot -RunDir $runPath -PromptText $assembledPrompt

function Get-MeaningfulOutputTail {
    param(
        [string]$Text,
        [int]$MaxLines = 12,
        [int]$MaxChars = 1400
    )

    if ([string]::IsNullOrWhiteSpace($Text)) {
        return $null
    }

    $lines = @(
        $Text -split "`r?`n" |
        ForEach-Object { $_.TrimEnd() } |
        Where-Object {
            $line = $_.Trim()
            -not [string]::IsNullOrWhiteSpace($line) -and
            $line -notmatch '^\[\d+/\d+\]' -and
            $line -notmatch '^\.\.\.still running'
        }
    )

    if ($lines.Count -eq 0) {
        return $null
    }

    $selected = if ($lines.Count -le $MaxLines) {
        $lines
    } else {
        $lines[($lines.Count - $MaxLines)..($lines.Count - 1)]
    }

    $summary = ($selected -join [Environment]::NewLine).Trim()
    if ($summary.Length -gt $MaxChars) {
        $summary = "..." + $summary.Substring($summary.Length - $MaxChars)
    }

    return $summary
}

function Get-FailureStage {
    param(
        [string]$CapturedText,
        [int]$ExitCode,
        [bool]$HitMaxTurns
    )

    if ($HitMaxTurns) {
        return "max-turns"
    }

    if ($CapturedText -match 'stage=artifact-validation' -or
        $CapturedText -match 'empty artifact content' -or
        $CapturedText -match 'incomplete artifact' -or
        $CapturedText -match 'commentary or an incomplete artifact') {
        return "artifact-validation"
    }

    if ($CapturedText -match 'permission' -or $CapturedText -match 'access is denied') {
        return "permissions"
    }

    if ($ExitCode -ne 0) {
        return "claude-run"
    }

    return "build-guard"
}

function Write-FailureSummary {
    param(
        [string]$Stage,
        [string]$CapturedText
    )

    $summary = Get-MeaningfulOutputTail -Text $CapturedText
    Write-Host "[DETAIL] stage=$Stage" -ForegroundColor DarkYellow
    if ([string]::IsNullOrWhiteSpace($summary)) {
        Write-Host "         No Claude output was captured." -ForegroundColor DarkGray
        return
    }

    Write-Host "         Last meaningful output:" -ForegroundColor DarkGray
    foreach ($line in ($summary -split "`r?`n")) {
        Write-Host ("         " + $line) -ForegroundColor DarkGray
    }
}

function Promote-LatestBuildRerunArtifact {
    param(
        [string]$RunDir,
        [datetime]$NotBeforeUtc
    )

    $buildMdPath = Join-Path $RunDir "build.md"
    if (Test-Path -LiteralPath $buildMdPath) {
        return $false
    }

    $latestRerun = Get-ChildItem -LiteralPath $RunDir -Filter "build_rerun_*.md" -File |
        Where-Object { $_.LastWriteTimeUtc -ge $NotBeforeUtc } |
        Sort-Object LastWriteTimeUtc -Descending |
        Select-Object -First 1

    if ($null -eq $latestRerun) {
        return $false
    }

    Copy-Item -LiteralPath $latestRerun.FullName -Destination $buildMdPath -Force
    Write-Host "[APSF] canonicalized: promoted $($latestRerun.Name) -> build.md" -ForegroundColor DarkGray
    return $true
}

function Get-HumanBlockerInfo {
    param([string]$RunDir)

    $payload = @"
import json
import sys
from pathlib import Path
from apsf.legacy.orchestration.rebuild_feedback import get_build_gate_decision

sys.stdout.reconfigure(encoding="utf-8")

run_dir = Path(r"$RunDir")
print(json.dumps(get_build_gate_decision(run_dir), ensure_ascii=False))
"@ | python -

    if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($payload)) {
        return $null
    }
    return $payload.Trim()
}

Write-Host ""

# ── Dry run ───────────────────────────────────────────────────────────────

if ($DryRun) {
    Write-Host "[DryRun] Assembled prompt ($($assembledPrompt.Length) chars):" -ForegroundColor Yellow
    Write-Host "─" * 60 -ForegroundColor DarkGray
    Write-Host $assembledPrompt.Substring(0, [Math]::Min(2000, $assembledPrompt.Length))
    if ($assembledPrompt.Length -gt 2000) {
        Write-Host "... [truncated, $($assembledPrompt.Length) total chars]" -ForegroundColor DarkGray
    }
    Write-Host "─" * 60 -ForegroundColor DarkGray
    Write-Host ""
    Write-Host "[DryRun] Would invoke: claude -p --tools '$Tools' --permission-mode bypassPermissions --max-turns $MaxTurns" -ForegroundColor Yellow
    Write-Host "[DryRun] No files written. Remove -DryRun to execute." -ForegroundColor DarkGray
    exit 0
}

# ── Invoke claude with tool access ────────────────────────────────────────

Write-Host "[1/2] Invoking claude (tool-enabled, max-turns=$MaxTurns)..." -ForegroundColor DarkGray
Write-Host "      Tools: $Tools" -ForegroundColor DarkGray
Write-Host "      permissions: bypassPermissions" -ForegroundColor DarkGray
Write-Host "      (Builder will write files directly — no stdout capture)" -ForegroundColor DarkGray
Write-Host ""

$humanBlockerJson = Get-HumanBlockerInfo -RunDir $runPath
if (-not [string]::IsNullOrWhiteSpace($humanBlockerJson)) {
    $humanBlocker = $humanBlockerJson | ConvertFrom-Json
    $gateStatus = [string]$humanBlocker.status
    if ($gateStatus -eq "HUMAN") {
        Write-Host "[STOP] Human-owned blocker detected before build." -ForegroundColor Yellow
        Write-Host ("       source: {0}" -f $humanBlocker.source) -ForegroundColor DarkGray
        Write-Host ("       {0}" -f $humanBlocker.summary) -ForegroundColor DarkGray
        foreach ($action in @($humanBlocker.actions)) {
            Write-Host ("       human action: {0}" -f $action) -ForegroundColor DarkGray
        }
        Write-Host ""
        Write-Host "       Builder rerun skipped to avoid a no-op rebuild." -ForegroundColor DarkGray
        exit 3
    }
    if ($gateStatus -in @("UNRECORDED", "CORRUPT")) {
        Write-Host "[STOP] Canonical blocker ownership is invalid for build gating." -ForegroundColor Yellow
        Write-Host ("       status: {0}" -f $gateStatus) -ForegroundColor DarkGray
        Write-Host ("       source: {0}" -f $humanBlocker.source) -ForegroundColor DarkGray
        if (-not [string]::IsNullOrWhiteSpace([string]$humanBlocker.summary)) {
            Write-Host ("       {0}" -f $humanBlocker.summary) -ForegroundColor DarkGray
        }
        if (-not [string]::IsNullOrWhiteSpace([string]$humanBlocker.detail)) {
            Write-Host ("       detail: {0}" -f $humanBlocker.detail) -ForegroundColor DarkGray
        }
        Write-Host ""
        Write-Host "       Build gate failed closed. Record or repair transition_outcome.json before rerunning Builder." -ForegroundColor DarkGray
        exit 4
    }
    if ($gateStatus -eq "SUPERSEDED") {
        Write-Host "[Gate] Canonical blocker ownership is SUPERSEDED for the current phase; proceeding." -ForegroundColor DarkGray
        if (-not [string]::IsNullOrWhiteSpace([string]$humanBlocker.detail)) {
            Write-Host ("       detail: {0}" -f $humanBlocker.detail) -ForegroundColor DarkGray
        }
        Write-Host ""
    }
}

$claudeCmd = Get-Command "claude" -ErrorAction Stop
$claudePath = $claudeCmd.Source

$claudeArgs = @(
    '-p',
    '--tools', $Tools,
    '--permission-mode', 'bypassPermissions',
    '--output-format', 'text',
    '--no-session-persistence',
    '--max-turns', [string]$MaxTurns,
    '--disable-slash-commands'
)
if (-not [string]::IsNullOrWhiteSpace($assignmentModel)) {
    $claudeArgs += @('--model', $assignmentModel)
    Write-Host "      model override: $assignmentModel" -ForegroundColor DarkGray
}

try {
    $buildStartUtc = [datetime]::UtcNow
    $claudeOutput = $assembledPrompt | & $claudePath @claudeArgs 2>&1 | Tee-Object -Variable _claudeCaptured
    $exitCode = $LASTEXITCODE
} catch {
    $exceptionText = ($_ | Out-String).Trim()
    Write-Host "[FAILURE] stage=invoke-exception exit=1" -ForegroundColor Red
    Write-FailureSummary -Stage "invoke-exception" -CapturedText $exceptionText
    exit 1
}

$claudeText = @($claudeOutput) -join [Environment]::NewLine
$hitMaxTurns = $claudeText -match 'Error:\s*Reached max turns'

# ── Success / Phase transition check ─────────────────────────────────────

$null = Promote-LatestBuildRerunArtifact -RunDir $runPath -NotBeforeUtc $buildStartUtc
$postBuildPhase = (apsf next $Run --phase-only).Trim()
$phaseAdvanced = ($postBuildPhase -ne "BUILD_NEEDED") -and ($postBuildPhase -ne "UNKNOWN")

Write-Host ""
if ($exitCode -eq 0 -and -not $hitMaxTurns) {
    if ($phaseAdvanced) {
        Write-Host "[SUCCESS] Build complete and phase advanced to: $postBuildPhase" -ForegroundColor Green
        Write-Host ""
        Write-Host "[Done] Run is ready for the next stage." -ForegroundColor Green
        Write-Host "       Execute: apsf next $Run" -ForegroundColor DarkGray
        exit 0
    } else {
        $stage = Get-FailureStage -CapturedText $claudeText -ExitCode $exitCode -HitMaxTurns $false
        Write-Host "[PARTIAL] Claude claimed success, but the phase is still BUILD_NEEDED." -ForegroundColor Yellow
        Write-Host "          Possible cause: build.md is missing or unfilled." -ForegroundColor DarkGray
        Write-Host "          (Build Guard: Success requires verifiable phase advancement)" -ForegroundColor DarkGray
        Write-FailureSummary -Stage $stage -CapturedText $claudeText
        Write-Host ""
        Write-Host "          Next: Check build.md and ensure all required artifacts exist." -ForegroundColor DarkGray
        exit 2
    }
} else {
    if ($hitMaxTurns) {
        $stage = Get-FailureStage -CapturedText $claudeText -ExitCode $exitCode -HitMaxTurns $true
        Write-Host "[PARTIAL] Reached max turns before completing the build." -ForegroundColor Red
        Write-Host "          Phase remains: $postBuildPhase" -ForegroundColor DarkGray
        Write-Host "          Increase -MaxTurns or finish the remaining work manually." -ForegroundColor DarkGray
        Write-FailureSummary -Stage $stage -CapturedText $claudeText
        exit 2
    }
    $stage = Get-FailureStage -CapturedText $claudeText -ExitCode $exitCode -HitMaxTurns $false
    Write-Host "[FAILURE] stage=$stage exit=$exitCode" -ForegroundColor Red
    Write-Host "          Phase remains: $postBuildPhase" -ForegroundColor DarkGray
    Write-FailureSummary -Stage $stage -CapturedText $claudeText
    exit 1
}
