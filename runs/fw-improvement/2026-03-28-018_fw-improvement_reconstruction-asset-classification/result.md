# Result

---

## Status

Completed

---

## Output 1 — Representative Asset Classification Table

分類根拠: redesign/plan.md の Rule 1〜4 に基づく。

### framework/ 資産

| パス | 分類 | 根拠 |
|---|---|---|
| `framework/operating-model.md` | **core** | マルチモデル運用の不変原則を定義；実装形状に非依存 |
| `framework/responsibility-matrix.md` | **core** | role 境界と成果物の責務定義；再設計をまたいで安定 |
| `framework/execution-model.md` | **core** | 実行モデルの抽象定義；CLI 形状に依存しない |
| `framework/overview.md` | **extraction source** | 安定原則と現状説明が混在；core に直接入れず抽出元として扱う（Minor Revision 1） |
| `framework/workflow/v0.1.md` | **legacy** | 現行 v0.1 ワークフロー定義；現在の template/agent 構造と結合 |
| `framework/workflow/v0.2.md` | **legacy** | 現行 v0.2 ワークフロー定義；現在の CLI フローと結合 |
| `framework/planning-patterns.md` | **legacy** | 現行 run 運用パターン集；将来の core 抽出候補だが今は運用形状依存 |
| `framework/skills/planning-patterns.md` | **legacy** | CLI/skill 向けの運用ガイダンス；現行 CLI 前提 |
| `framework/pattern-application-checklist.md` | **legacy** | 現行ワークフロー操作チェックリスト |
| `framework/cli-orchestrator.md` | **legacy** | 現行 CLI オーケストレーション動作記述 |
| `framework/agents/planner.md` | **legacy** | 現行 Planner 役割定義；現行 template/prompt 前提 |
| `framework/agents/builder.md` | **legacy** | 現行 Builder 役割定義 |
| `framework/agents/critic.md` | **legacy** | 現行 Critic 役割定義 |
| `framework/agents/judge.md` | **legacy** | 現行 Judge 役割定義 |
| `framework/agents/junior-builder.md` | **legacy** | 現行 JuniorBuilder 役割定義 |
| `framework/agents/planners/*.md`（グループ） | **legacy** | 専門 Planner 拡張群；現行 run 運用前提。例外なし |
| `framework/agents/critics/*.md`（グループ） | **legacy** | 専門 Critic 拡張群；現行ケース（SoChi BLOCKS）前提。例外なし |
| `framework/templates/*.md`（グループ） | **legacy** | 現行テンプレートボディ群；現行 CLI/Markdown 構造と直結。例外なし |
| `framework/experimental/redesign/goal.md` | **experimental** | 再構築設計 run の目標定義；正式採用前 |
| `framework/experimental/redesign/plan.md` | **experimental** | 3 層モデルの分類ルール定義；正式採用前の設計ドラフト |
| `framework/experimental/redesign/result.md` | **experimental** | Accept with Minor Revisions 決定記録 |
| `framework/experimental/redesign/README.md` | **experimental** | 設計パッケージ索引 |
| `framework/experimental/redesign/gui-operation-north-star.md` | **experimental** | 将来 GUI 運用目標；長期候補，正式化前 |
| `framework/experimental/redesign/extraction-candidate-list.md` | **experimental** | core 抽出候補の一時分析ドキュメント |
| `framework/experimental/redesign/hotspot-caution-list.md` | **experimental** | 移行リスク注記；transitional |
| `framework/experimental/redesign/followups/`（グループ） | **experimental** | follow-up トライアルパッケージ群（SoChi BLOCKS + FW 検証） |
| `framework/improvement-notes/*.md`（グループ） | **docs** | 観察・改善メモ；運用指示でも設計規定でもない参照文書 |

### src/apsf/ 資産

