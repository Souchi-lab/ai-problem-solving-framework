<#
.SYNOPSIS
    APSF Review wrapper for Codex CLI.

.DESCRIPTION
    Runs Codex in a bounded bridge mode for REVIEW_NEEDED.
    Contract:
      - APSF resolves run/phase/prompt.
      - Codex writes the review artifact directly or returns review.md content.
      - Phase advancement authority remains with APSF / write-phase.
#>

param(
    [Parameter(Mandatory = $true, Position = 0)]
    [string]$Run,

    [switch]$DryRun,
    [switch]$Force,
    [switch]$VerboseOutput
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

if (-not (Get-Command "apsf" -ErrorAction SilentlyContinue)) {
    Write-Host "[Error] 'apsf' not found. Run: pip install -e ." -ForegroundColor Red
    exit 1
}
if (-not (Get-Command "codex.cmd" -ErrorAction SilentlyContinue)) {
    Write-Host "[Error] 'codex.cmd' not found. Install Codex CLI." -ForegroundColor Red
    exit 1
}

$projectRoot = Split-Path $PSScriptRoot -Parent
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
    exit 1
}

$runPath = $resolvedRunPath.Trim()
if (-not (Test-Path -LiteralPath $runPath -PathType Container)) {
    Write-Host "[Error] Run path does not exist: $runPath" -ForegroundColor Red
    exit 1
}

function Get-Phase {
    param([string]$TargetRun)
    $phase = (apsf next $TargetRun --phase-only 2>$null)
    if ($LASTEXITCODE -eq 0 -and -not [string]::IsNullOrWhiteSpace($phase)) {
        return $phase.Trim()
    }
    return "UNKNOWN"
}

function Get-WriteFile {
    param([string]$TargetRun)
    $nextLines = apsf next $TargetRun 2>&1
    $writeMatch = $nextLines | Select-String -Pattern "Write\s*:\s*(\S+\.md)"
    if ($writeMatch) {
        return $writeMatch.Matches[0].Groups[1].Value
    }
    return "review.md"
}

function Get-TextHash {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        return ""
    }
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash
}

$phaseBefore = Get-Phase $Run
if ($phaseBefore -ne "REVIEW_NEEDED") {
    Write-Host "[Stop] Current phase is '$phaseBefore', not REVIEW_NEEDED." -ForegroundColor Yellow
    Write-Host "       codex review bridge v0 is REVIEW_NEEDED only." -ForegroundColor DarkGray
    exit 2
}

$assignmentLines = @(apsf model-assignment $Run --role Critic 2>$null)
$assignmentProvider = ($assignmentLines | Where-Object { $_ -match "^provider=(.+)" } | Select-Object -First 1) -replace "^provider=", ""
$assignmentModel = ($assignmentLines | Where-Object { $_ -match "^model=(.+)" } | Select-Object -First 1) -replace "^model=", ""
$assignmentHuman = ($assignmentLines | Where-Object { $_ -eq "human=true" } | Measure-Object).Count -gt 0

function Test-CodexModelOverride {
    param([string]$ModelName)
    if ([string]::IsNullOrWhiteSpace($ModelName)) {
        return $false
    }
    return $ModelName -match '^[A-Za-z0-9._:-]+$'
}

if ($assignmentHuman) {
    Write-Host "[Stop] model-assignment.md: Critic is human-assigned." -ForegroundColor Yellow
    Write-Host "       Keep REVIEW_NEEDED on the human/provider path for this run." -ForegroundColor DarkGray
    exit 2
}

if (-not [string]::IsNullOrWhiteSpace($assignmentProvider) -and $assignmentProvider -ne "unset" -and $assignmentProvider -ne "openai") {
    Write-Host "[Warn] model-assignment.md specifies provider=$assignmentProvider, but codex-cli bridge is OpenAI/Codex-oriented." -ForegroundColor Yellow
    Write-Host "       Proceeding with Codex CLI default model/profile." -ForegroundColor DarkGray
    $assignmentModel = ""
}
elseif (-not (Test-CodexModelOverride $assignmentModel) -and -not [string]::IsNullOrWhiteSpace($assignmentModel)) {
    Write-Host "[Warn] model-assignment.md model='$assignmentModel' is not a Codex CLI model id." -ForegroundColor Yellow
    Write-Host "       Proceeding with Codex CLI default model/profile." -ForegroundColor DarkGray
    $assignmentModel = ""
}

