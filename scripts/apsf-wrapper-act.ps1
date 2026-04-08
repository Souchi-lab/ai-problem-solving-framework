<#
.SYNOPSIS
    APSF wrapper entrypoint for ACT phases.

.DESCRIPTION
    Keeps wrapper mode stable while allowing explicit backend selection.
    Current capability boundary:
      - claude-cli: supported
      - codex-cli : supported for PLAN_NEEDED and REVIEW_NEEDED via bounded bridge
                    unsupported for other act phases
#>

param(
    [Parameter(Mandatory = $true, Position = 0)]
    [string]$Run,

    [ValidateSet("claude-cli", "codex-cli")]
    [string]$Backend = "claude-cli",

    [switch]$DryRun,
    [switch]$UntilPlan,
    [switch]$Force,
    [switch]$VerboseOutput
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path

function Get-Phase {
    param([string]$TargetRun)

    $phase = (apsf next $TargetRun --phase-only 2>$null)
    if ($LASTEXITCODE -eq 0 -and -not [string]::IsNullOrWhiteSpace($phase)) {
        return $phase.Trim()
    }
    return "UNKNOWN"
}

switch ($Backend) {
    "claude-cli" {
        $args = @($Run)
        if ($DryRun) { $args += "-DryRun" }
        if ($UntilPlan) { $args += "-UntilPlan" }
        if ($Force) { $args += "-Force" }
        if ($VerboseOutput) { $args += "-VerboseOutput" }
        & (Join-Path $scriptRoot "apsf-claude-act.ps1") @args
        exit $LASTEXITCODE
    }
    "codex-cli" {
        $phase = Get-Phase $Run
        if ($phase -eq "PLAN_NEEDED") {
            $args = @($Run)
            if ($DryRun) { $args += "-DryRun" }
            if ($UntilPlan) { $args += "-UntilPlan" }
            if ($Force) { $args += "-Force" }
            if ($VerboseOutput) { $args += "-VerboseOutput" }
            & (Join-Path $scriptRoot "apsf-codex-plan.ps1") @args
            exit $LASTEXITCODE
        }

        if ($phase -eq "REVIEW_NEEDED") {
            $args = @($Run)
            if ($DryRun) { $args += "-DryRun" }
            if ($Force) { $args += "-Force" }
            if ($VerboseOutput) { $args += "-VerboseOutput" }
            & (Join-Path $scriptRoot "apsf-codex-review.ps1") @args
            exit $LASTEXITCODE
        }

        if ($phase -eq "BUILD_NEEDED") {
            Write-Host "[Stop] BUILD_NEEDED does not use 'act' with backend 'codex-cli'." -ForegroundColor Yellow
            Write-Host "       Use the build wrapper instead:" -ForegroundColor DarkGray
            Write-Host "         .\\scripts\\apsf-wrapper-build.ps1 $Run -Backend codex-cli" -ForegroundColor DarkGray
            Write-Host "       Alternative:" -ForegroundColor DarkGray
            Write-Host "         apsf build $Run" -ForegroundColor DarkGray
            exit 2
        }

        Write-Host "[Stop] wrapper backend 'codex-cli' is not supported for act phase '$phase'." -ForegroundColor Yellow
        Write-Host "       Current codex act bridge scope is PLAN_NEEDED and REVIEW_NEEDED only." -ForegroundColor DarkGray
        Write-Host "       BUILD_NEEDED should use the tool-enabled build wrapper." -ForegroundColor DarkGray
        exit 2
    }
}
