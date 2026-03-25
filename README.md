# AI Problem Solving Framework (APSF)

> AIを使った問題解決プロセスを一般化・再利用可能にするフレームワーク

---

## このプロジェクトの目的

「AIを使ってコードを書く」ためのツールではない。

**AIを役割ごとに組み合わせて、問題解決の進め方そのものを再利用可能な型として保存すること**が目的である。

ドメインが変わっても、チームが変わっても、使うAIモデルが変わっても、
同じ問題解決ループを回せる構造を目指す。

---

## マルチモデル運用前提

このフレームワークは単一AIへの依存を前提としない。

```
Planner    → 人間 + OpenAI (GPT-4o)
JuniorBuilder → Gemini (Flash)
Builder    → Anthropic (Claude Sonnet)
Critic     → OpenAI (GPT-4o) — Builder と別系統で運用
Judge      → 人間
```

**role と provider を分離する**ことがこのフレームワークの設計核心。
`ClaudeBuilder` のような密結合は作らない。
どの role に何を使うかは run ごとに `model-assignment.md` で定義する。

詳細: [`framework/operating-model.md`](framework/operating-model.md)

---

## なぜ SoChi BLOCKS が最初の実験環境なのか

SoChi BLOCKS はブロック系パズルゲームを中心とした Web プロダクトで、
以下の理由からフレームワークの最初の検証場として最適である。

- **マルチドメイン**: Engineering / Design / Algorithm / Content / Marketing を含む
- **ミニスタートアップ構造**: 1〜少人数で全レイヤーを担当する現実がある
- **課題が具体的**: 直帰率・UX・パズル品質など実際の問題が積み上がっている
- **フィードバックが速い**: 小規模ゆえに変更の効果を素早く確認できる
- **失敗コストが低い**: 試行錯誤がしやすい

ただし **SoChi BLOCKS 専用設計ではなく、SoChi BLOCKS から始める汎用問題解決 OS** として設計する。

---

## ディレクトリ構成

```
ai-problem-solving-framework/
├── README.md                    # このファイル
├── pyproject.toml               # Python プロジェクト設定
├── .env.example                 # 環境変数サンプル
├── framework/                   # フレームワーク設計資産（ドメイン非依存）
│   ├── overview.md              # 全体像・設計思想
│   ├── operating-model.md       # マルチモデル運用モデル
│   ├── workflow/v0.1.md         # ワークフロー定義
│   ├── agents/                  # 各 role の責務・プロンプト草案
│   └── templates/               # 各ステップのひな型（設計資産・原本）
├── cases/                       # ドメイン固有の知識
│   └── sochi-blocks/            # 最初の検証ケース
├── runs/                        # 実行ログ（1フォルダ = 1 problem solving cycle）
│   ├── README.md
│   └── _template/               # 新しい run を切るときにコピーする
└── src/apsf/                    # Python 実行基盤
    ├── config/                  # 設定・環境変数
    ├── domain/                  # ドメインモデル（Role / Provider / RunContext 等）
    ├── providers/               # API接続層（OpenAI / Anthropic / Gemini）
    ├── agents/                  # 各 role の実装
    ├── prompts/                 # プロンプト読み込み・レンダリング
    ├── storage/                 # Markdown read/write / run 管理
    ├── orchestration/           # pipeline / assignment / handoff
    └── cli/                     # CLI エントリポイント
```

---

## 使い始め方

### 1. 環境構築

```bash
cp .env.example .env
# .env に各 API キーを記入する

pip install -e ".[dev]"
# または: uv pip install -e ".[dev]"
```

### 2. 環境確認

```bash
apsf check-env
```

### 3. フレームワーク構造の確認

```bash
apsf show-structure
```

### 4. 最初の run を作る

```bash
apsf start-run sochi-blocks_sns-post-template
# → 日付+連番が自動付与される: 2026-03-15-001_sochi-blocks_sns-post-template
```

