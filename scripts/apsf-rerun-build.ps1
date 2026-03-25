<#
.SYNOPSIS
    Reset a run back to BUILD_NEEDED while preserving downstream artifacts.

.DESCRIPTION
    Moves existing build/review/improve/result-side artifacts to timestamped
    backup names, optionally creates a `build_review.md` scaffold for builder feedback,
    then shows the next APSF phase so the run can be built again.
#>

param(
    [Parameter(Mandatory = $true, Position = 0)]
    [string]$Run,

    [switch]$SkipBuildReviewScaffold
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

function Ensure-BuildReviewScaffold {
    param([string]$RunDir)

    $path = Join-Path $RunDir "build_review.md"
    if (Test-Path -LiteralPath $path) {
        Write-Host "  kept existing build_review.md" -ForegroundColor DarkGray
        return
    }

    $content = @'
# Build Review

---

## Purpose

Feedback for revising `build.md` and the underlying build outputs before the Builder rebuilds them.
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

## Notes To Builder

- Keep `build.md` as a build record, not as a dump of full deliverable contents.
- Put implementation and durable artifacts in real files.
- Record verification commands and outcomes explicitly.
- Narrow the rebuild scope to the unresolved review gaps.
'@

    Set-Content -LiteralPath $path -Value $content -Encoding UTF8
    Write-Host "  created build_review.md scaffold" -ForegroundColor DarkGray
}

$runDir = Resolve-RunDir -TargetRun $Run
$suffix = "rerun_" + (Get-Date -Format "yyyyMMdd_HHmmss")

Write-Host ""
Write-Host "[APSF] rerun build:  $Run" -ForegroundColor Cyan
Write-Host "[APSF] run dir:      $runDir" -ForegroundColor Cyan
Write-Host ""

Backup-Artifact -RunDir $runDir -FileName "build.md" -Suffix $suffix
Backup-Artifact -RunDir $runDir -FileName "handoff.md" -Suffix $suffix
Backup-Artifact -RunDir $runDir -FileName "review.md" -Suffix $suffix
Backup-Artifact -RunDir $runDir -FileName "improve.md" -Suffix $suffix
Backup-Artifact -RunDir $runDir -FileName "result.md" -Suffix $suffix

if (-not $SkipBuildReviewScaffold) {
    Ensure-BuildReviewScaffold -RunDir $runDir
}

Write-Host ""
Write-Host "[APSF] next after reset:" -ForegroundColor Cyan
apsf next $Run

Write-Host ""
Write-Host "[Tip] Fill build_review.md if needed, then re-run Builder with:" -ForegroundColor Green
Write-Host ("       .\scripts\apsf-claude-act.ps1 {0}" -f $Run) -ForegroundColor DarkGray
