# CLI Orchestrator — 設計メモ

> **何か**: `apsf` CLI の Human-in-the-loop 支援コマンド群の責務・設計方針の記録。
> **いつ参照するか**: CLI コマンドの動作を確認するとき / 追加・変更の設計判断時。

---

## 全体責務

```
Human → apsf start-run → [run ディレクトリ作成]
Human → [goal.md を書く]
Human → apsf next      → [次ロールへの指示を表示]
  └→ AI / Human が指示を受け取り、該当ファイルを記入
  └→ apsf next を再実行して次フェーズへ進む
Human → apsf transcript → [transcript.md を自動生成]
```

`apsf` は Human の意思決定を代行しない。
何を書くかは Human と各 role が決める。
`apsf` は「今どこにいるか」と「何をすべきか」を整理して提示するだけである。

---

## コマンド一覧と責務

### `apsf start-run <name>`

**責務**: 新しい run ディレクトリを作成し、Human が goal.md を書き始められる状態にする。

- `runs/_template/` からファイルを一式コピーする
- 日付プレフィックスが省略されていれば今日の日付を自動付与する
- 作成したファイルの一覧を表示する
- goal.md を書くよう次アクションを案内する

**しないこと**:
- goal.md の本文を生成しない
- execution-assignment.md を自動で埋めない
- 「賢い」ことをしすぎず、骨格作成のみに集中する

**オプション**:
- `--dry-run`: 実際には作成せず、作成予定ファイルをプレビュー
- `--force` / `-f`: 既存ディレクトリを上書き

---

### `apsf next <run-name>`

**責務**: run の現在フェーズを推定し、次ロールにそのまま渡せる指示を表示する。

- `PhaseDetector` でファイル存在・充填状態からフェーズを推定する
- `NextInstructionBuilder` でフェーズ別の `short_instruction` + `detailed_instruction` を生成する
- 出力はあくまで「提案」であり、Human の判断を上書きしない

**重要: `next` は提案型である**

`apsf next` の出力は推定に基づく。以下の場合は誤検知が起きる可能性がある:
- ファイルに 4 行未満しか書いていない（充填済みと判定されない）
- テンプレートのコメント行だけ残っている
- v0.2 フローの optional ファイル（improve-plan.md / verify.md）が中途半端に存在する

迷ったら直接ファイルを確認すること。`apsf next` はあくまで出発点の提案である。

**オプション**:
- `--debug`: 判定根拠（existing / filled / unfilled / decision_reason）を追加表示

---

### `apsf write-phase <run-name>`

**責務**: 現在フェーズに対応する md を受け取り、正しいファイルへ保存する。

- `PhaseDetector` でフェーズを判定する
- `NextInstructionBuilder` で instruction を取得する
- 入力コンテンツを対象 md に保存する
- 保存後、`apsf next` を案内する

**`next` との責務分離**:

| | `apsf next` | `apsf write-phase` |
|---|---|---|
| 責務 | 案内 | 保存 |
| 出力 | instruction の表示 | ファイルへの書き込み |
| stdin 入力 | なし | あり |

**オプション**:
- `--print-prompt`: instruction テキストを stdout に出力して終了（保存しない）。外部 AI CLI へのパイプ用途。
- `--stdin`: 標準入力からコンテンツを受け取る（対話プロンプトなし）。パイプやリダイレクトで使用。
- `--dry-run`: 保存先を確認するだけ（実際には保存しない）
- `--force` / `-f`: 既存の meaningful content を上書き

**安全性**:
- 対象ファイルに meaningful content が既にある場合、デフォルトでは上書きしない（`--force` 必要）
- `--force --stdin` で上書きするとき、stderr に `[Warn] Overwriting <file> (current phase target)` を表示する
- 空入力・空白のみ・テンプレート骨格のみは保存しない
- `transcript.md` は対象外（`apsf transcript` コマンドを使うこと）

**stdout/stderr 責務**:

```
stdout: instruction テキスト（--print-prompt / 対話モード）← パイプ先 AI が読む内容
stderr: ヘッダー・Saving to・[Saved]・[Next] など UI メッセージ
```

`write-phase --stdin` の stdout は空であることが保証されている。
外部 AI CLI との連携でパイプの末尾に置いても stdout を汚染しない。

**`apsf act` との関係**:

```
# API なし（パイプ運用）
apsf act <run> --print-prompt | <ai-cli> | apsf write-phase <run> --stdin

# API あり（自動実行）
apsf act <run>   ← LLM を呼び出して自動生成・保存
```