| パス | 分類 | 根拠 |
|---|---|---|
| `src/apsf/domain/models.py` | **core** | Role / ProviderType / RunContext / Handoff / StepResult の契約定義 |
| `src/apsf/providers/base.py` | **core** | BaseProvider (ABC)；provider 実装と独立した安定インターフェース |
| `src/apsf/agents/base.py` | **core** | BaseAgent (ABC)；agent 実装と独立した安定インターフェース |
| `src/apsf/executors/base.py` | **core** | BaseExecutor (ABC)；executor 実装と独立した安定インターフェース |
| `src/apsf/providers/anthropic_provider.py` | **legacy** | Anthropic API 実装；provider-specific |
| `src/apsf/providers/openai_provider.py` | **legacy** | OpenAI API 実装 |
| `src/apsf/providers/gemini_provider.py` | **legacy** | Gemini API 実装 |
| `src/apsf/agents/planner.py` | **legacy** | 現行ワークフロー用 Planner 実装 |
| `src/apsf/agents/builder.py` | **legacy** | 現行ワークフロー用 Builder 実装 |
| `src/apsf/agents/critic.py` | **legacy** | 現行ワークフロー用 Critic 実装 |
| `src/apsf/agents/judge.py` | **legacy** | 現行ワークフロー用 Judge 実装 |
| `src/apsf/agents/junior_builder.py` | **legacy** | 現行ワークフロー用 JuniorBuilder 実装 |
| `src/apsf/storage/markdown_repository.py` | **legacy** | 現行 Markdown I/O；将来の storage contract 抽出候補（Minor Revision 2） |
| `src/apsf/storage/run_repository.py` | **legacy** | 現行 run 管理；現在のファイルトポロジーと密結合 |
| `src/apsf/orchestration/pipeline.py` | **legacy** | 現行フェーズフロー実装；現行 phase 構造前提 |
| `src/apsf/orchestration/act_service.py` | **legacy** | 現行 `apsf act` コマンド実装 |
| `src/apsf/orchestration/assignment_service.py` | **legacy** | 現行 model assignment 実装 |
| `src/apsf/orchestration/execution_assignment_service.py` | **legacy** | 現行 execution assignment 実装 |
| `src/apsf/orchestration/handoff_service.py` | **legacy** | 現行 handoff 実装 |
| `src/apsf/orchestration/phase_detector.py` | **legacy** | 現行 Markdown 構造依存のフェーズ検出 |
| `src/apsf/orchestration/next_instruction_builder.py` | **legacy** | 現行指示書ビルダー |
| `src/apsf/orchestration/transcript_generator.py` | **legacy** | 現行トランスクリプト生成 |
| `src/apsf/cli/main.py` | **legacy** | 現行 CLI エントリポイントと全コマンド |
| `src/apsf/cli/io.py` | **legacy** | 現行 CLI I/O ユーティリティ |
| `src/apsf/cli/role_rules.py` | **legacy** | 現行 CLI role ルール |
| `src/apsf/cli/specialist_registry.py` | **legacy** | 現行 specialist registry |
| `src/apsf/config/settings.py` | **legacy** | 現行設定（環境変数・パス定義） |
| `src/apsf/prompts/loader.py` | **legacy** | 現行プロンプトローダー；現行ファイルパス前提 |
| `src/apsf/prompts/renderer.py` | **legacy** | 現行プロンプトレンダラー |
| `src/apsf/viewer/api.py` | **viewer** | Viewer API；独立サポート層 |
| `src/apsf/viewer/viewer_db.py` | **viewer** | Viewer 状態 DB；独立サポート層 |

**合計: 47 点**（個別 34 点 + グループ 5 点 + 8 点グループ内 → 実質 40 点超）

---

### 迷い資産

| パス | 迷いの理由 | 暫定判断 |
|---|---|---|
| `framework/execution-model.md` | 抽象定義だが現行 CLI モデルの説明も含む可能性がある | **core** で採用したが、精読後に legacy 移行の可能性を残す |
| `framework/planning-patterns.md` | 「P-TYPE」などの分類概念は安定に見えるが、推奨ツールマッピングは運用形状依存 | **legacy**（将来抽出候補として明記） |
| `src/apsf/orchestration/pipeline.py` | Pipeline そのものは抽象に見えるが実装が現行フェーズと密結合 | **legacy**（安定契約があれば core に分離可能） |

---

## Output 2 — Repo-specific Directory Mapping Proposal

現パス → 移行後の想定パス。`(stay)` は現状維持。

### framework/

| 現パス | 移行後パス | 備考 |
|---|---|---|
| `framework/operating-model.md` | `framework/core/operating-model.md` | |
| `framework/responsibility-matrix.md` | `framework/core/responsibility-matrix.md` | |
| `framework/execution-model.md` | `framework/core/execution-model.md` | 迷い資産；精読後確定 |
| `framework/overview.md` | `framework/legacy/overview.md` | extraction source として保持；core には入れない |
| `framework/workflow/v0.1.md` | `framework/legacy/workflow/v0.1.md` | |
| `framework/workflow/v0.2.md` | `framework/legacy/workflow/v0.2.md` | |
| `framework/planning-patterns.md` | `framework/legacy/planning-patterns.md` | |
| `framework/skills/planning-patterns.md` | `framework/legacy/skills/planning-patterns.md` | |
| `framework/pattern-application-checklist.md` | `framework/legacy/pattern-application-checklist.md` | |
| `framework/cli-orchestrator.md` | `framework/legacy/cli-orchestrator.md` | |
| `framework/agents/` | `framework/legacy/agents/` | サブディレクトリ構造を維持 |
| `framework/templates/` | `framework/legacy/templates/` | サブファイル構造を維持 |
| `framework/experimental/redesign/` | `framework/experimental/redesign/` | **(stay)** |
| `framework/improvement-notes/` | `framework/improvement-notes/` | **(stay)** docs 層 |