$promptArgs = @($Run, "--print-prompt")
if ($Force) {
    $promptArgs += "--force"
}
$reviewPrompt = & apsf act @promptArgs
if ($LASTEXITCODE -ne 0) {
    Write-Host "[FAIL] Could not generate critic prompt." -ForegroundColor Red
    exit $LASTEXITCODE
}
if ([string]::IsNullOrWhiteSpace($reviewPrompt)) {
    Write-Host "[Stop] apsf act --print-prompt returned empty output." -ForegroundColor Yellow
    Write-Host "       Check: apsf next $Run" -ForegroundColor DarkGray
    exit 2
}

$targetFile = Get-WriteFile $Run
$targetPath = Join-Path $runPath $targetFile
$targetHashBefore = Get-TextHash $targetPath
$targetExistedBefore = Test-Path -LiteralPath $targetPath -PathType Leaf

$bridgePrompt = @"
You are the APSF Codex review bridge v0.

Repository root: $projectRoot
Run: $Run
Run directory: $runPath
Target artifact: $targetFile
Current phase: REVIEW_NEEDED

Rules:
- Treat the APSF critic prompt below as the authoritative assignment.
- Prefer writing $targetFile directly in the run directory.
- If you do not write the file directly, output only the final markdown for $targetFile.
- Do not edit run_state.json or advance the phase directly.
- Do not modify unrelated artifacts unless the critic prompt explicitly requires it.

Expected outcome:
- $targetFile is created or revised on disk, or markdown is returned for APSF to save via write-phase
- APSF can evaluate the resulting artifact and decide whether the run advances

Critic prompt follows:

$reviewPrompt
"@

Write-Host "[APSF] run:         $Run" -ForegroundColor Cyan
Write-Host "[APSF] run path:    $runPath" -ForegroundColor Cyan
Write-Host "[APSF] phase:       REVIEW_NEEDED" -ForegroundColor Cyan
if (-not [string]::IsNullOrWhiteSpace($assignmentModel)) {
    Write-Host "[APSF] critic:      model=$assignmentModel" -ForegroundColor Cyan
}
Write-Host "[APSF] target file: $targetFile" -ForegroundColor Cyan
Write-Host ""

if ($DryRun) {
    Write-Host "[DryRun] Assembled prompt ($($bridgePrompt.Length) chars):" -ForegroundColor Yellow
    Write-Host ("-" * 60) -ForegroundColor DarkGray
    Write-Host $bridgePrompt.Substring(0, [Math]::Min(2000, $bridgePrompt.Length))
    if ($bridgePrompt.Length -gt 2000) {
        Write-Host "... [truncated, $($bridgePrompt.Length) total chars]" -ForegroundColor DarkGray
    }
    Write-Host ("-" * 60) -ForegroundColor DarkGray
    Write-Host "[DryRun] Would invoke: codex exec - --full-auto --skip-git-repo-check -C $projectRoot" -ForegroundColor Yellow
    exit 0
}

$codexCmd = Get-Command "codex.cmd" -ErrorAction Stop
$codexPath = $codexCmd.Source
$codexArgs = @(
    "exec",
    "-",
    "--full-auto",
    "--skip-git-repo-check",
    "-C", $projectRoot
)
if (-not [string]::IsNullOrWhiteSpace($assignmentModel)) {
    $codexArgs += @("-m", $assignmentModel)
}

Write-Host "[1/2] Invoking codex review bridge..." -ForegroundColor DarkGray
Write-Host ""

