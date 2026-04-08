<#
.SYNOPSIS
    APSF wrapper entrypoint for BUILD phases.

.DESCRIPTION
    Preserves wrapper-first execution while allowing backend selection.
    Supported backends:
      - claude-cli
      - codex-cli
#>

param(
    [Parameter(Mandatory = $true, Position = 0)]
    [string]$Run,

    [ValidateSet("claude-cli", "codex-cli")]
    [string]$Backend = "claude-cli",

    [switch]$DryRun,

    [string]$PromptFile = "",

    [int]$MaxTurns = 10,

    [string]$Tools = "Bash,Edit,Glob,Grep,Read,Write,mcp__filesystem__read_file,mcp__filesystem__write_file,mcp__filesystem__list_directory"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path

switch ($Backend) {
    "claude-cli" {
        $invoke = @{
            Run = $Run
            MaxTurns = $MaxTurns
            Tools = $Tools
        }
        if ($DryRun) { $invoke.DryRun = $true }
        if (-not [string]::IsNullOrWhiteSpace($PromptFile)) { $invoke.PromptFile = $PromptFile }
        & (Join-Path $scriptRoot "apsf-claude-build.ps1") @invoke
        exit $LASTEXITCODE
    }
    "codex-cli" {
        $invoke = @{
            Run = $Run
            MaxTurns = $MaxTurns
        }
        if ($DryRun) { $invoke.DryRun = $true }
        if (-not [string]::IsNullOrWhiteSpace($PromptFile)) { $invoke.PromptFile = $PromptFile }
        & (Join-Path $scriptRoot "apsf-codex-build.ps1") @invoke
        exit $LASTEXITCODE
    }
}
