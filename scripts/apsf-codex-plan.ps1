<#
.SYNOPSIS
    APSF Plan wrapper for Codex CLI.

.DESCRIPTION
    Runs Codex in a bounded bridge mode for PLAN_NEEDED only.
    Contract:
      - APSF resolves run/phase/prompt.
      - Codex updates plan.md directly.
      - This wrapper emits a structured result based on observed artifact/gate outcome.
      - Phase advancement authority remains with APSF.
#>

param(
    [Parameter(Mandatory = $true, Position = 0)]
    [string]$Run,

    [switch]$DryRun,
    [switch]$UntilPlan,
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
if ($UntilPlan) {
    Write-Host "[Stop] -UntilPlan is not supported in apsf-codex-plan.ps1." -ForegroundColor Yellow
    Write-Host "       This bridge is already scoped to PLAN_NEEDED only." -ForegroundColor DarkGray
    exit 2
}

$projectRoot = Split-Path $PSScriptRoot -Parent
$resolvedRunPath = @"
from pathlib import Path
from apsf.legacy.storage.run_repository import RunRepository

project_root = Path(r"$projectRoot")
repo = RunRepository(
    runs_dir=project_root / "runs",
    template_dir=project_root / "runs" / "_template",
)
print(repo.get_run_dir(r"$Run"))
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

function Get-TextHash {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        return ""
    }
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash
}

function Test-CodexModelOverride {
    param([string]$Model)
    if ([string]::IsNullOrWhiteSpace($Model)) {
        return $false
    }
    return $Model -match '^[A-Za-z0-9._:-]+$'
}

$phaseBefore = Get-Phase $Run
if ($phaseBefore -ne "PLAN_NEEDED") {
    Write-Host "[Stop] Current phase is '$phaseBefore', not PLAN_NEEDED." -ForegroundColor Yellow
    Write-Host "       codex plan bridge v0 is PLAN_NEEDED only." -ForegroundColor DarkGray
    exit 2
}

$assignmentLines = @(apsf model-assignment $Run --role Planner 2>$null)
$assignmentProvider = ($assignmentLines | Where-Object { $_ -match "^provider=(.+)" } | Select-Object -First 1) -replace "^provider=", ""
$assignmentModel = ($assignmentLines | Where-Object { $_ -match "^model=(.+)" } | Select-Object -First 1) -replace "^model=", ""
$assignmentHuman = ($assignmentLines | Where-Object { $_ -eq "human=true" } | Measure-Object).Count -gt 0

if ($assignmentHuman) {
    Write-Host "[Stop] model-assignment.md: Planner is human-assigned." -ForegroundColor Yellow
    Write-Host "       Keep PLAN_NEEDED on the human/provider path for this run." -ForegroundColor DarkGray
    exit 2
}

if (-not [string]::IsNullOrWhiteSpace($assignmentProvider) -and $assignmentProvider -ne "unset" -and $assignmentProvider -ne "openai") {
    Write-Host "[Warn] model-assignment.md specifies provider=$assignmentProvider, but codex-cli bridge is OpenAI/Codex-oriented." -ForegroundColor Yellow
    Write-Host "       Proceeding with Codex CLI default model/profile." -ForegroundColor DarkGray
    $assignmentModel = ""
} elseif (-not (Test-CodexModelOverride $assignmentModel) -and -not [string]::IsNullOrWhiteSpace($assignmentModel)) {
    Write-Host "[Warn] model-assignment.md model='$assignmentModel' is not a Codex CLI model id." -ForegroundColor Yellow
    Write-Host "       Proceeding with Codex CLI default model/profile." -ForegroundColor DarkGray
    $assignmentModel = ""
}

$planPromptArgs = @($Run, "--print-prompt")
if ($Force) {
    $planPromptArgs += "--force"
    $planPromptArgs += "--force-reason"
    $planPromptArgs += "codex plan bridge overwrite"
}
$planPrompt = & apsf act @planPromptArgs
if ($LASTEXITCODE -ne 0) {
    Write-Host "[FAIL] Could not generate planner prompt." -ForegroundColor Red
    exit $LASTEXITCODE
}
if ([string]::IsNullOrWhiteSpace($planPrompt)) {
    Write-Host "[Stop] apsf act --print-prompt returned empty output." -ForegroundColor Yellow
    Write-Host "       Check: apsf next $Run" -ForegroundColor DarkGray
    exit 2
}

