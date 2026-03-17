<#
.SYNOPSIS
    APSF × claude -p パイプ実行ラッパー

.DESCRIPTION
    `apsf act <run> --print-prompt | claude -p | apsf write-phase <run> --stdin`
    を 1 コマンドで実行する。

    PowerShell 5.1 のパイプ文字化けを防ぐため、実行前に UTF-8 エンコーディングを設定する。
    推奨: pwsh (PowerShell 7+) で実行すると設定不要。

.PARAMETER Run
    実行対象の run 名（例: 2026-03-17_my-case_my-topic）

.PARAMETER DryRun
    プロンプトを表示するだけで保存しない

.EXAMPLE
    # 1 フェーズ実行（Plan → Build → Review と繰り返し打つ）
    .\scripts\apsf-claude-act.ps1 2026-03-17_my-case_my-topic

.EXAMPLE
    # 実行前確認（プロンプト内容を確認したいとき）
    .\scripts\apsf-claude-act.ps1 2026-03-17_my-case_my-topic -DryRun
#>

param(
    [Parameter(Mandatory = $true, Position = 0)]
    [string]$Run,

    [switch]$DryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# ── UTF-8 設定（PowerShell 5.1 のパイプ文字化け対策）──────────────────────
# pwsh (7+) はデフォルト UTF-8 のため通常不要。5.1 では必須。
$OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# ── 前提チェック ─────────────────────────────────────────────────────────
if (-not (Get-Command "apsf" -ErrorAction SilentlyContinue)) {
    Write-Error "[Error] `apsf` が見つかりません。`pip install -e .` を実行してください。"
    exit 1
}

if (-not (Get-Command "claude" -ErrorAction SilentlyContinue)) {
    Write-Error "[Error] `claude` が見つかりません。Claude Code CLI をインストールしてください。"
    exit 1
}

# ── 現在の phase を確認 ───────────────────────────────────────────────────
Write-Host ""
Write-Host "Run : $Run" -ForegroundColor Cyan
apsf next $Run 2>&1 | Where-Object { $_ -match "Phase|Mode|Next Role|Write|Stop|Info" } | Write-Host
Write-Host ""

# ── DryRun: プロンプトのみ表示して終了 ──────────────────────────────────
if ($DryRun) {
    Write-Host "[DRY-RUN] Prompt preview:" -ForegroundColor Yellow
    Write-Host "─" * 60 -ForegroundColor DarkGray
    apsf act $Run --print-prompt 2>$null
    Write-Host "─" * 60 -ForegroundColor DarkGray
    Write-Host "[DRY-RUN] No file saved. Remove -DryRun to execute." -ForegroundColor Yellow
    exit 0
}

# ── パイプ実行 ────────────────────────────────────────────────────────────
Write-Host "[Run] apsf act $Run --print-prompt | claude -p | apsf write-phase $Run --stdin" -ForegroundColor DarkGray
Write-Host ""

$promptText = apsf act $Run --print-prompt 2>$null

if ([string]::IsNullOrWhiteSpace($promptText)) {
    # Human 担当フェーズ（[Stop] は stderr に出るため stdout は空）
    Write-Host "[Stop] Human 担当フェーズです。apsf next $Run で詳細を確認してください。" -ForegroundColor Yellow
    apsf next $Run
    exit 0
}

$promptText | claude -p | apsf write-phase $Run --stdin

if ($LASTEXITCODE -ne 0) {
    Write-Error "[Error] パイプ実行が失敗しました (exit $LASTEXITCODE)。"
    exit $LASTEXITCODE
}

Write-Host ""
Write-Host "[Done] 次のフェーズは: apsf next $Run" -ForegroundColor Green
