# Plan

<!-- goal.md を参照して Planner が作成する -->

---

## Goal Readiness Check

<!-- Planner が goal.md の planning readiness を確認する。
     goal review ではなく、planning を阻害する構造的問題の限定チェック。
     goal.md の文体・優先度・目標の再定義はスコープ外。 -->

### チェック実施

| チェック項目 | チェック通過 | 備考 |
|---|---|---|
| スコープ（何を作るか）が 1 つに絞れるか | ○ / ✗ |  |
| plan が依存する前提が goal.md に記載されているか | ○ / ✗ |  |
| Success Criteria が存在し相互矛盾していないか | ○ / ✗ |  |
| blocking 依存関係が明示されているか | ○ / ✗ |  |

### 判定

- [ ] **Proceed** — 問題なし。plan 作成を続ける。
- [ ] **Proceed with assumptions** — 軽微な曖昧さあり。仮定を下記に明記し、plan を続ける。<!-- 仮定は plan.md 末尾の ## Assumptions & Open Questions にも転記すること -->
  - 仮定:
- [ ] **Blocked** — 重大な欠如 / 矛盾あり。plan 作成を中断し Human に差し戻す。
  - 根拠:
  - Human への依頼: goal.md の〔該当箇所〕を〔どう直すべきか〕修正し、PLAN_NEEDED に戻してください。

---

## Problem Structure

<!-- この問題の本質は何か。どんなサブ問題に分解できるか -->

- サブ問題 1:
- サブ問題 2:
- サブ問題 3:

---

## Hypotheses

<!-- 解決のための仮説を 1〜3 個。「〜すれば〜が改善されるはず」という形で -->

- H1:
- H2:
- H3:

---

## Options

<!-- 少なくとも 2 つのアプローチを比較する -->

### Option A: <!-- アプローチ名 -->
- 概要:
- メリット:
- デメリット:

### Option B: <!-- アプローチ名 -->
- 概要:
- メリット:
- デメリット:

<!-- 必要に応じて Option C 以降を追加 -->

---

## Selected Approach

<!-- 採用するアプローチとその理由 -->

**採用**: Option A / B / C

**理由**:

**採用しなかった選択肢の理由**:

---

**Planning Pattern Reference**:

- 必要に応じて `framework/planning-patterns.md` を参照し、今回の問題の primary pattern を意識して `Problem Structure` / `Execution Plan` / `Implementation Readiness` を書く

## External Inputs

<!-- Planner が記入。識別基準に照らして外部観察の要否を判定し記載する -->

### 要否判定

- [ ] 外部観察が必要（カテゴリ A / B / C のいずれかに該当）
  - 該当カテゴリ:
  - 判定根拠:
- [ ] 外部観察不要（内部仮説のみで Build に進む）

### 観察対象（必要な場合のみ記入）

| 観察対象 | 観察の目的 | 担当 | 完了タイミング | 記録先 |
|---|---|---|---|---|
|  |  | Human / AI |  | research-input.md または plan.md 付録 |

<!-- 外部観察が必要と判定した場合:
     framework/templates/research-input.md を
     runs/<run-name>/research-input.md としてコピーして使う
     （runs/_template には含まれていないため、必要な run で個別にコピーすること） -->

### Build 開始前チェック

- [ ] 必要な外部観察がすべて完了している（または不要と確認した）
- [ ] 外部観察結果が `research-input.md` または plan.md 付録に記録されている
- [ ] Builder が外部入力を参照できる状態になっている

---

## Implementation Readiness

<!-- build に進む前に Planner が自己チェックする -->
<!-- 3 項目以下しか ✅ にならない場合は、設計 run を追加することを検討する -->

- [ ] API / data shape が確定している（build 中に新たに設計しない）
- [ ] 変更対象ファイル・箇所を列挙できる
- [ ] 依存順が 3 段階以内で説明できる
- [ ] 既存互換の保持点を 1 文で言える
- [ ] 検証・スモークチェックの観点を build 前に言える

### Satisfiability Classification

<!-- Planner が goal.md の Success Criteria と plan 内の unresolved prerequisites を照合する。 -->
<!-- この分類は phase を変えない。warning / explanation 用の additive signal として使う。 -->

- Classification: `SATISFIED` / `EXPLORATORY` / `UNSATISFIED`
- Rationale:
- Required unresolved prerequisites (if any):

Classification rule:

- `SATISFIED`: Goal が execution-ready / verified output を要求していない、または required prerequisite が解消済み
- `EXPLORATORY`: Goal が provisional / investigative output を明示的に許しており、未解決項目がその暫定スコープと整合している
- `UNSATISFIED`: Goal が execution-ready / strictly verified output を要求しているのに、plan が required prerequisite を unresolved のまま残している

**Open Questions（build 開始前に 0〜1 件であること）**:

- （なければ「なし」と記載）

**readiness 判定**:

- [ ] build に進んでよい（上記 5 項目中 4 項目以上 ✅ かつ Open Questions ≤ 1）
- [ ] 設計 run を追加する（上記条件を満たさない）

> ⚠️ 「設計 run を追加する」を選んだ場合、Builder はこの plan を受領しても build に進んではいけない。

---

### Build / Execute Policy

<!-- Option B: build 自動進行は plan で明示許可された場合のみ許可する -->

- [ ] Builder はこの plan を受領後、自動で Build に進んでよい
- [ ] Builder は Build までで停止する
- [ ] Builder は Build 後、実行 / publish まで進んでよい

**Build 対象成果物**:

-

**Build に進んではいけない条件**:

-

**Build 後に実行 / publish へ進んでよい条件**:

-

**差し戻し条件（Planner に戻す条件）**:

-

---

## Execution Plan

<!-- Builder が動けるレベルの具体的なステップ -->

- [ ] Step 1:
- [ ] Step 2:
- [ ] Step 3:

---

## Assumptions & Open Questions

<!-- 前提としていること、確認が必要な事項 -->

- 前提:
- 要確認:
---

## Alignment Note

`framework/responsibility-matrix.md` is the canonical source for
phase / role / artifact boundaries.

Use `Build / Execute Policy` to state, explicitly:
- whether Builder may proceed,
- that Builder stops at Build,
- and that Builder is forbidden from creating `review.md`,
  `improve.md`, or `result.md`.