$planPath = Join-Path $runPath "plan.md"
$planHashBefore = Get-TextHash $planPath
$planExistedBefore = Test-Path -LiteralPath $planPath -PathType Leaf

$bridgePrompt = @"
You are the APSF Codex plan bridge v0.

Repository root: $projectRoot
Run: $Run
Run directory: $runPath
Target artifact: plan.md
Current phase: PLAN_NEEDED

Rules:
- Treat the APSF planner prompt below as the authoritative assignment.
- Update only plan.md for this run.
- Do not edit run_state.json or advance the phase directly.
- Do not modify unrelated artifacts unless the planner prompt explicitly requires it.
- Keep the change bounded to making plan.md sufficient for APSF planning review.

Expected outcome:
- plan.md is created or revised on disk
- APSF can evaluate the resulting artifact and decide whether the run advances

Planner prompt follows:

$planPrompt
"@

Write-Host "[APSF] run:       $Run" -ForegroundColor Cyan
Write-Host "[APSF] run path:  $runPath" -ForegroundColor Cyan
Write-Host "[APSF] phase:     PLAN_NEEDED" -ForegroundColor Cyan
if (-not [string]::IsNullOrWhiteSpace($assignmentModel)) {
    Write-Host "[APSF] planner:   model=$assignmentModel" -ForegroundColor Cyan
}
Write-Host "[APSF] target:    $planPath" -ForegroundColor Cyan
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

Write-Host "[1/1] Invoking codex plan bridge..." -ForegroundColor DarkGray
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
    if (-not [string]::IsNullOrWhiteSpace($exceptionText)) {
        Write-Host $exceptionText -ForegroundColor DarkGray
    }
    exit 1
}

$phaseAfter = Get-Phase $Run
$planExistsAfter = Test-Path -LiteralPath $planPath -PathType Leaf
$planHashAfter = Get-TextHash $planPath
$artifactUpdated = ($planHashBefore -ne $planHashAfter) -and -not [string]::IsNullOrWhiteSpace($planHashAfter)
$phaseAdvanced = ($phaseAfter -ne "PLAN_NEEDED") -and ($phaseAfter -ne "UNKNOWN")
$codexText = @($codexOutput) -join [Environment]::NewLine
$tailLines = @(
    $codexText -split "`r?`n" |
    ForEach-Object { $_.TrimEnd() } |
    Where-Object { -not [string]::IsNullOrWhiteSpace($_) }
)
if ($tailLines.Count -gt 8) {
    $tailLines = $tailLines[($tailLines.Count - 8)..($tailLines.Count - 1)]
}

$status = if ($exitCode -ne 0) {
    "failed"
} elseif (-not $planExistsAfter) {
    "failed"
} elseif ($artifactUpdated -or $phaseAdvanced) {
    "success"
} else {
    "no_change"
}

$summary = if ($status -eq "success" -and $phaseAdvanced) {
    "Codex bridge updated plan.md and APSF now reports phase '$phaseAfter'."
} elseif ($status -eq "success") {
    "Codex bridge updated plan.md. APSF phase judgement remains '$phaseAfter'."
} elseif ($status -eq "no_change") {
    "Codex bridge completed without a detectable plan.md change."
} else {
    "Codex bridge failed to produce a usable plan.md result."
}

$result = [ordered]@{
    status = $status
    run_name = $Run
    phase = "PLAN_NEEDED"
    target_artifact = "plan.md"
    artifact_updated = $artifactUpdated
    summary = $summary
    evidence = [ordered]@{
        phase_before = $phaseBefore
        phase_after = $phaseAfter
        phase_advanced = $phaseAdvanced
        artifact_existed_before = $planExistedBefore
        artifact_exists_after = $planExistsAfter
        codex_exit_code = $exitCode
        output_tail = $tailLines
    }
}

Write-Host ""
$result | ConvertTo-Json -Depth 5

if ($status -eq "failed") {
    exit ($(if ($exitCode -ne 0) { $exitCode } else { 2 }))
}
exit 0