`write-phase` は "台車" である。API の有無にかかわらず、
生成コンテンツを正しいフェーズファイルへ着地させる役割を持つ。

---

### `apsf act <run-name>`

**責務**: 現在フェーズを判定し、LLM を呼び出して phase 文書を自動生成・保存する。

- Human 担当フェーズ（goal.md / improve.md 等）では停止し、何も生成しない
- Auto 担当フェーズ（plan.md / build.md / review.md）のみ実行する
- 1 回の実行で 1 phase だけを処理する（v0.1 設計）

**オプション**:
- `--print-prompt`: LLM に渡すプロンプトを stdout のみに出力して終了。外部 AI CLI へのパイプに使用。
- `--dry-run`: フェーズ情報とプロンプト全文を表示するだけ（LLM 呼び出しなし）
- `--force` / `-f`: 既存コンテンツを上書き

**Human 停止ルール**（`HUMAN_OWNED_PHASES`）:

| フェーズ | 理由 |
|---|---|
| SETUP_NEEDED | execution-assignment.md は Human が設計する |
| GOAL_NEEDED | goal.md は Human のみが定義できる |
| IMPROVE_NEEDED | Judge 判断は Human が行う（v0.1） |
| IMPROVE_PLAN_OPTIONAL | スコープ定義は Human（v0.2） |
| VERIFY_OPTIONAL | 完了条件確認は Human（v0.2） |
| RESULT_NEEDED | 振り返りは Human が書く |
| COMPLETE | 完了済み、何もしない |

**Auto 実行ルール**（`AUTO_OWNED_PHASES`）:

| フェーズ | Role | 出力 |
|---|---|---|
| PLAN_NEEDED | Planner | plan.md |
| BUILD_NEEDED | Builder | build.md |
| REVIEW_NEEDED | Critic | review.md |

**`--print-prompt` の stdout 契約**:

Human 停止フェーズでは stdout に何も出力しない（stderr に `[Stop]` メッセージ）。
Auto フェーズではプロンプトテキストのみを stdout に出力する（ヘッダー等は stderr）。

```bash
# stdout: プロンプトテキストのみ（ノイズゼロ）
apsf act <run> --print-prompt 2>/dev/null

# stderr: Human 停止メッセージ
apsf act <run> --print-prompt 2>&1 1>/dev/null
# → [Stop] Human phase (IMPROVE_NEEDED): ...
```

---

### `apsf transcript <run-name>`

**責務**: run ディレクトリ内の一次記録ファイルを所定順に連結し、`transcript.md` を自動生成する。

- `TranscriptGenerator` が `TRANSCRIPT_SOURCE_ORDER` に従って処理する
- 存在しないファイルはスキップ（v0.2 の optional ファイルも同様）
- `transcript.md` 自身は入力対象としない（再帰読み込みの防止）

**transcript は正式フェーズではない**:

```
Goal → Plan → Build → Review → Improve → Result
                                              ↓ (optional)
                                          [Transcript]
```

`transcript.md` は二次成果物である。一次記録（goal.md〜result.md）の可読化ツールであり、
逐語ログでも会話の再現でもない。正確な情報は一次記録を参照すること。

---

## パイプ運用フロー

`apsf act --print-prompt | <ai-cli> | apsf write-phase --stdin` を核とした
「API なし・パイプ運用」が APSF v0.2 の推奨フローである。

```
[Human] goal.md / execution-assignment.md を記入
   ↓
apsf act <run> --print-prompt 2>/dev/null   # stdout にプロンプト
   ↓ pipe
<ai-cli>                                     # 応答を stdout に出力
   ↓ pipe
apsf write-phase <run> --stdin               # stdin から読んで保存
   ↓
apsf next <run>                              # IMPROVE_NEEDED → Human 停止
```

**3 フェーズのワンパターン実行**:

```bash
RUN=YYYY-MM-DD_case_topic

# Plan
apsf act $RUN --print-prompt 2>/dev/null | <ai-cli> | apsf write-phase $RUN --stdin

# Build
apsf act $RUN --print-prompt 2>/dev/null | <ai-cli> | apsf write-phase $RUN --stdin

# Review
apsf act $RUN --print-prompt 2>/dev/null | <ai-cli> | apsf write-phase $RUN --stdin

# → apsf next $RUN で IMPROVE_NEEDED になり Human 停止
```

