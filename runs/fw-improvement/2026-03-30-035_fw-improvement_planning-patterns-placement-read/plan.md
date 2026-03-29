# Plan

---

## Goal Readiness Check

- `framework/planning-patterns.md` の本文を精読した
- `framework/core/` と `framework/legacy/` の受け皿は存在する
- run-018 の初期分類（legacy）と run-023 の保留理由（概念と運用が混在）を確認した

Decision: Proceed

---

## planning-patterns.md 精読結果

### 文書の構成

| セクション | 内容 | 性質 |
|---|---|---|
| How To Use | primary/secondary pattern の選び方 | 使用手順（現行フロー前提） |
| Readiness Connection | P-TYPE × readiness matrix | 現行 plan.md テンプレート前提 |
| P-01〜P-08 定義 | Purpose / Recognition Signals / Problem Structure / Execution Plan / Readiness / Recommended Tool / Notes / Example | 抽象層 + 運用層の混在 |
| Skill Usage Principle | skill 自動起動禁止の運用方針 | 現行 CLI skill 前提 |
| Notes | "first version"、skillization は follow-up run で | 現行実装状態の注記 |

### 抽象層と運用層の混在

**抽象層（core 候補に見える部分）**:

- P-01〜P-08 の Pattern 定義本体（Recognition Signals、Problem Structure Shape）は概念として type-agnostic に見える
- "Feature Implementation / Bug Fix / Refactoring / Migration…" の分類軸は汎用的

**運用層（legacy を指示する部分）**:

- **Examples** が全て具体 APSF run パスに固定されている（`runs/fw-improvement/2026-03-19-...`）
- **APSF-specific Notes** が現行 CLI 形状に言及（"CLI 拡張や repository API"、"taxonomy filesystem や parent/child topology"）
- **Recommended Planner Tool** が `model-assignment.md` を参照（現行運用 artifact）
- **Notes** に "first version" マーカーが残存
- 対になる `framework/legacy/skills/planning-patterns.md` は Unit C1 で既に legacy/ に着地済み

---

## 判定

**legacy**

### 理由

1. **run-018 初期分類との整合**：run-018 で「現行 run 運用パターン集；将来の core 抽出候補だが今は運用形状依存」と分類済み。今回の精読はその観察を確認する結果になった。

2. **core に短絡しない**：P-01〜P-08 の抽象層は実在するが、examples・APSF-specific Notes・Recommended Tool 参照と不分離のまま文書が書かれている。書き換えなしに抽象層だけを分離することはできない。goal.md の制約「durable guidance と current operational advice の混在があるなら正直に扱う」を適用する。

3. **対の skills ファイルとの一貫性**：`framework/legacy/skills/planning-patterns.md`（適用手順）は既に `legacy/` に着地している。概念定義ファイルも `legacy/` に揃えるのが最も honest。

4. **core inflation を防ぐ**：`framework/core/` には安定契約（operating-model / responsibility-matrix）が入っている。運用前提を含む "first version" パターン集は core 禁止事項「CLI エントリポイント前提の実装詳細」に隣接しており、今のままでは core に入れない。

5. **将来の抽出可能性は残る**：書き換えを伴う core 抽出は将来の選択肢として開いているが、今回は判定だけで閉じる。

---

## このrunで作成するもの

- `result.md` — 判定と根拠の要約

### 含めないもの

- 実ファイル移動
- 文書書き換え
- reconstruction 系列の再拡張

---

## Verification Policy

1. 判定が `core / legacy / hold` のいずれかで明示されている
2. 判定理由が structural reading に基づいている
3. run-018 の初期分類と矛盾しない
4. 実ファイル移動を含んでいない
