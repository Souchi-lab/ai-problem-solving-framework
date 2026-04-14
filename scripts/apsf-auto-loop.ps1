<#
.SYNOPSIS
    APSF auto loop for PLAN/BUILD/REVIEW until a human-owned phase is reached.
.DESCRIPTION
    Repeats PLAN_NEEDED / BUILD_NEEDED / REVIEW_NEEDED using the selected wrapper scripts.
    Stops on human-owned phases such as IMPROVE_NEEDED / RESULT_NEEDED, on GUI stop requests,
    or when a wrapper returns a non-continuable exit code.
#>

param(
    [Parameter(Mandatory = $true, Position = 0)]
    [string]$Run,

    [string]$PlanScript = "apsf-codex-plan.ps1",

    [string]$BuildScript = "apsf-codex-build.ps1",

    [string]$ReviewScript = "apsf-claude-act.ps1",

    [int]$MaxCycles = 10
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path $PSScriptRoot -Parent

$HUMAN_PHASES = @(
    "GOAL_NEEDED", "SETUP_NEEDED", "IMPROVE_PLAN_OPTIONAL",
    "IMPROVE_NEEDED", "VERIFY_OPTIONAL", "RESULT_NEEDED",
    "TRANSCRIPT_RECOMMENDED", "COMPLETE"
)

function Write-LoopLog {
    param([string]$Message)
    $timestamp = Get-Date -Format "yyyy-MM-ddTHH:mm:ssK"
    Write-Host "[$timestamp] $Message"
}

function Get-Phase {
    $phase = (apsf next $Run --phase-only 2>$null)
    if ($LASTEXITCODE -eq 0 -and -not [string]::IsNullOrWhiteSpace($phase)) {
        return $phase.Trim()
    }
    return "UNKNOWN"
}

Write-LoopLog "auto_loop_start run=$Run plan=$PlanScript build=$BuildScript review=$ReviewScript max_cycles=$MaxCycles"

# Resolve run directory once for stop-signal check
$resolvedRunDir = @"
import sys
from pathlib import Path
from apsf.legacy.storage.run_repository import RunRepository
sys.stdout.reconfigure(encoding="utf-8")
project_root = Path(r"$projectRoot")
repo = RunRepository(runs_dir=project_root / "runs", template_dir=project_root / "runs" / "_template")
run_name = r"$Run"
parts = [p for p in run_name.split("/") if p]
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
        print(repo.get_child_run_dir(parent, child))
else:
    print(repo.get_run_dir(run_name))
"@ | python -

$runDir = $resolvedRunDir.Trim()
$stopFile = Join-Path $runDir ".apsf_stop_requested"
$pidFile = Join-Path $runDir ".apsf_loop_pid"

trap {
    Remove-Item -LiteralPath $pidFile -Force -ErrorAction SilentlyContinue
    Write-LoopLog "stop_reason=trap"
    break
}

function Get-ImproveDecision {
    $payload = @"
import json
import sys
from pathlib import Path
from apsf.viewer import api

sys.stdout.reconfigure(encoding="utf-8")
run_dir = Path(r"$runDir")
print(json.dumps(api._evaluate_improve_auto_loop_decision(run_dir), ensure_ascii=False))
"@ | python -

    if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($payload)) {
        throw "Failed to evaluate improve advisory."
    }

    return $payload | ConvertFrom-Json
}

function Write-LoopMarker {
    try {
        $process = Get-Process -Id $PID -ErrorAction Stop
        $cim = Get-CimInstance Win32_Process -Filter "ProcessId = $PID" -ErrorAction Stop
        $marker = [ordered]@{
            pid = $PID
            process_name = $process.ProcessName + ".exe"
            started_at = $process.StartTime.ToUniversalTime().ToString("o")
            command_line = if ($null -ne $cim.CommandLine) { [string]$cim.CommandLine } else { $null }
        }
        $marker | ConvertTo-Json -Compress | Set-Content -LiteralPath $pidFile -Encoding UTF8
        return
    } catch {
    }

    Set-Content -LiteralPath $pidFile -Value ([string]$PID) -Encoding UTF8
}

function Invoke-Reroute {
    param(
        [Parameter(Mandatory = $true)]
        [ValidateSet("Return to Build", "Return to Plan")]
        [string]$Recommendation
    )

    if ($Recommendation -eq "Return to Build") {
        Write-LoopLog "invoke role=judge-reroute script=apsf-rerun-build.ps1"
        & (Join-Path $scriptRoot "apsf-rerun-build.ps1") $Run
        $exitCode = $LASTEXITCODE
        Write-LoopLog "result role=judge-reroute target=BUILD_NEEDED exit=$exitCode"
        return $exitCode
    }

    Write-LoopLog "invoke role=judge-reroute script=apsf-rerun-plan.ps1"
    & (Join-Path $scriptRoot "apsf-rerun-plan.ps1") $Run
    $exitCode = $LASTEXITCODE
    Write-LoopLog "result role=judge-reroute target=PLAN_NEEDED exit=$exitCode"
    return $exitCode
}