同じコマンドパターンでフェーズが自動進行する。

---

## 外部 AI CLI 互換表

APSF のパイプ運用で `<ai-cli>` として使えるツールの評価。

**互換性の要件（dumb pipe として機能するか）**:
- stdin でプロンプトを受け取れる
- stdout に応答テキストだけを出せる（ヘッダーやステータスを含まない）
- ファイル操作・tool call 等のアジェンティック挙動に流れない

| CLI | 評価 | stdin 受付 | stdout clean | non-agentic | 備考 |
|---|---|---|---|---|---|
| `llm` | ✅ **推奨** | ✅ | ✅ | ✅ | Simon Willison 製。pure text I/O 前提の設計。`pip install llm` |
| `claude -p` | △ **条件付き採用可** | ✅ | ✅ | ✅ | **Claude Code セッション内からは不可**。通常 PowerShell（pwsh 推奨）で 3 phase 完走確認済み。PS 5.1 は UTF-8 設定必要。ラッパー: `scripts/apsf-claude-act.ps1` |
| `codex` | ❌ 非推奨 | ✅ | ❌ | ❌ | アジェンティックモード。ファイル読み書き・shell コマンド実行を行い、stdout はヘッダー+ツール出力で汚染される。`-o FILE` は最後のメッセージ（確認文）のみ。APSF パイプ不成立。 |
| `gemini -p ""` | ❌ 非推奨 | ✅ | ❌ | ❌ | アジェンティックモードで動作。stdout は conversational text のみ（"I will create..."）。`write_file` tool を呼ぼうとして失敗。 |

### Windows での推奨実行環境

**Windows では `pwsh`（PowerShell 7+）を推奨する。**

| 環境 | 状態 | 理由 |
|---|---|---|
| `pwsh` (PowerShell 7+) | ✅ 推奨 | パイプでバイト列を直接渡す。UTF-8 設定不要。 |
| Windows PowerShell 5.1 | △ 条件付き | パイプ通過時に文字コード変換が発生。UTF-8 設定が必要。 |
| Git Bash / WSL | ✅ 使用可 | Unix 系動作のため UTF-8 問題なし。 |

**PowerShell 7+ のインストール**:

```powershell
winget install Microsoft.PowerShell
# または: https://github.com/PowerShell/PowerShell/releases
```

**PowerShell 5.1 を使う場合（やむを得ない場合）**:

```powershell
# セッション開始時に 1 回設定（$PROFILE に書くと毎回不要）
$OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
```

---

### 推奨: `llm`

```bash
pip install llm
llm keys set anthropic   # または: llm keys set openai / gemini

# 使用例
apsf act $RUN --print-prompt 2>/dev/null | llm | apsf write-phase $RUN --stdin
```

Simon Willison の `llm` ツールは stdin → stdout の純テキスト生成に特化しており、
APSF のパイプ設計と最も相性が良い。

### `codex` 評価結果（2026-03-17 検証済み）

`codex exec -` で stdin 受付は可能だが、**アジェンティックモード**で動作するため APSF パイプには不適。

| 観点 | 結果 | 詳細 |
|---|---|---|
| stdin 受付 | ✅ | `cat prompt.txt \| codex exec - --skip-git-repo-check` で受付確認 |
| non-interactive 実行 | ✅ | `codex exec` サブコマンドで非対話モード確認 |
| stdout clean | ❌ | ヘッダー + tool call 出力 + tokens used がすべて stdout/stderr に混在 |
| non-agentic 挙動 | ❌ | `Get-ChildItem`, `Get-Content`, `apply_patch` を自動実行。plan.md をルートに生成 |
| APSF パイプ相性 | ❌ | `-o FILE` の内容は「Created plan.md...」の確認文のみ。plan 本文は filesystem に書かれる |

**根本的問題**: codex はプロンプトに応じてファイルを読み・書くエージェントとして動作する。
APSF が求める「プロンプト in → テキスト応答 out」の dumb pipe モデルとは設計が異なる。

**`--sandbox read-only` について**: フラグ自体は受け付けるが、ファイル書き込みを防いでも
`-o FILE` の内容が確認文のみになる問題は解決しない。plan 本文を stdout に返す動作にならない。

---

### `claude -p` 評価状況（2026-03-17）

#### 確認済み（通常 PowerShell）

