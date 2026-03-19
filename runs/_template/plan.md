# Plan

<!-- このファイルは framework/templates/plan.md のひな型を使用している -->
<!-- Planner が goal.md をもとに作成する -->
<!-- プロンプト: framework/agents/planner.md を参照 -->

---

## Problem Structure

-
-

---

## Hypotheses

- H1:
- H2:

---

## Options

### Option A:
- 概要:
- メリット:
- デメリット:

### Option B:
- 概要:
- メリット:
- デメリット:

---

## Selected Approach

**採用**:

**理由**:

---

## Implementation Readiness

<!-- build に進む前に Planner が自己チェックする -->
<!-- 3 項目以下しか ✅ にならない場合は、設計 run を追加することを検討する -->
<!-- 注: framework/templates/plan.md では Build / Execute Policy の直前に配置。-->
<!-- この _template は簡易版のため Execution Plan の直前に配置している -->

- [ ] API / data shape が確定している（build 中に新たに設計しない）
- [ ] 変更対象ファイル・箇所を列挙できる
- [ ] 依存順が 3 段階以内で説明できる
- [ ] 既存互換の保持点を 1 文で言える
- [ ] 検証・スモークチェックの観点を build 前に言える

**Open Questions（build 開始前に 0〜1 件であること）**:

- （なければ「なし」と記載）

**readiness 判定**:

- [ ] build に進んでよい（上記 5 項目中 4 項目以上 ✅ かつ Open Questions ≤ 1）
- [ ] 設計 run を追加する（上記条件を満たさない）

> ⚠️ 「設計 run を追加する」を選んだ場合、Builder はこの plan を受領しても build に進んではいけない。

---

## Execution Plan

- [ ] Step 1:
- [ ] Step 2:
- [ ] Step 3:

---

## Assumptions & Open Questions

-
