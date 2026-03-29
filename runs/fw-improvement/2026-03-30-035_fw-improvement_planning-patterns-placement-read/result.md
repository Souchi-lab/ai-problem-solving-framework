# Result

---

## Status

Completed

---

## 読解結果

### 文書構成

| セクション | 性質 |
|---|---|
| How To Use | 使用手順（現行フロー前提） |
| Readiness Connection | 現行 plan.md テンプレート前提の P-TYPE × readiness matrix |
| P-01〜P-08 定義 | 抽象構造（Recognition Signals / Problem Structure Shape）+ 運用層（examples / APSF-specific Notes）の混在 |
| Skill Usage Principle | 現行 CLI skill 前提の運用方針 |
| Notes | "first version" マーカー残存 |

### 抽象層と運用層の混在

**抽象層として読める部分**：P-01〜P-08 の Recognition Signals と Problem Structure Shape は concept として type-agnostic に見える。

**運用層として読める部分**：

- Examples が全て具体 APSF run パスに固定（`runs/fw-improvement/2026-03-19-...`）
- APSF-specific Notes が現行 CLI 形状に言及（"CLI 拡張"、"taxonomy filesystem"）
- Recommended Planner Tool が `model-assignment.md` を参照（現行運用 artifact）
- Notes に "first version" マーカーが残存

両層は現物の文書内で**不分離**であり、書き換えなしに抽象層だけを取り出すことはできない。

---

## 判定

**`framework/legacy/planning-patterns.md`**

---

## 判定理由

| 論点 | 内容 |
|---|---|
| 内容の核はあるが現物は core 文書ではない | 抽象構造を持つが examples / APSF-specific Notes / `model-assignment.md` 参照と不分離。goal.md の制約「混在があるなら正直に扱う」を適用 |
| 対の skills ファイルとの一貫性 | `framework/legacy/skills/planning-patterns.md`（適用手順）は Unit C1 で既に `legacy/` 着地済み。概念定義ファイルも揃えるのが honest |
| core inflation を防ぐ | `framework/core/` には stable contract（operating-model / responsibility-matrix）が入っている。"first version" 運用前提のパターン集は今のままでは core に入れない |
| run-018 初期分類を精読が追認 | run-018 で「将来の core 抽出候補だが今は運用形状依存」と分類済み。精読はその観察を確認する結果になった |
| 将来の core 抽出は開いている | P-TYPE archetypes の書き換えを伴う core 昇格は将来選択肢として残るが、今回スコープ外 |

---

## Verification チェック

| # | 基準 | 結果 |
|---|---|---|
| 1 | 判定が `core / legacy / hold` のいずれかで明示されている | ✅ legacy |
| 2 | 判定理由が structural reading に基づいている | ✅ |
| 3 | run-018 の初期分類と矛盾しない | ✅ 精読で追認 |
| 4 | 実ファイル移動を含んでいない | ✅ |

---

## reconstruction 系列の保留論点

この判定により、reconstruction 系の主要保留論点はゼロになった。

| 元保留論点 | 解消 run |
|---|---|
| `framework/execution-model.md` → core / legacy | run-022：legacy 確定 |
| `src/apsf/orchestration/pipeline.py` → core / legacy | run-032：legacy 確定、run-034：実移動完了 |
| `framework/planning-patterns.md` → core / legacy | run-035（この run）：legacy 確定 |
