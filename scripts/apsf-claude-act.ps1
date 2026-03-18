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

.EXAMPLE
    # Execute one phase (repeat for Plan -> Build -> Review)
    .\scripts\apsf-claude-act.ps1 2026-03-18_my-case_my-topic

.EXAMPLE
    # Preview only (no save)
    .\scripts\apsf-claude-act.ps1 2026-03-18_my-case_my-topic -DryRun
#>

param(
    [Parameter(Mandatory = $true, Position = 0)]
    [string]$Run,

    [switch]$DryRun
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

# Get phase info from apsf next
$nextLines = apsf next $Run 2>&1

$phaseMatch = $nextLines | Select-String -Pattern "Phase\s*:\s*(\S+)"
$writeMatch = $nextLines | Select-String -Pattern "Write\s*:\s*(\S+\.md)"
$humanStop  = $nextLines | Select-String -Pattern "\(Human\)"

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
    $hasContent    = (Test-Path $targetPath) -and ((Get-Content $targetPath -Raw -ErrorAction SilentlyContinue) -match '\S')
    if ($hasContent) {
        $overwriteRisk = "yes  (existing content detected in $targetFile)"
        $riskColor     = "Yellow"
    } else {
        $overwriteRisk = "no"
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