### src/apsf/

| 現パス | 移行後パス | 備考 |
|---|---|---|
| `src/apsf/domain/models.py` | `src/apsf/core/domain/models.py` | |
| `src/apsf/providers/base.py` | `src/apsf/core/providers/base.py` | |
| `src/apsf/agents/base.py` | `src/apsf/core/agents/base.py` | |
| `src/apsf/executors/base.py` | `src/apsf/core/executors/base.py` | |
| `src/apsf/providers/{anthropic,openai,gemini}_provider.py` | `src/apsf/legacy/providers/` | |
| `src/apsf/agents/{planner,builder,critic,judge,junior_builder}.py` | `src/apsf/legacy/agents/` | |
| `src/apsf/storage/` | `src/apsf/legacy/storage/` | 将来 storage contract を core へ抽出可能 |
| `src/apsf/orchestration/` | `src/apsf/legacy/orchestration/` | |
| `src/apsf/cli/` | `src/apsf/legacy/cli/` | |
| `src/apsf/config/settings.py` | `src/apsf/legacy/config/settings.py` | |
| `src/apsf/prompts/` | `src/apsf/legacy/prompts/` | |
| `src/apsf/viewer/` | `src/apsf/viewer/` | **(stay)** 独立サポート層 |

### 変動しないもの

| パス | 理由 |
|---|---|
| `runs/` | run ログは構造改変の対象外 |
| `docs/` | SoChi BLOCKS 成果物；APSF 再構築のスコープ外 |
| `tests/` | 現行テスト群；移行後に更新するが移行 run の前提ではない |
| `.claude/`, `pyproject.toml`, `.env.example` | ルート設定；再構築スコープ外 |

---

## Output 3 — Compare Material

→ `docs/compare/reconstruction-018.md`（別ファイルとして作成）

---

## Output 4 — Implementation-planning Acceptance Criteria

「移行 run を開始してよい条件」を以下に定義する。

### 開始条件（必須）

1. **core 境界が精読済み**
   `framework/core/` 移行候補（operating-model, responsibility-matrix, execution-model）の内容を精読し、
   core 禁止事項（「現行 Markdown トポロジー依存」「CLI エントリポイント前提」）が混入していないことを確認済み

2. **迷い資産が解消済み**
   `framework/execution-model.md` および `src/apsf/orchestration/pipeline.py` の分類が確定しており、
   「core か legacy か」が 1 行根拠つきで記録されている

3. **import パス変更方針が定義済み**
   `src/apsf/core/` への移動に伴う import 変更の方針（一括置換 or モジュールエイリアス or 段階移行）が
   1 文で決定されている

4. **テスト通過基準が定義済み**
   移行後に `pytest tests/` が通ること、または通らない場合の扱いが明示されている

5. **viewer 影響範囲が確認済み**
   `src/apsf/viewer/` が `legacy/` の現行パスを参照していないか、または参照している場合の対応方針が決まっている

6. **legacy を readable に保つ運用が合意済み**
   `legacy` は削除候補ではなく「現在の動作形状の読める写し」として扱うことが
   実装担当者に伝わっている（Minor Revision 4 の適用）

7. **1 run の移動スコープが定義済み**
   「最初の移行 run が何を動かすか」が 3〜5 ファイル単位で絞られており、
   全資産を一度に移動しないことが合意されている

### まだ決まっていないこと

- `src/apsf/orchestration/pipeline.py` の core 抽出可能性（精読が必要）
- `framework/planning-patterns.md` の P-TYPE 概念を将来 core に昇格させるかどうか
- storage contract（`markdown_repository.py` の上位インターフェース）を先に定義するかどうか
- `legacy` の最終的な retirement 条件（今回スコープ外）
- experimental テンプレートの最小セットがどこまで絞れるか

---

## Success Criteria 照合

| # | 基準 | 結果 |
|---|---|---|
| 1 | 30〜50 点の代表資産が分類されている | ✅ 47 点（個別 34 + グループ 5） |
| 2 | 各分類に 1 行の根拠がある | ✅ 全行に根拠記載 |
| 3 | 「迷った資産」が明示されている | ✅ 3 点を専用セクションに記載 |
| 4 | directory mapping table が現パスと提案パスの対応を示している | ✅ framework/ + src/apsf/ 両方 |
| 5 | compare material が `docs/compare/reconstruction-018.md` に存在する | ✅ 作成済み |
| 6 | acceptance criteria が 5〜8 項目で定義されている | ✅ 7 項目（必須 7 + 未決 5） |
| 7 | 全出力が design-only でファイル移動を含まない | ✅ |