```powershell
# 最小疎通確認 ✅
"Reply with exactly: PIPE_OK" | claude -p
# → PIPE_OK（stdout clean・non-interactive・stdin 受付）
```

#### 確認済み（Claude Code セッション内 — ブロック）

```bash
# nested session ブロック ❌
echo "..." | claude -p
# → Error: Claude Code cannot be launched inside another Claude Code session.

# env -u CLAUDECODE による回避 — ハングのため廃止
echo "..." | env -u CLAUDECODE claude -p
# → 応答なし（タイムアウト）
# → Claude Code 内からの claude -p 呼び出しは正式ルートとしない
```

#### 実測結果（通常 PowerShell — 外部端末）

Plan / Build / Review / IMPROVE_NEEDED の 3 フェーズ完走を確認:

```powershell
# 事前設定（PowerShell 5.1 の場合のみ必須）
$OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# 3 phase ループ
apsf act $RUN --print-prompt 2>$null | claude -p | apsf write-phase $RUN --stdin  # Plan
apsf act $RUN --print-prompt 2>$null | claude -p | apsf write-phase $RUN --stdin  # Build
apsf act $RUN --print-prompt 2>$null | claude -p | apsf write-phase $RUN --stdin  # Review
apsf next $RUN  # → IMPROVE_NEEDED（Human 停止）
```

**フロー結果**: ✅ パイプ成立・フェーズ自動進行・Human 停止 すべて正常

**文字化け問題**: 事前設定なしで実行した場合、PowerShell 5.1 のパイプ変換により日本語が文字化けする
（詳細: 下記「Windows + PowerShell の UTF-8 注意事項」参照）。

#### 最終評価

**△ 条件付き採用可**

| 条件 | 状態 |
|---|---|
| Claude Code セッション外（通常 PowerShell / Terminal） | 必須 |
| PowerShell 7+ (pwsh) | UTF-8 デフォルト。事前設定不要 ✅ **推奨** |
| PowerShell 5.1 | 事前に `$OutputEncoding` + `[Console]::OutputEncoding` の UTF-8 設定が必要 |
| Claude Code セッション内 | 不可（nested session ブロック。`env -u CLAUDECODE` 回避もハング） |

#### 実運用ラッパー

毎回コマンドを打つかわりに `scripts/apsf-claude-act.ps1` を使う:

```powershell
# 1 フェーズ実行（UTF-8 設定・Human 停止チェック込み）
.\scripts\apsf-claude-act.ps1 2026-03-17_my-case_my-topic

# プロンプト確認のみ（保存しない）
.\scripts\apsf-claude-act.ps1 2026-03-17_my-case_my-topic -DryRun
```

---

## stdio 設計原則

APSF の stdio 設計は成立している。実運用の成否は **外部 AI CLI の特性** に依存する。

```
stdout の責務: 有用なコンテンツ（プロンプトテキスト / instruction）
stderr の責務: UI メッセージ（ヘッダー・[Saved]・[Next] 等）
```

このため、APSF の標準フローは「互換 CLI 前提」で定義する:

- `apsf act --print-prompt` の stdout はノイズゼロが保証されている
- `apsf write-phase --stdin` の stdout は空が保証されている（パイプ透過）
- Human 停止フェーズでは `--print-prompt` の stdout も空（[Stop] は stderr のみ）

**APSF 側の問題ではなく、外部 CLI 側の問題**であることが dogfood で確認された:

> `gemini -p ""` は agentic モードで tool call に流れ、stdout に文書コンテンツが出ない。
> `codex exec -` も agentic モードで動作し、ファイルを読み書きする。stdout はヘッダー混在。
> `claude -p` は Claude Code セッション内では nested session ブロックが発動する。
> APSF の stdio / phase orchestration 設計は正しく動作している。

---

## Windows + PowerShell の UTF-8 注意事項

### 問題の構造

PowerShell 5.1（Windows PowerShell）はパイプ通過時に外部プロセスの stdout を
**文字列として仲介**する。このときのエンコーディングが UTF-8 でないと文字化けする:

```
AI CLI (UTF-8 出力)
  → PowerShell 5.1 が [Console]::OutputEncoding (cp932) でデコード  ← ここで壊れる
  → PowerShell 5.1 が $OutputEncoding (ASCII/cp932) で再エンコード
  → apsf write-phase --stdin が受け取るバイト列は UTF-8 ではない
  → 日本語が文字化け
```

PowerShell 7+ (`pwsh`) はパイプで生バイト列を渡す（文字列変換なし）ため、この問題は発生しない。

