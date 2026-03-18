<#
.SYNOPSIS
    APSF × claude -p パイプ実行ラッパー

.DESCRIPTION
    `apsf act <run> --print-prompt | claude -p | apsf write-phase <run> --stdin`
    を 1 コマンドで実行する。

    実行前に現在の phase を表示し、3 ステージそれぞれで進捗と失敗箇所を明示する。
    PowerShell 5.1 の文字化けを防ぐため UTF-8 エンコーディングを事前設定する。
    推奨: pwsh (PowerShell 7+) で実行すると設定不要。

.PARAMETER Run
    実行対象の run 名（例: 2026-03-18_my-case_my-topic）

.PARAMETER DryRun
    保存は行わず、実行内容と上書きリスクを表示して終了する

.EXAMPLE
    # 1 フェーズ実行（Plan → Build → Review と繰り返し打つ）
    .\scripts\apsf-claude-act.ps1 2026-03-18_my-case_my-topic

.EXAMPLE
    # 実行前確認（保存しない）
    .\scripts\apsf-claude-act.ps1 2026-03-18_my-case_my-topic -DryRun
#>

param(
    [Parameter(Mandatory = $true, Position = 0)]
    [string]$Run,

    [switch]$DryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# ── UTF-8 設定（PowerShell 5.1 の文字化け対策）──────────────────────────
# pwsh 7+ はデフォルト UTF-8 のため設定は無害。PS 5.1 では必須。
$OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# ── 前提チェック ─────────────────────────────────────────────────────────
if (-not (Get-Command "apsf" -ErrorAction SilentlyContinue)) {
    Write-Host "[Error] 'apsf' が見つかりません。pip install -e . を実行してください。" -ForegroundColor Red
    exit 1
}
if (-not (Get-Command "claude" -ErrorAction SilentlyContinue)) {
    Write-Host "[Error] 'claude' が見つかりません。Claude Code CLI をインストールしてください。" -ForegroundColor Red
    exit 1
}

# ── phase 情報を apsf next から取得 ──────────────────────────────────────
$nextLines = apsf next $Run 2>&1

$phaseMatch  = $nextLines | Select-String -Pattern "Phase\s*:\s*(\S+)"
$writeMatch  = $nextLines | Select-String -Pattern "Write\s*:\s*(\S+\.md)"
$humanStop   = $nextLines | Select-String -Pattern "\(Human\)"

$phase      = if ($phaseMatch)  { $phaseMatch.Matches[0].Groups[1].Value }  else { "UNKNOWN" }
$targetFile = if ($writeMatch)  { $writeMatch.Matches[0].Groups[1].Value }  else { "unknown" }
$isHuman    = $null -ne $humanStop

# ── runs ディレクトリ解決（APSF_ROOT 環境変数 or CWD 基準）──────────────
$runsBase = if ($env:APSF_ROOT) { Join-Path $env:APSF_ROOT "runs" } else { ".\runs" }
$targetPath = Join-Path $runsBase "$Run\$targetFile"

# ── 実行前サマリ ─────────────────────────────────────────────────────────
Write-Host ""
Write-Host "[APSF] run:        $Run"       -ForegroundColor Cyan
Write-Host "[APSF] next phase: $phase"     -ForegroundColor Cyan
Write-Host "[APSF] target file: $targetFile" -ForegroundColor Cyan
$humanLabel = if ($isHuman) { "true  ← Human 担当。実行不要。" } else { "false" }
$humanColor = if ($isHuman) { "Yellow" } else { "Cyan" }
Write-Host "[APSF] human stop: $humanLabel" -ForegroundColor $humanColor
Write-Host ""

# ── Human 担当フェーズは停止 ─────────────────────────────────────────────
if ($isHuman) {
    Write-Host "[Stop] Human 担当フェーズです。ファイルを直接編集してください。" -ForegroundColor Yellow
    Write-Host "       target: $targetPath" -ForegroundColor DarkGray
    Write-Host "       確認:   apsf next $Run" -ForegroundColor DarkGray
    exit 0
}

# ── DryRun ───────────────────────────────────────────────────────────────
if ($DryRun) {
    $hasContent = (Test-Path $targetPath) -and ((Get-Content $targetPath -Raw -ErrorAction SilentlyContinue) -match '\S')
    $overwriteRisk = if ($hasContent) { "yes  ← $targetFile には既存コンテンツあり" } else { "no" }
    $riskColor = if ($hasContent) { "Yellow" } else { "DarkGray" }

    Write-Host "[DryRun] source: apsf act $Run --print-prompt" -ForegroundColor Yellow
    Write-Host "[DryRun] sink:   apsf write-phase $Run --stdin" -ForegroundColor Yellow
    Write-Host "[DryRun] target phase file: $targetFile" -ForegroundColor Yellow
    Write-Host "[DryRun] overwrite risk: $overwriteRisk" -ForegroundColor $riskColor
    Write-Host ""
    Write-Host "[DryRun] No file saved. Remove -DryRun to execute." -ForegroundColor DarkGray
    exit 0
}

# ── ステージ実行 ─────────────────────────────────────────────────────────

# [1/3] prompt 生成
Write-Host "[1/3] generate prompt..." -ForegroundColor DarkGray
$promptText = apsf act $Run --print-prompt 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "[FAIL] stage=generate-prompt exit=$LASTEXITCODE" -ForegroundColor Red
    exit $LASTEXITCODE
}
if ([string]::IsNullOrWhiteSpace($promptText)) {
    # Human フェーズの二重チェック（apsf next の parse ミス対策）
    Write-Host "[Stop] apsf act が空を返しました。Human フェーズか phase 未確定の可能性があります。" -ForegroundColor Yellow
    Write-Host "       確認:   apsf next $Run" -ForegroundColor DarkGray
    exit 0
}

# [2/3] claude -p 呼び出し
Write-Host "[2/3] invoke claude -p..." -ForegroundColor DarkGray
$claudeOutput = $promptText | claude -p
if ($LASTEXITCODE -ne 0) {
    Write-Host "[FAIL] stage=claude-p exit=$LASTEXITCODE" -ForegroundColor Red
    exit $LASTEXITCODE
}

# [3/3] write-phase --stdin 保存
Write-Host "[3/3] write phase..." -ForegroundColor DarkGray
$claudeOutput | apsf write-phase $Run --stdin
if ($LASTEXITCODE -ne 0) {
    Write-Host "[FAIL] stage=write-phase exit=$LASTEXITCODE" -ForegroundColor Red
    exit $LASTEXITCODE
}

Write-Host ""
Write-Host "[Done] $targetFile saved. Next: apsf next $Run" -ForegroundColor Green
Write-Host "[Note] Record any friction in fw-improvement-memo.md" -ForegroundColor DarkGray