function Handle-ImproveNeeded {
    try {
        $decision = Get-ImproveDecision
    } catch {
        Write-LoopLog "[IMPROVE_NEEDED] advisory_source=judge_advisory_error recommendation= human_owned_blocker= action=STOP reason=advisory_missing"
        Write-LoopLog "stop_reason=advisory_missing phase=IMPROVE_NEEDED"
        exit 0
    }

    $advisorySource = if ($null -ne $decision.advisory_source -and -not [string]::IsNullOrWhiteSpace([string]$decision.advisory_source)) {
        [string]$decision.advisory_source
    } else {
        ""
    }
    $recommendation = if ($null -ne $decision.recommendation) { [string]$decision.recommendation } else { "" }
    $hasHumanOwnedBlocker = ($decision.PSObject.Properties.Name -contains "human_owned_blocker") -and $null -ne $decision.human_owned_blocker
    $humanOwnedBlocker = if ($hasHumanOwnedBlocker) { [bool]$decision.human_owned_blocker } else { $null }
    $action = if ($null -ne $decision.action) { [string]$decision.action } else { "STOP" }
    $reason = if ($null -ne $decision.reason) { [string]$decision.reason } else { "advisory_missing" }
    $logLine = if ($null -ne $decision.log_line -and -not [string]::IsNullOrWhiteSpace([string]$decision.log_line)) {
        [string]$decision.log_line
    } else {
        "[IMPROVE_NEEDED] advisory_source=$advisorySource recommendation=$recommendation human_owned_blocker=$humanOwnedBlocker action=$action reason=$reason"
    }
    $stopReason = if ($null -ne $decision.stop_reason -and -not [string]::IsNullOrWhiteSpace([string]$decision.stop_reason)) {
        [string]$decision.stop_reason
    } else {
        $null
    }

    if ($action -eq "BUILD_NEEDED" -or $action -eq "PLAN_NEEDED") {
        Write-LoopLog $logLine
        $exitCode = Invoke-Reroute -Recommendation $recommendation
        if ($exitCode -ne 0) {
            Write-LoopLog "stop_reason=judge_reroute_exit exit=$exitCode target=$recommendation"
            exit $exitCode
        }
        return
    }

    Write-LoopLog $logLine
    if ($null -ne $stopReason) {
        Write-LoopLog "stop_reason=$stopReason phase=IMPROVE_NEEDED"
    } else {
        Write-LoopLog "stop_reason=human_phase phase=IMPROVE_NEEDED"
    }
    exit 0
}

Write-LoopMarker

try {
    for ($cycle = 1; $cycle -le $MaxCycles; $cycle++) {
        $phase = Get-Phase
        Write-LoopLog "cycle=$cycle/$MaxCycles phase=$phase"

        if (Test-Path -LiteralPath $stopFile) {
            Remove-Item -LiteralPath $stopFile -Force -ErrorAction SilentlyContinue
            Write-LoopLog "stop_reason=gui_stop_request phase=$phase"
            exit 0
        }

        if ($phase -eq "IMPROVE_NEEDED") {
            Handle-ImproveNeeded
            continue
        }

        if ($HUMAN_PHASES -contains $phase) {
            Write-LoopLog "stop_reason=human_phase phase=$phase"
            exit 0
        }

        if ($phase -eq "UNKNOWN") {
            Write-LoopLog "stop_reason=unknown_phase"
            exit 1
        }

        if ($phase -eq "PLAN_NEEDED") {
            Write-LoopLog "invoke role=plan script=$PlanScript"
            & (Join-Path $scriptRoot $PlanScript) $Run
            $exitCode = $LASTEXITCODE
            Write-LoopLog "result role=plan exit=$exitCode"
            if ($exitCode -ne 0 -and $exitCode -ne 2) {
                Write-LoopLog "stop_reason=plan_exit exit=$exitCode"
                exit $exitCode
            }
        } elseif ($phase -eq "BUILD_NEEDED") {
            Write-LoopLog "invoke role=build script=$BuildScript"
            & (Join-Path $scriptRoot $BuildScript) $Run
            $exitCode = $LASTEXITCODE
            Write-LoopLog "result role=build exit=$exitCode"
            if ($exitCode -ne 0 -and $exitCode -ne 2) {
                Write-LoopLog "stop_reason=build_exit exit=$exitCode"
                exit $exitCode
            }
        } elseif ($phase -eq "REVIEW_NEEDED") {
            Write-LoopLog "invoke role=review script=$ReviewScript"
            & (Join-Path $scriptRoot $ReviewScript) $Run
            $exitCode = $LASTEXITCODE
            Write-LoopLog "result role=review exit=$exitCode"
            if ($exitCode -ne 0 -and $exitCode -ne 2) {
                Write-LoopLog "stop_reason=review_exit exit=$exitCode"
                exit $exitCode
            }
        } else {
            Write-LoopLog "stop_reason=unhandled_phase phase=$phase"
            exit 0
        }
    }

    $currentPhase = Get-Phase
    Write-LoopLog "stop_reason=max_cycles phase=$currentPhase max_cycles=$MaxCycles"
    exit 0
} finally {
    Remove-Item -LiteralPath $pidFile -Force -ErrorAction SilentlyContinue
}
