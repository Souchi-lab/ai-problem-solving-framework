<#
.SYNOPSIS
    Reset a run back to IMPROVE_NEEDED while preserving later close artifacts.

.DESCRIPTION
    Moves existing improve/result/transcript artifacts to timestamped backup names,
    optionally creates an `improve_review.md` scaffold for Judge feedback,
    then shows the next APSF phase so the run can be judged again.
#>

param(
    [Parameter(Mandatory = $true, Position = 0)]
    [string]$Run,

    [switch]$SkipImproveReviewScaffold
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

function Ensure-ImproveReviewScaffold {
    param([string]$RunDir)

    $path = Join-Path $RunDir "improve_review.md"
    if (Test-Path -LiteralPath $path) {
        Write-Host "  kept existing improve_review.md" -ForegroundColor DarkGray
        return
    }

    $templatePath = Join-Path (Split-Path $PSScriptRoot -Parent) "framework\templates\improve-review.md"
    if (-not (Test-Path -LiteralPath $templatePath)) {
        throw "Template not found: $templatePath"
    }

    Copy-Item -LiteralPath $templatePath -Destination $path -Force
    Write-Host "  created improve_review.md scaffold" -ForegroundColor DarkGray
}

$runDir = Resolve-RunDir -TargetRun $Run
$suffix = "rerun_" + (Get-Date -Format "yyyyMMdd_HHmmss")

Write-Host ""
Write-Host "[APSF] rerun improve: $Run" -ForegroundColor Cyan
Write-Host "[APSF] run dir:        $runDir" -ForegroundColor Cyan
Write-Host ""

Backup-Artifact -RunDir $runDir -FileName "improve.md" -Suffix $suffix
Backup-Artifact -RunDir $runDir -FileName "result.md" -Suffix $suffix
Backup-Artifact -RunDir $runDir -FileName "transcript.md" -Suffix $suffix

if (-not $SkipImproveReviewScaffold) {
    Ensure-ImproveReviewScaffold -RunDir $runDir
}

Write-Host ""
Write-Host "[APSF] next after reset:" -ForegroundColor Cyan
apsf next $Run

Write-Host ""
Write-Host "[Tip] Fill improve_review.md if needed, then revisit Judge guidance with:" -ForegroundColor Green
Write-Host ("       apsf next {0}" -f $Run) -ForegroundColor DarkGray
