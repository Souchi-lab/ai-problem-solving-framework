<#
.SYNOPSIS
    Reset a run back to REVIEW_NEEDED while preserving prior review artifacts.

.DESCRIPTION
    Moves existing review/improve/result files to timestamped backup names,
    then shows the next APSF phase so the run can be reviewed again.
#>

param(
    [Parameter(Mandatory = $true, Position = 0)]
    [string]$Run,

    [switch]$SkipReviewReviewScaffold
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

function Resolve-RunDir {
    param([string]$TargetRun)

    $runsRoot = Join-Path (Split-Path $PSScriptRoot -Parent) "runs"
    $normalizedRun = $TargetRun -replace '/', '\'
    $segments = $normalizedRun.Split('\', [System.StringSplitOptions]::RemoveEmptyEntries)

    if ($segments.Length -ge 2 -and @("work", "fw-improvement") -contains $segments[0]) {
        $taxonomyPath = Join-Path $runsRoot $normalizedRun
        if (Test-Path -LiteralPath $taxonomyPath -PathType Container) {
            return (Resolve-Path -LiteralPath $taxonomyPath).Path
        }
    }

    $legacyPath = Join-Path $runsRoot $normalizedRun
    if (Test-Path -LiteralPath $legacyPath -PathType Container) {
        return (Resolve-Path -LiteralPath $legacyPath).Path
    }

    if ($segments.Length -eq 2) {
        foreach ($taxonomy in @("fw-improvement", "work")) {
            $candidate = Join-Path (Join-Path $runsRoot $taxonomy) $normalizedRun
            if (Test-Path -LiteralPath $candidate -PathType Container) {
                return (Resolve-Path -LiteralPath $candidate).Path
            }
        }
    }

    if ($segments.Length -eq 1) {
        foreach ($taxonomy in @("fw-improvement", "work")) {
            $candidate = Join-Path (Join-Path $runsRoot $taxonomy) $segments[0]
            if (Test-Path -LiteralPath $candidate -PathType Container) {
                return (Resolve-Path -LiteralPath $candidate).Path
            }
        }

        if ($segments[0] -match '^\d{3}c\d+_[a-z0-9-]+_.+$') {
            foreach ($taxonomy in @("fw-improvement", "work")) {
                $taxonomyDir = Join-Path $runsRoot $taxonomy
                if (-not (Test-Path -LiteralPath $taxonomyDir -PathType Container)) {
                    continue
                }
                $candidate = Get-ChildItem -LiteralPath $taxonomyDir -Directory -ErrorAction SilentlyContinue |
                    ForEach-Object { Join-Path $_.FullName $segments[0] } |
                    Where-Object { Test-Path -LiteralPath $_ -PathType Container } |
                    Select-Object -First 1
                if ($null -ne $candidate) {
                    return (Resolve-Path -LiteralPath $candidate).Path
                }
            }
        }
    }

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

function Ensure-ReviewReviewScaffold {
    param([string]$RunDir)

    $path = Join-Path $RunDir "review_review.md"
    if (Test-Path -LiteralPath $path) {
        Write-Host "  kept existing review_review.md" -ForegroundColor DarkGray
        return
    }

    $templatePath = Join-Path (Split-Path $PSScriptRoot -Parent) "framework\templates\review-review.md"
    if (-not (Test-Path -LiteralPath $templatePath)) {
        throw "Template not found: $templatePath"
    }

    Copy-Item -LiteralPath $templatePath -Destination $path -Force
    Write-Host "  created review_review.md scaffold" -ForegroundColor DarkGray
}

function Show-AdvisoryNextPhase {
    param(
        [string]$ProjectRoot,
        [string]$RunDir,
        [string]$Run
    )

    $advisory = @"
import sys
from pathlib import Path
from apsf.legacy.orchestration.phase_detector import PhaseDetector
from apsf.legacy.orchestration.next_instruction_builder import NextInstructionBuilder

sys.stdout.reconfigure(encoding="utf-8")

run_dir = Path(r"$RunDir")
run_name = r"$Run"
info = PhaseDetector(run_dir).detect_advisory()
instruction = NextInstructionBuilder().build(info, run_name)

print("=" * 60)
print(f"Run   : {run_name}")
print(f"Phase : {info.phase.value}  [advisory]")
print("=" * 60)
print("")
print(f"Next Role : {instruction.next_role}")
print(f"Write     : {instruction.target_file}")
if info.files_to_read:
    print(f"Read      : {', '.join(info.files_to_read)}")
if info.handoff_hint:
    print(f"Handoff   : {info.handoff_hint}")
print("")
print(f"[{instruction.short_instruction}]")
print("")
print("For full AI-ready instructions:")
print(f"  apsf write-phase {run_name} --print-prompt")
print("=" * 60)
"@ | python -

    if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($advisory)) {
        Write-Host "[Warn] Could not render advisory next phase." -ForegroundColor Yellow
        Write-Host ("       Check manually: apsf next {0}" -f $Run) -ForegroundColor DarkGray
        return
    }

    Write-Host $advisory.TrimEnd()
}

function Reset-RunStateToReviewNeeded {
    param(
        [string]$RunDir,
        [string]$Run
    )

    $result = @"
import sys
from pathlib import Path

from apsf.core.manifest.manifest_repository import ManifestRepository
from apsf.core.state.transition_service import TransitionService

sys.stdout.reconfigure(encoding="utf-8")

run_dir = Path(r"$RunDir")
run_name = r"$Run"
TransitionService().transition(
    run_dir,
    to_phase="REVIEW_NEEDED",
    actor="rerun",
    reason="apsf-rerun-review: reset to REVIEW_NEEDED",
)
ManifestRepository(run_dir).remove_entries(["review.md", "improve.md", "result.md"])
print("REVIEW_NEEDED")
"@ | python -

    if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($result)) {
        throw "Failed to reset run_state.json to REVIEW_NEEDED."
    }
}

$runDir = Resolve-RunDir -TargetRun $Run
$suffix = "rerun_" + (Get-Date -Format "yyyyMMdd_HHmmss")

Write-Host ""
Write-Host "[APSF] rerun review: $Run" -ForegroundColor Cyan
Write-Host "[APSF] run dir:       $runDir" -ForegroundColor Cyan
Write-Host ""

Backup-Artifact -RunDir $runDir -FileName "review.md" -Suffix $suffix
Backup-Artifact -RunDir $runDir -FileName "improve.md" -Suffix $suffix
Backup-Artifact -RunDir $runDir -FileName "result.md" -Suffix $suffix

if (-not $SkipReviewReviewScaffold) {
    Ensure-ReviewReviewScaffold -RunDir $runDir
}

Reset-RunStateToReviewNeeded -RunDir $runDir -Run $Run

Write-Host ""
Write-Host "[APSF] next after reset:" -ForegroundColor Cyan
Show-AdvisoryNextPhase -ProjectRoot (Split-Path $PSScriptRoot -Parent) -RunDir $runDir -Run $Run

Write-Host ""
Write-Host "[Tip] Re-run Critic with:" -ForegroundColor Green
Write-Host ("       .\scripts\apsf-claude-act.ps1 {0}" -f $Run) -ForegroundColor DarkGray
