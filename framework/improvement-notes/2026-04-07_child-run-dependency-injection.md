# Child Run 依存成果物の自動注入

**日付:** 2026-04-07
**優先度:** 高
**発見契機:** run 001c2 で c1 の strategy-spec を参照せず独自仮定で build が走り、数値の食い違いが後から発覚

---

## 問題

child run 間に依存関係がある場合（例: c2 は c1 の成果物を前提とする）、現状の仕組みでは：

- `execution-assignment.md` に依存関係が記載されていても Builder prompt には注入されない
- Builder は依存 child run の成果物を読まずに独自仮定で build を進めてしまう
- Critic も依存 child run の数値を知らずにレビューするため、食い違いが通過してしまう

### 今回の具体的な食い違い

| 項目 | c2 が使った値 | c1 strategy-spec の確定値 |
|---|---|---|
| 価格上限 | ¥10,000 | ¥9,000 |
| ADTV 閾値 | ¥500,000,000/day | ¥50,000,000/day |
| total-return 方針 | Q-5 未解決 | price-return（AdjC）で確定済み |

これらは c1 完了時点で確定していたが、c2 には伝わっていなかった。

---

## 改善案

### 案 A: `plan.md` に依存成果物パスを明記（最小コスト）

```markdown
## Dependencies
- 001c1: strategy-spec-v0.1.md（価格上限・ADTV・return type の確定値）
```

Planner が plan.md を書く際に依存 child run の成果物パスを明示する規約にする。
Builder はビルド前に必ずこのファイルを読む手順を specialist / role guidance に追加する。

### 案 B: `execution-assignment.md` に `depends_on` フィールドを追加

```markdown
## Dependencies
- run: 001c1_investment-project_strategy-spec
  artifact: strategy-spec-v0.1.md
  reason: 価格上限・ADTV 閾値・universe filter の確定値
```

wrapper スクリプトが BUILD_NEEDED 起動時にこのファイルを読み、
依存成果物の内容を Builder prompt に自動注入する。

### 案 C: Critic チェックリストに「依存 child run との照合」を追加

Critic（特に C-09 Data Contract Critic）が review 時に
plan.md の Dependencies セクションを読んで、
依存成果物との数値照合を必須チェック項目とする。

---

## 推奨アプローチ

**短期:** 案 A（規約のみ、コードなし）を即時採用。Planner と Builder の specialist / role guidance に追記。

**中期:** 案 B（自動注入）を wrapper に実装。依存成果物が未完了の場合は BUILD_NEEDED をブロックする。

**長期:** 案 C を Critic specialist に組み込み、照合漏れを review で確実にキャッチする。

---

## 影響範囲

- `framework/agents/builder.md` — 依存成果物を読む手順を追加
- `framework/agents/planners/` — plan.md に Dependencies セクションを書く規約
- `scripts/apsf-claude-build.ps1` — 案 B 実装時に depends_on 注入ロジックを追加
- `framework/agents/critics/` — 案 C 実装時に照合チェックを追加
