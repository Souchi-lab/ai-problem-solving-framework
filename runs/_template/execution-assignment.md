# Execution Assignment

<!-- framework/templates/execution-assignment.md のひな型を使用 -->
<!-- run 開始時に model-assignment.md と同時に作成する -->
<!-- 「どうやって実行するか」を定義するファイル。model-assignment.md は「どのモデルを使うか」 -->

---

## Run Name

<!-- 例: 2026-03-15_sochi-blocks_sns-post-template -->

## Goal Summary

<!-- goal.md の 1〜2 行要約 -->

---

## Role Execution Assignments

| Role | Execution Type | Tool / Method | Workspace | Notes |
|---|---|---|---|---|
| Planner | human | チャットAI + テキストエディタ | workspaces/planner/ | goal.md を読んで plan.md を作成 |
| JuniorBuilder | cli | gemini-cli | workspaces/junior_builder/ | 高速ドラフト・構造スケッチ |
| Builder | cli | claude | workspaces/builder/ | ★ 最良ツールをここに投入 |
| Critic | human | ChatGPT / 手動レビュー | workspaces/critic/ | Builder と異なるツールで評価 |
| Judge | human | 手動 | workspaces/judge/ | 人間が最終判断（v0.1） |

---

## Command or Manual Procedure

### Planner（human）

1. `runs/<run-name>/goal.md` を読む
2. `cases/<case-key>/context.md` で背景・制約を確認する
3. ChatGPT またはテキストエディタで plan.md の骨子を書く
4. `runs/<run-name>/plan.md` に保存する
5. `runs/<run-name>/handoff.md` を更新する（→ Builder へ）

```
参照ファイル:
  runs/<run-name>/goal.md
  cases/sochi-blocks/context.md
  framework/agents/planner.md

出力ファイル:
  runs/<run-name>/plan.md
  runs/<run-name>/handoff.md  ← Planner → Builder
```

---

### JuniorBuilder（cli: gemini-cli）

```bash
# workspaces/junior_builder/ に移動してから実行
cd workspaces/junior_builder/

# plan.md の構造を元に高速ドラフトを作成
gemini "runs/<run-name>/plan.md を読んで、SNS 投稿テンプレートの構造案を作ってください。
詳細より速度優先。3〜5 パターンのドラフトを出力してください。"
```

出力: `workspaces/junior_builder/draft.md` に保存 → Builder が参照

---

### Builder（cli: claude）

```bash
# workspaces/builder/ に移動してから実行
cd workspaces/builder/

# plan.md + JuniorBuilder のドラフトを元に高品質版を作成
claude "以下を読んでください:
- runs/<run-name>/goal.md
- runs/<run-name>/plan.md
- workspaces/junior_builder/draft.md

SNS 投稿テンプレートの完成版を作成してください。
品質・訴求力・再利用性を重視してください。
出力先: runs/<run-name>/build.md"
```

出力: `runs/<run-name>/build.md`
完了後: `runs/<run-name>/handoff.md` を更新する（→ Critic へ）

---

### Critic（human: ChatGPT）

1. `runs/<run-name>/build.md` を読む
2. `runs/<run-name>/goal.md` の成功基準を確認する
3. ChatGPT に以下のプロンプトで評価を依頼する:
   ```
   以下の SNS 投稿テンプレートを評価してください。
   goal.md の成功基準との照合、改善点、懸念事項を列挙してください。
   [build.md の内容を貼り付け]
   ```
4. `runs/<run-name>/review.md` に評価結果を保存する
5. `runs/<run-name>/handoff.md` を更新する（→ Judge へ）

```
参照ファイル:
  runs/<run-name>/build.md
  runs/<run-name>/goal.md

出力ファイル:
  runs/<run-name>/review.md
  runs/<run-name>/handoff.md  ← Critic → Judge
```

---

### Judge（human）

1. `runs/<run-name>/review.md` を読む
2. `runs/<run-name>/build.md` を読む
3. 以下を判断する:
   - このまま採用 → `improve.md` に「採用・理由」を記録
   - 修正して採用 → `improve.md` に「修正指示」を記録して Builder に差し戻す
   - 却下 → `improve.md` に「却下・理由・次のアクション」を記録
4. `runs/<run-name>/improve.md` に判断結果を保存する
5. 採用の場合は `runs/<run-name>/result.md` を作成する

```
参照ファイル:
  runs/<run-name>/build.md
  runs/<run-name>/review.md
  runs/<run-name>/handoff.md

出力ファイル:
  runs/<run-name>/improve.md
  runs/<run-name>/result.md  ← 採用時のみ
```

---

## Why This Execution Plan

- **Planner = human**: 問題の構造化・制約の理解は人間判断が品質安定に直結するため
- **JuniorBuilder = gemini-cli**: 高速ドラフト生成はコスト・速度優先、SNS 構造案は精度より網羅性が重要
- **Builder = claude**: 最高品質の成果物が必要なステップに最良ツールを集中投入
- **Critic = human + ChatGPT**: Builder と異なるツール・視点で評価することでバイアス排除
- **Judge = human**: 採用・却下の最終判断は人間が持つ（v0.1 設計方針）

---

## Operational Risks

- [ ] `gemini-cli` がインストールされていない場合 → JuniorBuilder を human に切り替える
- [ ] `claude` CLI がインストールされていない場合 → Builder を human（ChatGPT）に切り替える
- [ ] Builder の出力が長すぎる場合 → build.md を分割して Critic に渡す
- [ ] Judge が差し戻しを繰り返す場合 → goal.md の成功基準が曖昧な可能性を疑う
