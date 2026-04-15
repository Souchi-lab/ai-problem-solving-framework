<#
.SYNOPSIS
    APSF x claude -p pipe execution wrapper

.DESCRIPTION
    Runs: apsf act <run> --print-prompt | claude -p | apsf write-phase <run> --stdin

    Supports:
    - single-phase execution
    - -UntilPlan chain mode (generate execution-assignment if needed, then plan)
    - -DryRun preview
    - template-only guard recovery via --force retry
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
if (-not (Get-Command "claude" -ErrorAction SilentlyContinue)) {
    Write-Host "[Error] 'claude' not found. Install Claude Code CLI." -ForegroundColor Red
    exit 1
}

function Get-Phase {
    param([string]$TargetRun)
    $nextLines = apsf next $TargetRun 2>&1
    $phaseMatch = $nextLines | Select-String -Pattern "Phase\s*:\s*(\S+)"
    if ($phaseMatch) {
        return $phaseMatch.Matches[0].Groups[1].Value
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
    return "unknown"
}

function Resolve-RunFilePath {
    param(
        [string]$TargetRun,
        [string]$TargetFile
    )

    $runsRoot = Join-Path (Split-Path $PSScriptRoot -Parent) "runs"
    $normalizedRun = $TargetRun -replace '/', '\'
    $segments = $normalizedRun.Split('\', [System.StringSplitOptions]::RemoveEmptyEntries)

    if ($segments.Length -eq 3 -and @("work", "fw-improvement") -contains $segments[0]) {
        $candidate = Join-Path $runsRoot $normalizedRun
        $path = Join-Path $candidate $TargetFile
        if (Test-Path -LiteralPath $path -PathType Leaf) {
            return $path
        }
    }

    if ($segments.Length -eq 2) {
        $direct = Join-Path $runsRoot $normalizedRun
        $directFile = Join-Path $direct $TargetFile
        if (Test-Path -LiteralPath $directFile -PathType Leaf) {
            return $directFile
        }

        foreach ($taxonomy in @("fw-improvement", "work")) {
            $candidate = Join-Path (Join-Path $runsRoot $taxonomy) $normalizedRun
            $path = Join-Path $candidate $TargetFile
            if (Test-Path -LiteralPath $path -PathType Leaf) {
                return $path
            }
        }
    }

    if ($segments.Length -eq 1) {
        foreach ($taxonomy in @("fw-improvement", "work")) {
            $candidate = Join-Path (Join-Path $runsRoot $taxonomy) $segments[0]
            $path = Join-Path $candidate $TargetFile
            if (Test-Path -LiteralPath $path -PathType Leaf) {
                return $path
            }
        }

        if ($segments[0] -match '^\d{3}c\d+_[a-z0-9-]+_.+$') {
            foreach ($taxonomy in @("fw-improvement", "work")) {
                $taxonomyDir = Join-Path $runsRoot $taxonomy
                if (-not (Test-Path -LiteralPath $taxonomyDir -PathType Container)) {
                    continue
                }
                $match = Get-ChildItem -LiteralPath $taxonomyDir -Directory -ErrorAction SilentlyContinue |
                    ForEach-Object { Join-Path (Join-Path $_.FullName $segments[0]) $TargetFile } |
                    Where-Object { Test-Path -LiteralPath $_ -PathType Leaf } |
                    Select-Object -First 1
                if ($null -ne $match) {
                    return $match
                }
            }
        }
    }

    $match = Get-ChildItem -Path $runsRoot -Recurse -File -Filter $TargetFile -ErrorAction SilentlyContinue |
        Where-Object { $_.FullName -like "*\$normalizedRun\$TargetFile" } |
        Select-Object -First 1

    if ($null -ne $match) {
        return $match.FullName
    }

    return $null
}

function Get-Specialist {
    param(
        [string]$TargetRun,
        [string]$CurrentPhase
    )
    
    $roleName = switch ($CurrentPhase) {
        "SETUP_NEEDED"  { "Planner" }
        "PLAN_NEEDED"   { "Planner" }
        "BUILD_NEEDED"  { "Builder" }
        "REVIEW_NEEDED" { "Critic" }
        "ADOPT_NEEDED"  { "Judge" }
        "RESULT_NEEDED" { "Judge" }
        default         { "" }
    }

    if ([string]::IsNullOrWhiteSpace($roleName)) {
        return "Unknown"
    }

    $assignmentFile = Resolve-RunFilePath -TargetRun $TargetRun -TargetFile "execution-assignment.md"
    if ($null -eq $assignmentFile -or -not (Test-Path -LiteralPath $assignmentFile)) {
        return "Unknown (Setup pending)"
    }

    $lines = Get-Content -LiteralPath $assignmentFile
    $execType = ""
    $tool = ""
    $specialistSubtype = ""

    # Parse table for Executor, Tool, and fallback Notes
    foreach ($line in $lines) {
        if ($line -match "^\|\s*(?i)$roleName\s*\|\s*([^\|]+?)\s*\|\s*([^\|]+?)\s*\|\s*([^\|]+?)\s*\|\s*(.*)$") {
            $execType = $matches[1].Trim()
            $tool = $matches[2].Trim()
            $notes = $matches[4].Trim()
            if ($notes -match "(?i)Primary\s+[A-Z]-TYPE:\s*([^\|\.]+)") {
                $specialistSubtype = $matches[1].Trim()
            }
            break
        }
    }
    
    # Parse explicit [Role] Specialist section if it exists
    $inRoleSection = $false
    foreach ($line in $lines) {
        if ($line -match "^##\s*(?i)$roleName\s*Specialist") {
            $inRoleSection = $true
            continue
        }
        if ($inRoleSection -and $line -match "^##\s+") {
            $inRoleSection = $false
        }
        if ($inRoleSection -and $line -match "(?i)Primary\s+[A-Z]-TYPE:\s*(.+)") {
            $specialistSubtype = $matches[1].Trim()
            break
        }
    }

    # Parse Confirmed Specialist section if still unknown
    if ($specialistSubtype -eq "" -or $specialistSubtype -eq "Unknown") {
        $inConfirmSection = $false
        foreach ($line in $lines) {
            if ($line -match "^##\s*Confirmed\s+Specialist") {
                $inConfirmSection = $true
                continue
            }
            if ($inConfirmSection -and $line -match "^##\s+") {
                $inConfirmSection = $false
            }
            if ($inConfirmSection -and $line -match "(?i)[A-Z]-TYPE\s*:\s*([^\|\s\.]+)") {
                $specialistSubtype = $matches[1].Trim()
                break
            }
        }
    }

    $base = if ($execType -ne "") { "$execType ($tool)" } else { "Not Assigned" }
    
    if ($specialistSubtype -ne "") {
        return "$base => $specialistSubtype"
    }
    
    return $base
}

function Get-FileState {
    param([string]$Path)

    if ([string]::IsNullOrWhiteSpace($Path) -or -not (Test-Path -LiteralPath $Path)) {
        return [PSCustomObject]@{
            Exists = $false
            Hash = ""
            Length = 0
        }
    }

    $item = Get-Item -LiteralPath $Path
    $hash = (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash
    return [PSCustomObject]@{
        Exists = $true
        Hash = $hash
        Length = $item.Length
    }
}

function Get-PromptWithRetry {
    param(
        [string]$TargetRun,
        [string]$ExpectedPhase
    )

    $prompt = apsf act $TargetRun --print-prompt 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[FAIL] stage=generate-prompt exit=$LASTEXITCODE" -ForegroundColor Red
        exit $LASTEXITCODE
    }

    if (-not [string]::IsNullOrWhiteSpace($prompt)) {
        return $prompt
    }

    $currentPhase = Get-Phase $TargetRun
    if ($currentPhase -eq $ExpectedPhase) {
        Write-Host "  [retry] prompt blocked by template-only content; retry with --force..." -ForegroundColor DarkGray
        $prompt = apsf act $TargetRun --print-prompt --force 2>$null
        if ($LASTEXITCODE -ne 0) {
            Write-Host "[FAIL] stage=generate-prompt-retry exit=$LASTEXITCODE" -ForegroundColor Red
            exit $LASTEXITCODE
        }
    }

    return $prompt
}

function Get-ClaudeTimeoutSec {
    $raw = $env:APSF_CLAUDE_TIMEOUT_SEC
    if ([string]::IsNullOrWhiteSpace($raw)) {
        return 600
    }

    $value = 0
    if (-not [int]::TryParse($raw, [ref]$value)) {
        return 600
    }

    if ($value -lt 30) {
        return 30
    }

    return $value
}

function Test-Artifact {
    param([string]$Content, [string]$TargetFile)

    $lines = @($Content -split "`r?`n")
    $firstLine = ""
    $isClaudeError = $false

    foreach ($line in $lines) {
        $trimmed = $line.Trim()
        if (-not [string]::IsNullOrWhiteSpace($trimmed)) {
            $cleaned = $trimmed.TrimStart([char]0xFEFF)
            if ($cleaned -match '^Error: Reached max turns') {
                $isClaudeError = $true
                continue
            }
            $firstLine = $cleaned
            break
        }
    }

    if ([string]::IsNullOrWhiteSpace($firstLine)) {
        return [PSCustomObject]@{
            Valid = $false
            Level = "FAIL"
            Reason = "Claude returned empty artifact content."
            CleanContent = $Content
        }
    }

    $cleanContent = $Content
    if ($lines.Count -ge 3 -and $firstLine -match '^```') {
        # Search LAST plain ``` to find the outer closing fence.
        # Searching first would mistake an inner ```apsf-judge-advisory``` closing fence
        # for the outer fence, truncating the advisory block and breaking the regex match.
        $closingFenceIndex = -1
        for ($i = $lines.Count - 1; $i -ge 1; $i--) {
            if ($lines[$i].Trim() -eq '```') {
                $closingFenceIndex = $i
                break
            }
        }
        if ($closingFenceIndex -gt 0) {
            $innerLines = $lines[1..($closingFenceIndex - 1)]
            $cleanContent = ($innerLines -join "`n").Trim()
            $lines = @($cleanContent -split "`r?`n")
            $firstLine = ""
            foreach ($line in $lines) {
                $trimmed = $line.Trim()
                if (-not [string]::IsNullOrWhiteSpace($trimmed)) {
                    $firstLine = $trimmed.TrimStart([char]0xFEFF)
                    break
                }
            }
        }
    }

    if (
        $firstLine -match '^`\S+`\s+(created|written|has been)' -or
        $firstLine -match '^\S+\.md\s+(created|written|has been)' -or
        $firstLine -match '^(Here is|I created|I wrote|The file|Please approve)'
    ) {
        return [PSCustomObject]@{
            Valid = $false
            Level = "FAIL"
            Reason = "Output looks like meta-commentary. First line: $firstLine"
            CleanContent = $Content
        }
    }

    $missingWarnings = @()
    $missingRequired = @()

    if ($TargetFile -eq 'plan.md') {
        if ($firstLine -notmatch '^#\s+Plan\b') {
            return [PSCustomObject]@{"Valid"=$false; "Level"="FAIL"; "Reason"="Artifact does not start with '# Plan'. First line: $firstLine"; "CleanContent"=$Content}
        }
        foreach ($section in @('Problem Structure', 'Execution Plan')) {
            if ($Content -notmatch "(?m)^#{1,3}\s+$section\b") { $missingRequired += $section }
        }
        $hasOptions = ($Content -match '(?m)^#{1,3}\s+Options?\b' -or $Content -match '(?m)^#{1,3}\s+Selected Approach\b')
        if (-not $hasOptions) { $missingRequired += 'Options or Selected Approach' }

        foreach ($section in @('Goal Readiness Check', 'Implementation Readiness', 'Assumptions & Open Questions')) {
            if ($Content -notmatch "(?m)^#{1,3}\s+$([regex]::Escape($section))\b") { $missingWarnings += $section }
        }
    } elseif ($TargetFile -eq 'execution-assignment.md') {
        if ($firstLine -notmatch '^#\s+Execution Assignment\b') {
            return [PSCustomObject]@{"Valid"=$false; "Level"="FAIL"; "Reason"="Artifact does not start with '# Execution Assignment'. First line: $firstLine"; "CleanContent"=$Content}
        }
        if ($Content -notmatch "(?m)^##\s+Role Execution Assignments\b") {
            $missingRequired += 'Role Execution Assignments'
        } else {
            foreach ($role in @('Planner', 'Builder', 'Critic', 'Judge')) {
                if ($Content -notmatch "(?m)^\|\s*$role\b") {
                    $missingRequired += "Role:$role"
                }
            }
        }
    } elseif ($TargetFile -eq 'review.md') {
        if ($firstLine -notmatch '^#{1,2}\s+.*\bReview\b') {
            return [PSCustomObject]@{"Valid"=$false; "Level"="FAIL"; "Reason"="Artifact does not start with a review heading. First line: $firstLine"; "CleanContent"=$Content}
        }
    } elseif ($TargetFile -eq 'build.md') {
        if ($firstLine -notmatch '^#\s+Build\b') {
            return [PSCustomObject]@{"Valid"=$false; "Level"="FAIL"; "Reason"="Artifact does not start with '# Build'. First line: $firstLine"; "CleanContent"=$Content}
        }
    }

    if ($missingRequired.Count -gt 0) {
        return [PSCustomObject]@{
            Valid = $false
            Level = "FAIL"
            Reason = "Missing required sections: $($missingRequired -join ', ')"
            CleanContent = $cleanContent
        }
    }

    # Clean the content if we skipped Claude errors
    if ($isClaudeError) {
        $cleanContent = ($lines | Where-Object { $_ -notmatch '^Error: Reached max turns' }) -join "`n"
    }

    return [PSCustomObject]@{
        Valid = $true
        Level = if ($missingWarnings.Count -gt 0) { "WARN" } else { "OK" }
        Reason = if ($missingWarnings.Count -gt 0) { "Optional sections not found: $($missingWarnings -join ', ')" } else { "" }
        CleanContent = $cleanContent
    }
}

function Invoke-ClaudePrompt {
    param(
        [string]$PromptText,
        [switch]$VerboseOutput
    )

    $timeoutSec = Get-ClaudeTimeoutSec
    $claudeCmd = Get-Command "claude" -ErrorAction Stop
    $claudePath = $claudeCmd.Source
    $job = Start-Job -ScriptBlock {
        param(
            [string]$ResolvedClaudePath,
            [string]$Prompt
        )

        $ErrorActionPreference = "Stop"
        $OutputEncoding = [System.Text.Encoding]::UTF8
        [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
        try {
            $claudeArgs = @(
                '-p',
                '--tools', '',
                '--output-format', 'text',
                '--no-session-persistence',
                '--max-turns', '3',
                '--disable-slash-commands'
            )
            $output = $Prompt | & $ResolvedClaudePath @claudeArgs 2>&1
            $exitCode = $LASTEXITCODE
            [PSCustomObject]@{
                Output = @($output)
                ExitCode = if ($null -eq $exitCode) { 0 } else { $exitCode }
            }
        } catch {
            [PSCustomObject]@{
                Output = @($_ | Out-String)
                ExitCode = 1
            }
        }
    } -ArgumentList $claudePath, $PromptText

    $elapsed = 0
    $interval = 30
    $completed = $null
    while ($elapsed -lt $timeoutSec) {
        $completed = Wait-Job -Job $job -Timeout $interval
        if ($null -ne $completed) {
            break
        }
        $elapsed += $interval
        if ($elapsed -lt $timeoutSec) {
            Write-Host "       ...still running (elapsed: ${elapsed}s / timeout: ${timeoutSec}s)..." -ForegroundColor DarkGray
        }
    }

    if ($null -eq $completed) {
        Stop-Job -Job $job -ErrorAction SilentlyContinue | Out-Null
        Remove-Job -Job $job -Force -ErrorAction SilentlyContinue | Out-Null
        Write-Host "[FAIL] stage=claude-p timeout=${timeoutSec}s" -ForegroundColor Red
        return $null
    }

    $result = Receive-Job -Job $job
    Remove-Job -Job $job -Force -ErrorAction SilentlyContinue | Out-Null

    if ($null -eq $result) {
        Write-Host "[FAIL] stage=claude-p empty-result" -ForegroundColor Red
        return $null
    }

    $combinedOutput = @($result.Output) -join [Environment]::NewLine
    if ($result.ExitCode -ne 0) {
        if ($VerboseOutput -and -not [string]::IsNullOrWhiteSpace($combinedOutput)) {
            [Console]::Error.WriteLine($combinedOutput)
        }
        Write-Host "[FAIL] stage=claude-p exit=$($result.ExitCode)" -ForegroundColor Red
        return $null
    }

    return $combinedOutput
}

function Invoke-ClaudeAndWritePhase {
    param(
        [string]$TargetRun,
        [string]$ExpectedPhase,
        [string]$TargetFile,
        [string]$PromptText,
        [switch]$VerboseOutput
    )

    $targetPath = Resolve-RunFilePath -TargetRun $TargetRun -TargetFile $TargetFile
    $beforeState = Get-FileState -Path $targetPath

    Write-Host "  [2/3] invoke claude -p (tools disabled)..." -ForegroundColor DarkGray
    $claudeOutput = Invoke-ClaudePrompt -PromptText $PromptText -VerboseOutput:$VerboseOutput
    if ($null -eq $claudeOutput) {
        Write-Host "       [No File Written] $TargetFile was not saved. Phase is unchanged." -ForegroundColor Yellow
        Write-Host "       Check or retry: apsf next $TargetRun" -ForegroundColor DarkGray
        exit 1
    }
    if ([string]::IsNullOrWhiteSpace($claudeOutput)) {
        Write-Host "[FAIL] stage=claude-p empty-output" -ForegroundColor Red
        Write-Host "       [No File Written] Claude returned empty. $TargetFile was not saved. Phase is unchanged." -ForegroundColor Yellow
        Write-Host "       Check or retry: apsf next $TargetRun" -ForegroundColor DarkGray
        exit 1
    }

    $artifactCheck = Test-Artifact -Content $claudeOutput -TargetFile $TargetFile
    if (-not $artifactCheck.Valid) {
        Write-Host "[FAIL] stage=artifact-validation" -ForegroundColor Red
        Write-Host "       $($artifactCheck.Reason)" -ForegroundColor DarkGray
        Write-Host "       Claude returned commentary or an incomplete artifact; refusing to save." -ForegroundColor DarkGray
        exit 1
    }
    if ($artifactCheck.Level -eq "WARN" -and -not [string]::IsNullOrWhiteSpace($artifactCheck.Reason)) {
        Write-Host "[WARN] stage=artifact-validation" -ForegroundColor Yellow
        Write-Host "       $($artifactCheck.Reason)" -ForegroundColor DarkGray
    }
    
    $claudeOutput = $artifactCheck.CleanContent

    $phaseAfterClaude = Get-Phase $TargetRun
    if ($phaseAfterClaude -ne $ExpectedPhase) {
        $afterState = Get-FileState -Path $targetPath
        $targetChanged = ($beforeState.Exists -ne $afterState.Exists) -or ($beforeState.Hash -ne $afterState.Hash)

        if (-not $targetChanged) {
            Write-Host "  [3/3] phase advanced, but $TargetFile did not change." -ForegroundColor Yellow
            Write-Host "       phase=$phaseAfterClaude target=$TargetFile" -ForegroundColor DarkGray
            Write-Host "       This usually means Claude wrote some other file directly." -ForegroundColor DarkGray
            Write-Host "       Check: apsf next $TargetRun" -ForegroundColor DarkGray
            exit 1
        }

        Write-Host "  [3/3] skipped write-phase: claude wrote file directly (phase=$phaseAfterClaude)" -ForegroundColor DarkGray
        Write-Host ""
        Write-Host "[Done] $TargetFile saved by claude. Next: apsf next $TargetRun" -ForegroundColor Green
        Write-Host "[Note] Record any friction in fw-improvement-memo.md" -ForegroundColor DarkGray
        exit 0
    }

    Write-Host "  [3/3] write $TargetFile..." -ForegroundColor DarkGray
    $claudeOutput | apsf write-phase $TargetRun --stdin
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[FAIL] stage=write-phase ($TargetFile) exit=$LASTEXITCODE" -ForegroundColor Red
        Write-Host "       [No File Written] Failed to save output. $TargetFile was not updated. Phase is unchanged." -ForegroundColor Yellow
        Write-Host "       Check or retry: apsf next $TargetRun" -ForegroundColor DarkGray
        exit $LASTEXITCODE
    }
}

if ($UntilPlan) {
    $phase = Get-Phase $Run

    if ($phase -eq "GOAL_NEEDED") {
        Write-Host "[Stop] goal.md must be filled by Human before chaining." -ForegroundColor Yellow
        Write-Host "       target: runs/$Run/goal.md" -ForegroundColor DarkGray
        Write-Host "       check:  apsf next $Run" -ForegroundColor DarkGray
        exit 0
    }

    if ($DryRun) {
        Write-Host ""
        Write-Host "[DryRun] Chain mode: -UntilPlan" -ForegroundColor Yellow
        if ($phase -eq "SETUP_NEEDED") {
            Write-Host "  Step 1: apsf generate-setup $Run  ->  execution-assignment.md  [auto]" -ForegroundColor Yellow
        } else {
            Write-Host "  Step 1: (skipped) execution-assignment.md already filled (phase=$phase)" -ForegroundColor DarkGray
        }
        Write-Host "  Step 2: apsf act $Run             ->  plan.md                  [auto]" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "  Prerequisite : goal.md must be filled (Human-owned, cannot be automated)" -ForegroundColor DarkGray
        Write-Host "  Overwrite    : If execution-assignment.md already has content, Step 1 is skipped." -ForegroundColor DarkGray
        Write-Host "                 Use -Force to overwrite." -ForegroundColor DarkGray
        Write-Host ""
        Write-Host "[DryRun] No file saved. Remove -DryRun to execute." -ForegroundColor DarkGray
        exit 0
    }

    $specialist = Get-Specialist -TargetRun $Run -CurrentPhase $phase

    Write-Host ""
    Write-Host "[APSF] run:        $Run" -ForegroundColor Cyan
    Write-Host "[APSF] mode:       -UntilPlan" -ForegroundColor Cyan
    Write-Host "[APSF] cur phase:  $phase" -ForegroundColor Cyan
    Write-Host "[APSF] specialist: $specialist" -ForegroundColor Cyan
    Write-Host ""

    if ($phase -eq "SETUP_NEEDED") {
        Write-Host "[Step 1/2] generate-setup..." -ForegroundColor Cyan
        $generateSetupArgs = @($Run, "--print-prompt")
        if ($Force) {
            $generateSetupArgs += "--force"
        }

        Write-Host "  [1/3] generate setup prompt..." -ForegroundColor DarkGray
        $setupPrompt = & apsf generate-setup @generateSetupArgs
        if ($LASTEXITCODE -ne 0) {
            Write-Host "[FAIL] stage=generate-setup-prompt exit=$LASTEXITCODE" -ForegroundColor Red
            exit $LASTEXITCODE
        }
        if ([string]::IsNullOrWhiteSpace($setupPrompt)) {
            Write-Host "[Stop] apsf generate-setup returned empty output. Check phase:" -ForegroundColor Yellow
            Write-Host "       apsf next $Run" -ForegroundColor DarkGray
            exit 0
        }

        Invoke-ClaudeAndWritePhase -TargetRun $Run -ExpectedPhase "SETUP_NEEDED" -TargetFile "execution-assignment.md" -PromptText $setupPrompt -VerboseOutput:$VerboseOutput
        Write-Host "[Done] execution-assignment.md saved." -ForegroundColor Green
        Write-Host ""
    } else {
        Write-Host "[Step 1/2] skipped: execution-assignment.md already filled (phase=$phase)" -ForegroundColor DarkGray
        Write-Host ""
    }

    Write-Host "[Step 2/2] generate plan.md..." -ForegroundColor Cyan
    $phase2 = Get-Phase $Run
    if ($phase2 -ne "PLAN_NEEDED") {
        Write-Host "[Stop] Expected PLAN_NEEDED but got: $phase2" -ForegroundColor Yellow
        Write-Host "       Check run state: apsf next $Run" -ForegroundColor DarkGray
        exit 0
    }

    Write-Host "  [1/3] generate plan prompt..." -ForegroundColor DarkGray
    $planPrompt = Get-PromptWithRetry -TargetRun $Run -ExpectedPhase "PLAN_NEEDED"
    if ([string]::IsNullOrWhiteSpace($planPrompt)) {
        Write-Host "[Stop] apsf act returned empty output. Check phase:" -ForegroundColor Yellow
        Write-Host "       apsf next $Run" -ForegroundColor DarkGray
        exit 0
    }

    Invoke-ClaudeAndWritePhase -TargetRun $Run -ExpectedPhase "PLAN_NEEDED" -TargetFile "plan.md" -PromptText $planPrompt -VerboseOutput:$VerboseOutput
    Write-Host ""
    Write-Host "[Done] plan.md saved. Next: apsf next $Run" -ForegroundColor Green
    Write-Host "[Note] Record any friction in fw-improvement-memo.md" -ForegroundColor DarkGray
    exit 0
}

$phase = Get-Phase $Run
$targetFile = Get-WriteFile $Run
$nextLines = apsf next $Run 2>&1
$humanStop = $nextLines | Select-String -Pattern "Next Role\s*:.*Human"
$isHuman = $null -ne $humanStop
$specialist = Get-Specialist -TargetRun $Run -CurrentPhase $phase

Write-Host ""
Write-Host "[APSF] run:         $Run" -ForegroundColor Cyan
Write-Host "[APSF] next phase:  $phase" -ForegroundColor Cyan
Write-Host "[APSF] target file: $targetFile" -ForegroundColor Cyan
Write-Host "[APSF] specialist:  $specialist" -ForegroundColor Cyan
if ($isHuman) {
    Write-Host "[APSF] human stop:  true  (human-owned phase, no auto-exec)" -ForegroundColor Yellow
} else {
    Write-Host "[APSF] human stop:  false" -ForegroundColor Cyan
}
Write-Host ""

if ($isHuman) {
    Write-Host "[Stop] Human-owned phase. Edit the file directly." -ForegroundColor Yellow
    Write-Host "       target: .\\runs\\$Run\\$targetFile" -ForegroundColor DarkGray
    Write-Host "       check:  apsf next $Run" -ForegroundColor DarkGray
    exit 0
}

if ($phase -eq "BUILD_NEEDED") {
    Write-Host "[Stop] BUILD_NEEDED does not use 'act'." -ForegroundColor Yellow
    Write-Host "       Builder needs real file edits, so this phase must go through a tool-enabled build path." -ForegroundColor DarkGray
    Write-Host "       Run one of these instead:" -ForegroundColor DarkGray
    Write-Host "         1. .\\scripts\\apsf-wrapper-build.ps1 $Run -Backend claude-cli" -ForegroundColor DarkGray
    Write-Host "         2. .\\scripts\\apsf-wrapper-build.ps1 $Run -Backend codex-cli" -ForegroundColor DarkGray
    Write-Host "         3. apsf build $Run" -ForegroundColor DarkGray
    Write-Host "       act wrapper scope: PLAN_NEEDED and REVIEW_NEEDED only" -ForegroundColor DarkGray
    Write-Host "       check: apsf next $Run" -ForegroundColor DarkGray
    exit 1
}

if ($DryRun) {
    Write-Host "[DryRun] source: apsf act $Run --print-prompt" -ForegroundColor Yellow
    Write-Host "[DryRun] sink:   apsf write-phase $Run --stdin" -ForegroundColor Yellow
    Write-Host "[DryRun] target phase file: $targetFile" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "[DryRun] No file saved. Remove -DryRun to execute." -ForegroundColor DarkGray
    exit 0
}

Write-Host "[1/3] generate prompt..." -ForegroundColor DarkGray
$promptText = Get-PromptWithRetry -TargetRun $Run -ExpectedPhase $phase
if ([string]::IsNullOrWhiteSpace($promptText)) {
    Write-Host "[Stop] apsf act returned empty output. Check phase:" -ForegroundColor Yellow
    Write-Host "       apsf next $Run" -ForegroundColor DarkGray
    exit 0
}

Invoke-ClaudeAndWritePhase -TargetRun $Run -ExpectedPhase $phase -TargetFile $targetFile -PromptText $promptText -VerboseOutput:$VerboseOutput
Write-Host ""
Write-Host "[Done] $targetFile saved. Next: apsf next $Run" -ForegroundColor Green
Write-Host "[Note] Record any friction in fw-improvement-memo.md" -ForegroundColor DarkGray
