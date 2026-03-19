<#
.SYNOPSIS
    APSF x claude -p pipe execution wrapper

.DESCRIPTION
    Runs: apsf act <run> --print-prompt | claude -p | apsf write-phase <run> --stdin

    Shows pre-execution summary, stage progress, and failure location.
    Sets UTF-8 encoding to prevent mojibake on PowerShell 5.1.
    Recommended: run with pwsh (PowerShell 7+) where UTF-8 is the default.

.PARAMETER Run
    Target run name (e.g. 2026-03-18_my-case_my-topic)

.PARAMETER DryRun
    Show what would be executed without saving

.PARAMETER UntilPlan
    Chain mode: auto-generate execution-assignment.md (if needed) then plan.md.
    Stops at GOAL_NEEDED (goal.md is always Human-owned).
    Skips execution-assignment.md generation if already filled (use -Force to overwrite).

.PARAMETER Force
    Overwrite existing content (applies to -UntilPlan Step 1 only).

.EXAMPLE
    # Execute one phase (repeat for Plan -> Build -> Review)
    .\scripts\apsf-claude-act.ps1 2026-03-18_my-case_my-topic

.EXAMPLE
    # Preview only (no save)
    .\scripts\apsf-claude-act.ps1 2026-03-18_my-case_my-topic -DryRun

.EXAMPLE
    # Chain: auto-generate execution-assignment.md then plan.md
    .\scripts\apsf-claude-act.ps1 2026-03-18_my-case_my-topic -UntilPlan

.EXAMPLE
    # Chain dry-run: show what would be executed without saving
    .\scripts\apsf-claude-act.ps1 2026-03-18_my-case_my-topic -UntilPlan -DryRun

.EXAMPLE
    # Chain with overwrite (re-generate execution-assignment.md even if filled)
    .\scripts\apsf-claude-act.ps1 2026-03-18_my-case_my-topic -UntilPlan -Force
#>