### 修正方法

#### 方法 A（推奨）: PowerShell 7+ を使う

```powershell
# PowerShell 7+ のインストール確認
pwsh --version

# 7+ セッションで実行（文字化けなし）
pwsh -Command 'apsf act $env:RUN --print-prompt 2>$null | claude -p | apsf write-phase $env:RUN --stdin'
```

#### 方法 B: PowerShell 5.1 で事前設定

```powershell
# セッション開始時に 1 回だけ実行（プロファイルに書いておくと毎回不要）
$OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# 設定確認
$OutputEncoding.EncodingName       # → "Unicode (UTF-8)" と出るべき
[Console]::OutputEncoding.EncodingName  # → "Unicode (UTF-8)" と出るべき
```

#### 方法 C: $PROFILE に永続化（PS 5.1 ユーザー向け）

```powershell
# $PROFILE を編集して起動時に自動設定
Add-Content $PROFILE "`n`$OutputEncoding = [System.Text.Encoding]::UTF8"
Add-Content $PROFILE "`n[Console]::OutputEncoding = [System.Text.Encoding]::UTF8"
```

### APSF 側のフォールバック動作

`apsf write-phase --stdin` が UTF-8 でないバイト列を受け取った場合:

```
[Warn] stdin のデコードに失敗しました（UTF-8 ではないバイト列を検出）。
       PowerShell 5.1 のパイプエンコーディング変換が原因の可能性があります。
       ...（修正コマンドが表示される）...
       cp932 でフォールバックデコードして続行します（文字化けの可能性あり）。
```

クラッシュせずにフォールバックデコードして保存するが、**正しい文字で保存されるとは限らない**。
根本解決は PowerShell 側のエンコーディング設定にある。

---

## Human と CLI の責務分離

| 責務 | Human | CLI |
|---|---|---|
| 何を解くかを決める | **Human** | CLI は問わない |
| run を開始する | `apsf start-run` を呼ぶ | ディレクトリ作成・ファイルコピー |
| goal.md を書く | **Human** が書く | CLI は生成しない |
| 各ロールの指示を受け取る | `apsf next` で確認 | フェーズ推定・指示文生成 |
| build.md / review.md などを書く | **各ロール** が書く | CLI は内容を生成しない |
| 採用・却下を判断する | **Human (Judge)** | CLI は判断しない |
| transcript を生成する | `apsf transcript` を呼ぶ | ファイル連結・整形 |

---

## フェーズ判定のルール（PhaseDetector）

判定基準: ファイルの存在 + 充填状態（`_is_filled`）

```
充填済み = コメント行・見出し行・区切り行を除いて 4 行以上ある
```

フェーズ判定順序（waterfall）:
```
SETUP_NEEDED          ← execution-assignment.md が未充填
GOAL_NEEDED           ← goal.md が未充填
PLAN_NEEDED           ← plan.md が未充填
IMPROVE_PLAN_OPTIONAL ← improve-plan.md が存在・未充填（v0.2）
BUILD_NEEDED          ← build.md が未充填
REVIEW_NEEDED         ← review.md が未充填
IMPROVE_NEEDED        ← improve.md が未充填
VERIFY_OPTIONAL       ← verify.md が存在・未充填（v0.2）
RESULT_NEEDED         ← result.md が未充填
TRANSCRIPT_RECOMMENDED← transcript.md が未充填
COMPLETE              ← 全ファイル充填済み
```

IMPROVE_PLAN_OPTIONAL / VERIFY_OPTIONAL はファイルが存在する場合のみ発動する。
v0.1 フロー（これらのファイルを使わない）では検出されない。

---

## 実装ファイル

| ファイル | 責務 |
|---|---|
| `src/apsf/cli/main.py` | CLI コマンド定義・表示ロジック |
| `src/apsf/orchestration/phase_detector.py` | フェーズ推定ロジック |
| `src/apsf/orchestration/next_instruction_builder.py` | フェーズ別指示文生成 |
| `src/apsf/orchestration/transcript_generator.py` | transcript.md 生成ロジック |
| `src/apsf/storage/run_repository.py` | run ディレクトリの作成・管理 |

CLI 表示ロジックと instruction 生成ロジックは分離されている。
`NextInstructionBuilder` は CLI に依存せず、単独でテスト可能。

---

*このファイルは設計の説明文書です。コードと乖離が生じたらコードを優先してください。*