### 5. パイプ運用を使う場合は LLM CLI を用意する（オプション）

`apsf act --print-prompt | <ai-cli> | apsf write-phase --stdin` のパイプ運用を使うには、
**stdin からプロンプトを受け取り、stdout に応答テキストだけを出力できる LLM CLI** が必要。

**なぜ必要か**: APSF は phase 管理・prompt 生成・ファイル保存を担う。
AI によるテキスト生成の部分は外部 CLI に委ねる設計のため。

**現時点の推奨: `llm`**

```bash
pip install llm
llm keys set anthropic   # または: llm keys set openai / gemini
```

セットアップ後:

```bash
RUN=2026-03-17_my-case_my-topic

# Plan / Build / Review を同じパターンで実行（フェーズ自動進行）
apsf act $RUN --print-prompt 2>/dev/null | llm | apsf write-phase $RUN --stdin
apsf act $RUN --print-prompt 2>/dev/null | llm | apsf write-phase $RUN --stdin
apsf act $RUN --print-prompt 2>/dev/null | llm | apsf write-phase $RUN --stdin

# → apsf next $RUN で IMPROVE_NEEDED になり Human 停止
```

**比較対象の AI CLI**（検証済み）:

| CLI | 状態 | 備考 |
|---|---|---|
| `llm` | ✅ 推奨 | `pip install llm`。pure text I/O。 |
| `claude -p` | △ 条件付き | 通常 PowerShell（`pwsh` 推奨）で 3 phase 完走確認済み。Claude Code セッション内からは不可。PS 5.1 は UTF-8 設定が必要。ラッパー: `scripts/apsf-claude-act.ps1` |
| `codex` | ❌ 非推奨 | agentic モードで動作し、ファイルを読み書きする。stdout にヘッダー混在。APSF パイプ不成立。 |
| `gemini -p ""` | ❌ 非推奨 | agentic モードで動作し stdout に応答本文が出ない。 |

詳細: [`framework/cli-orchestrator.md`](framework/cli-orchestrator.md)

**Windows での推奨実行環境**:

| 環境 | 推奨度 | 備考 |
|---|---|---|
| `pwsh`（PowerShell 7+） | ✅ **推奨** | UTF-8 デフォルト。設定不要。`winget install Microsoft.PowerShell` |
| Windows PowerShell 5.1 | △ | 事前に `$OutputEncoding` + `[Console]::OutputEncoding` の UTF-8 設定が必要 |
| Git Bash / WSL | ✅ 使用可 | Unix 系動作のため UTF-8 問題なし |

**`claude -p` を使う場合のラッパースクリプト**（UTF-8 設定・Human 停止チェック込み）:

```powershell
# 1 フェーズ実行
.\scripts\apsf-claude-act.ps1 2026-03-17_my-case_my-topic

# 確認のみ（保存しない）
.\scripts\apsf-claude-act.ps1 2026-03-17_my-case_my-topic -DryRun
```

LLM CLI なしでも `apsf act <run> --print-prompt` でプロンプトを取得し、
任意の AI ツールに手動で貼り付けてから `apsf write-phase <run> --stdin` で保存できる。

---

### ⚠️ Build & Re-build — BUILD_NEEDED フェーズは別スクリプト

Builder は **ファイルへの実アクセス** が必要なため、PLAN/REVIEW に使う `apsf-claude-act.ps1`（tools: disabled）は BUILD_NEEDED に使えない。

#### Phase Routing Table

| Phase | コマンド | Tool Access | スクリプト |
|---|---|---|---|
| PLAN_NEEDED | `apsf act <run>` | **無効** | `apsf-claude-act.ps1` |
| REVIEW_NEEDED | `apsf act <run>` | **無効** | `apsf-claude-act.ps1` |
| BUILD_NEEDED | `apsf build <run>` | **有効** | `apsf-claude-build.ps1` |

#### 基本的な使い方