param(
    [Parameter(Mandatory = $true, Position = 0)]
    [string]$Run,

    [switch]$DryRun,

    # Chain mode: auto-run SETUP_NEEDED then PLAN_NEEDED in sequence
    [switch]$UntilPlan,

    # Overwrite execution-assignment.md even if already filled (UntilPlan Step 1 only)
    [switch]$Force
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# UTF-8 setup (required for PS 5.1 pipe encoding; harmless on pwsh 7+)
$OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# Prerequisite checks
if (-not (Get-Command "apsf" -ErrorAction SilentlyContinue)) {
    Write-Host "[Error] 'apsf' not found. Run: pip install -e ." -ForegroundColor Red
    exit 1
}
if (-not (Get-Command "claude" -ErrorAction SilentlyContinue)) {
    Write-Host "[Error] 'claude' not found. Install Claude Code CLI." -ForegroundColor Red
    exit 1
}

# ============================================================
# -UntilPlan: chain mode (SETUP_NEEDED -> PLAN_NEEDED)
# ============================================================
if ($UntilPlan) {

    # -- Get current phase --
    $nextLines = apsf next $Run 2>&1
    $phaseMatch = $nextLines | Select-String -Pattern "Phase\s*:\s*(\S+)"
    $phase = if ($phaseMatch) { $phaseMatch.Matches[0].Groups[1].Value } else { "UNKNOWN" }

    # -- GOAL_NEEDED: always Human-owned, cannot be automated --
    if ($phase -eq "GOAL_NEEDED") {
        Write-Host "[Stop] goal.md must be filled by Human before chaining." -ForegroundColor Yellow
        Write-Host "       target: runs/$Run/goal.md" -ForegroundColor DarkGray
        Write-Host "       check:  apsf next $Run"    -ForegroundColor DarkGray
        exit 0
    }

    # -- DryRun: show chain plan and exit --
    if ($DryRun) {
        Write-Host ""
        Write-Host "[DryRun] Chain mode: -UntilPlan"   -ForegroundColor Yellow
        Write-Host "  Step 1: apsf generate-setup $Run  ->  execution-assignment.md  [auto]" -ForegroundColor Yellow
        Write-Host "  Step 2: apsf act $Run             ->  plan.md                  [auto]" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "  Prerequisite : goal.md must be filled (Human-owned, cannot be automated)" -ForegroundColor DarkGray
        Write-Host "  Overwrite    : If execution-assignment.md already has content, Step 1 is skipped." -ForegroundColor DarkGray
        Write-Host "                 Use -Force to overwrite." -ForegroundColor DarkGray
        Write-Host ""
        Write-Host "[DryRun] No file saved. Remove -DryRun to execute." -ForegroundColor DarkGray
        exit 0
    }

    Write-Host ""
    Write-Host "[APSF] run:        $Run"          -ForegroundColor Cyan
    Write-Host "[APSF] mode:       -UntilPlan"    -ForegroundColor Cyan
    Write-Host "[APSF] cur phase:  $phase"         -ForegroundColor Cyan
    Write-Host ""

    # ---- Step 1: generate execution-assignment.md (if SETUP_NEEDED) ----
    if ($phase -eq "SETUP_NEEDED") {
        Write-Host "[Step 1/2] generate-setup..." -ForegroundColor Cyan

        $generateSetupArgs = @($Run, "--print-prompt")
        if ($Force) { $generateSetupArgs += "--force" }

        # [1/3] generate setup prompt
        Write-Host "  [1/3] generate setup prompt..." -ForegroundColor DarkGray
        $setupPrompt = & apsf generate-setup @generateSetupArgs 2>$null
        if ($LASTEXITCODE -ne 0) {
            Write-Host "[FAIL] stage=generate-setup-prompt exit=$LASTEXITCODE" -ForegroundColor Red
            exit $LASTEXITCODE
        }
        if ([string]::IsNullOrWhiteSpace($setupPrompt)) {
            Write-Host "[Stop] apsf generate-setup returned empty output. Check phase:" -ForegroundColor Yellow
            Write-Host "       apsf next $Run" -ForegroundColor DarkGray
            exit 0
        }

        # [2/3] invoke claude -p
        Write-Host "  [2/3] invoke claude -p..." -ForegroundColor DarkGray
        $setupOutput = $setupPrompt | claude -p
        if ($LASTEXITCODE -ne 0) {
            Write-Host "[FAIL] stage=claude-p (setup) exit=$LASTEXITCODE" -ForegroundColor Red
            exit $LASTEXITCODE
        }

        # [3/3] write execution-assignment.md
        Write-Host "  [3/3] write execution-assignment.md..." -ForegroundColor DarkGray
        $setupOutput | apsf write-phase $Run --stdin
        if ($LASTEXITCODE -ne 0) {
            Write-Host "[FAIL] stage=write-phase (execution-assignment.md) exit=$LASTEXITCODE" -ForegroundColor Red
            exit $LASTEXITCODE
        }

        Write-Host "[Done] execution-assignment.md saved." -ForegroundColor Green
        Write-Host ""

    } else {
        # execution-assignment.md is already filled -- skip Step 1
        Write-Host "[Step 1/2] skipped: execution-assignment.md already filled (phase=$phase)" -ForegroundColor DarkGray
        Write-Host ""
    }

    # ---- Step 2: generate plan.md ----
    Write-Host "[Step 2/2] generate plan.md..." -ForegroundColor Cyan

    # Re-check phase after Step 1
    $nextLines2 = apsf next $Run 2>&1
    $phaseMatch2 = $nextLines2 | Select-String -Pattern "Phase\s*:\s*(\S+)"
    $phase2 = if ($phaseMatch2) { $phaseMatch2.Matches[0].Groups[1].Value } else { "UNKNOWN" }

    if ($phase2 -ne "PLAN_NEEDED") {
        Write-Host "[Stop] Expected PLAN_NEEDED but got: $phase2" -ForegroundColor Yellow
        Write-Host "       Check run state: apsf next $Run" -ForegroundColor DarkGray
        exit 0
    }

    # [1/3] generate plan prompt
    Write-Host "  [1/3] generate plan prompt..." -ForegroundColor DarkGray
    $planPrompt = apsf act $Run --print-prompt 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[FAIL] stage=generate-plan-prompt exit=$LASTEXITCODE" -ForegroundColor Red
        exit $LASTEXITCODE
    }
    if ([string]::IsNullOrWhiteSpace($planPrompt)) {
        Write-Host "[Stop] apsf act returned empty output. Check phase:" -ForegroundColor Yellow
        Write-Host "       apsf next $Run" -ForegroundColor DarkGray
        exit 0
    }

    # [2/3] invoke claude -p
    Write-Host "  [2/3] invoke claude -p..." -ForegroundColor DarkGray
    $planOutput = $planPrompt | claude -p
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[FAIL] stage=claude-p (plan) exit=$LASTEXITCODE" -ForegroundColor Red
        exit $LASTEXITCODE
    }

    # [3/3] write plan.md
    Write-Host "  [3/3] write plan.md..." -ForegroundColor DarkGray
    $planOutput | apsf write-phase $Run --stdin
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[FAIL] stage=write-phase (plan.md) exit=$LASTEXITCODE" -ForegroundColor Red
        exit $LASTEXITCODE
    }

    Write-Host ""
    Write-Host "[Done] plan.md saved. Next: apsf next $Run" -ForegroundColor Green
    Write-Host "[Note] Record any friction in fw-improvement-memo.md"  -ForegroundColor DarkGray
    exit 0
}