try {
    $stdinPath = [System.IO.Path]::GetTempFileName()
    $stdoutPath = [System.IO.Path]::GetTempFileName()
    $stderrPath = [System.IO.Path]::GetTempFileName()
    try {
        [System.IO.File]::WriteAllText($stdinPath, $bridgePrompt, [System.Text.Encoding]::UTF8)
        $quotedCodexPath = '"' + $codexPath + '"'
        $quotedArgs = @($codexArgs | ForEach-Object {
            $arg = [string]$_
            '"' + ($arg -replace '"', '\"') + '"'
        }) -join " "
        $cmdLine = "$quotedCodexPath $quotedArgs < `"$stdinPath`" > `"$stdoutPath`" 2> `"$stderrPath`""
        & cmd.exe /d /c $cmdLine
        $exitCode = $LASTEXITCODE
        $stdoutLines = if (Test-Path $stdoutPath) { Get-Content $stdoutPath -ErrorAction SilentlyContinue } else { @() }
        $stderrLines = if (Test-Path $stderrPath) { Get-Content $stderrPath -ErrorAction SilentlyContinue } else { @() }
        $codexOutput = @($stdoutLines + $stderrLines)
    } finally {
        foreach ($path in @($stdinPath, $stdoutPath, $stderrPath)) {
            if ($path -and (Test-Path $path)) {
                Remove-Item -LiteralPath $path -Force -ErrorAction SilentlyContinue
            }
        }
    }
} catch {
    $exceptionText = ($_ | Out-String).Trim()
    Write-Host "[FAILURE] stage=invoke-exception exit=1" -ForegroundColor Red
    if (-not [string]::IsNullOrWhiteSpace($exceptionText)) {
        foreach ($line in ($exceptionText -split "`r?`n")) {
            Write-Host ("         " + $line) -ForegroundColor DarkGray
        }
    }
    exit 1
}

$phaseAfter = Get-Phase $Run
$targetExistsAfter = Test-Path -LiteralPath $targetPath -PathType Leaf
$targetHashAfter = Get-TextHash $targetPath
$artifactUpdated = ($targetHashBefore -ne $targetHashAfter) -and -not [string]::IsNullOrWhiteSpace($targetHashAfter)
$phaseAdvanced = ($phaseAfter -ne "REVIEW_NEEDED") -and ($phaseAfter -ne "UNKNOWN")
$codexText = @($codexOutput) -join [Environment]::NewLine

if ($exitCode -eq 0 -and $phaseAdvanced) {
    Write-Host "[SUCCESS] Review complete and phase advanced to: $phaseAfter" -ForegroundColor Green
    Write-Host ""
    Write-Host "[Done] Run is ready for the next stage." -ForegroundColor Green
    Write-Host "       Execute: apsf next $Run" -ForegroundColor DarkGray
    exit 0
}

if ($exitCode -eq 0 -and $artifactUpdated) {
    Write-Host "[SUCCESS] Review artifact updated directly by codex." -ForegroundColor Green
    Write-Host ""
    Write-Host "[Done] $targetFile updated. Next: apsf next $Run" -ForegroundColor Green
    exit 0
}

if ($exitCode -eq 0 -and -not [string]::IsNullOrWhiteSpace($codexText)) {
    Write-Host "[2/2] write $targetFile via apsf write-phase..." -ForegroundColor DarkGray
    $codexText | apsf write-phase $Run --stdin
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "[Done] $targetFile saved. Next: apsf next $Run" -ForegroundColor Green
        exit 0
    }
    Write-Host "[FAILURE] stage=write-phase exit=$LASTEXITCODE" -ForegroundColor Red
}

Write-Host "[FAILURE] stage=codex-run exit=$exitCode" -ForegroundColor Red
if (-not [string]::IsNullOrWhiteSpace($codexText)) {
    Write-Host "          Last meaningful output:" -ForegroundColor DarkGray
    $tailLines = @(
        $codexText -split "`r?`n" |
        ForEach-Object { $_.TrimEnd() } |
        Where-Object { -not [string]::IsNullOrWhiteSpace($_) }
    )
    if ($tailLines.Count -gt 12) {
        $tailLines = $tailLines[($tailLines.Count - 12)..($tailLines.Count - 1)]
    }
    foreach ($line in $tailLines) {
        Write-Host ("          " + $line) -ForegroundColor DarkGray
    }
}

Write-Host ""
Write-Host "          Next: inspect $targetFile and run 'apsf next $Run'." -ForegroundColor DarkGray
exit ($(if ($exitCode -ne 0) { $exitCode } else { 2 }))