```powershell
$run = "<run-name>"

# 通常: plan.md + build_review.md（あれば）を自動収集して claude を起動
.\scripts\apsf-claude-build.ps1 $run

# プロンプト確認のみ（claude は起動しない）
.\scripts\apsf-claude-build.ps1 $run -DryRun

# カスタムプロンプトを使う場合
.\scripts\apsf-claude-build.ps1 $run -PromptFile path\to\custom.md
```

#### Re-build（build_review.md がある場合）

`build_review.md` が run ディレクトリにある場合、`apsf-claude-build.ps1` は自動的に
plan.md に追記してから claude を起動する。別途指定不要。

```
runs/<run-name>/
  plan.md           ← 必須（Builder のメイン入力）
  build_review.md   ← オプション（Re-build 指示。存在すれば自動収集）
```

#### Fallback（直接 claude を使う場合）

```powershell
claude --tools Bash,Edit,Glob,Grep,Read,Write
```

詳細: [`framework/agents/builder.md`](framework/agents/builder.md)

---


### 6. goal.md を書いてループを開始する

```
runs/2026-03-15_sochi-blocks_sns-post-template/
  model-assignment.md  ← 最初にどの role に何を使うかを決める
  goal.md              ← 次に何を解くかを書く
  plan.md              ← Planner が作成
  build.md             ← Builder が作成
  review.md            ← Critic が作成
  improve.md           ← 人間が判断
  result.md            ← ループ完了時に記録
  handoff.md           ← role 間の受け渡し記録
```

---

## v0.1 / v0.2 でできること

| 機能 | v0.1 | v0.2 |
|---|---|---|
| Markdown ベースのループ運用 | ✅ | |
| CLI で run 初期化・フェーズ管理 | ✅ | |
| multi-model assignment 定義 | ✅（手動） | |
| `apsf act` による phase 自動生成 | ✅ | |
| `--print-prompt` / `--stdin` パイプ運用 | ✅ | |
| stdout/stderr 分離（pipe 透過設計） | ✅ | |
| Improve Plan / Verify オプションフェーズ | ✅（手動作成時のみ） | |
| 互換 LLM CLI による完全自動パイプ | △（`llm` 設定が必要） | ✅ 標準フロー化 |
| Judge による自動評価 | ❌ | 候補 |
| 並列 Build 比較 | ❌ | ✅ |

---

## 今後の発展方針

| バージョン | 主な追加 |
|---|---|
| v0.1 | Markdown基盤・multi-model骨格・CLI・SoChi BLOCKSケース |
| v0.2 | 実API接続・Judge独立化・定量metrics |
| v0.3 | 複数ケース対応・pipeline自動実行 |
| v1.0 | Multi-agent オーケストレーション・完全自動化 |

---

## 関連

- [フレームワーク全体像](framework/overview.md)
- [マルチモデル運用モデル](framework/operating-model.md)
- [SoChi BLOCKSケース](cases/sochi-blocks/README.md)
- [最初の run 推薦](cases/sochi-blocks/goals.md)
---

## Responsibility Matrix Alignment

`framework/responsibility-matrix.md` is the canonical source for
phase / role / artifact boundaries.

Read aligned docs in this order when details appear to conflict:
1. `framework/responsibility-matrix.md`
2. `framework/workflow/*.md`
3. `framework/agents/*.md`
4. `framework/templates/*.md`

`framework/workflow/*.md`, `framework/agents/*.md`, and
`framework/templates/*.md` are aligned derived docs. They do not replace the
canonical definition in `framework/responsibility-matrix.md`.

Alignment rules:
- `self-check` is Builder-internal quality control, not a standalone phase.
- Builder stops at build outputs, `build.md`, and `handoff.md`.
- Critic owns `review.md`.
- Judge or Human owns `improve.md` and `result.md`.
- `handoff.md` is a transfer note, not a replacement for canonical phase artifacts.