# ============================================================
# Default: single-phase execution (existing behavior)
# ============================================================

# Get phase info from apsf next
$nextLines = apsf next $Run 2>&1

$phaseMatch = $nextLines | Select-String -Pattern "Phase\s*:\s*(\S+)"
$writeMatch = $nextLines | Select-String -Pattern "Write\s*:\s*(\S+\.md)"
$humanStop  = $nextLines | Select-String -Pattern "Next Role\s*:.*Human"

$phase      = if ($phaseMatch) { $phaseMatch.Matches[0].Groups[1].Value } else { "UNKNOWN" }
$targetFile = if ($writeMatch) { $writeMatch.Matches[0].Groups[1].Value } else { "unknown" }
$isHuman    = $null -ne $humanStop

# Resolve runs directory (APSF_ROOT env var or CWD)
$runsBase   = if ($env:APSF_ROOT) { Join-Path $env:APSF_ROOT "runs" } else { ".\runs" }
$targetPath = Join-Path $runsBase "$Run\$targetFile"

# Pre-execution summary
Write-Host ""
Write-Host "[APSF] run:         $Run"        -ForegroundColor Cyan
Write-Host "[APSF] next phase:  $phase"      -ForegroundColor Cyan
Write-Host "[APSF] target file: $targetFile" -ForegroundColor Cyan
if ($isHuman) {
    Write-Host "[APSF] human stop:  true  (human-owned phase, no auto-exec)" -ForegroundColor Yellow
} else {
    Write-Host "[APSF] human stop:  false" -ForegroundColor Cyan
}
Write-Host ""

# Stop for human-owned phases
if ($isHuman) {
    Write-Host "[Stop] Human-owned phase. Edit the file directly." -ForegroundColor Yellow
    Write-Host "       target: $targetPath"      -ForegroundColor DarkGray
    Write-Host "       check:  apsf next $Run"   -ForegroundColor DarkGray
    exit 0
}

# DryRun: show plan without executing
if ($DryRun) {
    # Use apsf act --dry-run to leverage APSF core's _is_filled() threshold.
    # [Info] in output means the file already has meaningful content (filled).
    # Any other output (DRY-RUN, prompt text) means template-only or empty.
    # This avoids the coarse -match '\S' check that fires on template headers.
    $actDryOut = apsf act $Run --dry-run 2>$null
    if ($actDryOut -match "\[Info\]") {
        $overwriteRisk = "yes (meaningful content detected)"
        $riskColor     = "Yellow"
    } else {
        $overwriteRisk = "no (template only)"
        $riskColor     = "DarkGray"
    }

    Write-Host "[DryRun] source: apsf act $Run --print-prompt"  -ForegroundColor Yellow
    Write-Host "[DryRun] sink:   apsf write-phase $Run --stdin" -ForegroundColor Yellow
    Write-Host "[DryRun] target phase file: $targetFile"        -ForegroundColor Yellow
    Write-Host "[DryRun] overwrite risk: $overwriteRisk"        -ForegroundColor $riskColor
    Write-Host ""
    Write-Host "[DryRun] No file saved. Remove -DryRun to execute." -ForegroundColor DarkGray
    exit 0
}

# Stage execution

# [1/3] generate prompt
Write-Host "[1/3] generate prompt..." -ForegroundColor DarkGray
$promptText = apsf act $Run --print-prompt 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "[FAIL] stage=generate-prompt exit=$LASTEXITCODE" -ForegroundColor Red
    exit $LASTEXITCODE
}
if ([string]::IsNullOrWhiteSpace($promptText)) {
    # Safety check: empty stdout means human phase or undetected stop
    Write-Host "[Stop] apsf act returned empty output. Check phase:" -ForegroundColor Yellow
    Write-Host "       apsf next $Run" -ForegroundColor DarkGray
    exit 0
}

# [2/3] invoke claude -p
Write-Host "[2/3] invoke claude -p..." -ForegroundColor DarkGray
$claudeOutput = $promptText | claude -p
if ($LASTEXITCODE -ne 0) {
    Write-Host "[FAIL] stage=claude-p exit=$LASTEXITCODE" -ForegroundColor Red
    exit $LASTEXITCODE
}

# [3/3] write phase
Write-Host "[3/3] write phase..." -ForegroundColor DarkGray
$claudeOutput | apsf write-phase $Run --stdin
if ($LASTEXITCODE -ne 0) {
    Write-Host "[FAIL] stage=write-phase exit=$LASTEXITCODE" -ForegroundColor Red
    exit $LASTEXITCODE
}

Write-Host ""
Write-Host "[Done] $targetFile saved. Next: apsf next $Run" -ForegroundColor Green
Write-Host "[Note] Record any friction in fw-improvement-memo.md" -ForegroundColor DarkGray
