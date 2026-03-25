<#
.SYNOPSIS
    Reset a run back to PLAN_NEEDED while preserving downstream artifacts.

.DESCRIPTION
    Moves existing plan/build/review-side artifacts to timestamped backup names,
    optionally creates a `plan_review.md` scaffold for planner feedback,
    then shows the next APSF phase so the run can be planned again.
#>

param(
    [Parameter(Mandatory = $true, Position = 0)]
    [string]$Run,

    [switch]$SkipPlanReviewScaffold
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Resolve-RunDir {
    param([string]$TargetRun)

    $runsRoot = Join-Path (Split-Path $PSScriptRoot -Parent) "runs"
    $dir = Get-ChildItem -Path $runsRoot -Recurse -Directory -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -eq $TargetRun } |
        Select-Object -First 1

    if ($null -eq $dir) {
        throw "Run directory not found: $TargetRun"
    }

    return $dir.FullName
}

function Backup-Artifact {
    param(
        [string]$RunDir,
        [string]$FileName,
        [string]$Suffix
    )

    $path = Join-Path $RunDir $FileName
    if (-not (Test-Path -LiteralPath $path)) {
        return
    }

    $stem = [System.IO.Path]::GetFileNameWithoutExtension($FileName)
    $ext = [System.IO.Path]::GetExtension($FileName)
    $backup = Join-Path $RunDir ("{0}_{1}{2}" -f $stem, $Suffix, $ext)
    Move-Item -LiteralPath $path -Destination $backup -Force
    Write-Host ("  backed up {0} -> {1}" -f $FileName, [System.IO.Path]::GetFileName($backup)) -ForegroundColor DarkGray
}

function Ensure-PlanReviewScaffold {
    param([string]$RunDir)

    $path = Join-Path $RunDir "plan_review.md"
    if (Test-Path -LiteralPath $path) {
        Write-Host "  kept existing plan_review.md" -ForegroundColor DarkGray
        return
    }

    $content = @'
# Plan Review

---

## Purpose

Feedback for revising `plan.md` before the Planner rewrites it.
This is a supporting note, not a canonical APSF phase artifact.

---

## Summary

- 

---

## Requested Revisions

1. 
2. 
3. 

---

## Findings

### Critical

- None

### Major

- 

### Minor

- 

---

## Notes To Planner

- Clarify the build boundary for this run.
- State what should happen in this run versus a follow-up run.
- Make any transition criteria explicit if the selected approach is staged.
'@

    Set-Content -LiteralPath $path -Value $content -Encoding UTF8
    Write-Host "  created plan_review.md scaffold" -ForegroundColor DarkGray
}

$runDir = Resolve-RunDir -TargetRun $Run
$suffix = "rerun_" + (Get-Date -Format "yyyyMMdd_HHmmss")

Write-Host ""
Write-Host "[APSF] rerun plan:   $Run" -ForegroundColor Cyan
Write-Host "[APSF] run dir:      $runDir" -ForegroundColor Cyan
Write-Host ""

Backup-Artifact -RunDir $runDir -FileName "plan.md" -Suffix $suffix
Backup-Artifact -RunDir $runDir -FileName "handoff.md" -Suffix $suffix
Backup-Artifact -RunDir $runDir -FileName "build.md" -Suffix $suffix
Backup-Artifact -RunDir $runDir -FileName "review.md" -Suffix $suffix
Backup-Artifact -RunDir $runDir -FileName "improve.md" -Suffix $suffix
Backup-Artifact -RunDir $runDir -FileName "result.md" -Suffix $suffix

if (-not $SkipPlanReviewScaffold) {
    Ensure-PlanReviewScaffold -RunDir $runDir
}

Write-Host ""
Write-Host "[APSF] next after reset:" -ForegroundColor Cyan
apsf next $Run

Write-Host ""
Write-Host "[Tip] Fill plan_review.md, then re-run Planner with:" -ForegroundColor Green
Write-Host ("       .\scripts\apsf-claude-act.ps1 {0}" -f $Run) -ForegroundColor DarkGray
