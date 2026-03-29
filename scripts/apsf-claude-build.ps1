<#
.SYNOPSIS
    APSF Build wrapper — runs claude with file-system tool access for BUILD_NEEDED phase.

.DESCRIPTION
    Invokes: claude -p --tools <toolset> < <assembled prompt>

    Unlike apsf-claude-act.ps1 (which disables tools for PLAN/REVIEW phases),
    this script enables filesystem tool access so Builder can read, edit, and
    create real project files.

    Contract:
      - Builder writes files DIRECTLY to disk. build.md is an optional log.
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

$runsRoot = Join-Path (Split-Path $PSScriptRoot -Parent) "runs"
$runDir = Get-ChildItem -Path $runsRoot -Recurse -Directory -ErrorAction SilentlyContinue |
    Where-Object { $_.Name -eq $Run } |
    Select-Object -First 1

if ($null -eq $runDir) {
    Write-Host "[Error] Run not found: $Run" -ForegroundColor Red
    Write-Host "  Searched under: $runsRoot" -ForegroundColor DarkGray
    exit 1
}

$runPath = $runDir.FullName
Write-Host "[APSF] run:       $Run" -ForegroundColor Cyan
Write-Host "[APSF] run path:  $runPath" -ForegroundColor Cyan
Write-Host "[APSF] mode:      BUILD (tool-enabled)" -ForegroundColor Cyan

# ── Phase guard ──────────────────────────────────────────────────────────

$currentPhase = (apsf next $Run --phase-only).Trim()
Write-Host "[APSF] phase:     $currentPhase" -ForegroundColor Cyan

if ($currentPhase -ne "BUILD_NEEDED" -and $currentPhase -ne "UNKNOWN") {
    Write-Host "" 
    Write-Host "[Warn] Current phase is '$currentPhase', not BUILD_NEEDED." -ForegroundColor Yellow
    Write-Host "       This script is designed for BUILD_NEEDED only." -ForegroundColor DarkGray
    Write-Host "       For PLAN_NEEDED / REVIEW_NEEDED, use apsf-claude-act.ps1" -ForegroundColor DarkGray
    $confirm = Read-Host "Continue anyway? [y/N]"
    if ($confirm -ne "y" -and $confirm -ne "Y") {
        Write-Host "Aborted." -ForegroundColor Yellow
        exit 0
    }
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
"@

    if ($hasBuildReview) {
        $assembledPrompt += @"

---

## Re-build Feedback (build_review.md)

The following feedback was recorded after the previous build attempt.
Address these issues before proceeding.

$buildReviewContent
"@
        Write-Host "[APSF] inputs:    plan.md (via Read tool) + build_review.md" -ForegroundColor Cyan
    } else {
        Write-Host "[APSF] inputs:    plan.md (via Read tool)" -ForegroundColor Cyan
    }
}

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
    Write-Host "[DryRun] Would invoke: claude -p --tools '$Tools' --max-turns $MaxTurns" -ForegroundColor Yellow
    Write-Host "[DryRun] No files written. Remove -DryRun to execute." -ForegroundColor DarkGray
    exit 0
}

# ── Invoke claude with tool access ────────────────────────────────────────

Write-Host "[1/2] Invoking claude (tool-enabled, max-turns=$MaxTurns)..." -ForegroundColor DarkGray
Write-Host "      Tools: $Tools" -ForegroundColor DarkGray
Write-Host "      (Builder will write files directly — no stdout capture)" -ForegroundColor DarkGray
Write-Host ""

$claudeCmd = Get-Command "claude" -ErrorAction Stop
$claudePath = $claudeCmd.Source

$claudeArgs = @(
    '-p',
    '--tools', $Tools,
    '--output-format', 'text',
    '--no-session-persistence',
    '--max-turns', [string]$MaxTurns,
    '--disable-slash-commands'
)

try {
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
