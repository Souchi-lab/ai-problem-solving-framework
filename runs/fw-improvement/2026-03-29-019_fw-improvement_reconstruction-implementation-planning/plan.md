# Plan

---

## Goal Readiness Check

- `goal.md` は `run-018` を前提に、implementation-planning のみを主語として固定している
- `run-018` で分類結果、mapping、compare material、acceptance criteria が揃っている
- 迷い資産 3 点が明示されており、初手から外す条件がある
- 今回は still design-only であり、ファイル移動や import 変更は行わない

Decision: Proceed

---

## Problem Structure

今回の問題は、
`core / legacy / experimental / viewer` の思想を再議論することではない。

問題は、
`run-018` の分類結果を
**実際に移し始められる単位**
へどう切るかである。

implementation-planning として必要なのは次の 4 点である。

1. 最初に触る単位はどこか
2. その次に触る単位はどこか
3. どこまでを 1 単位に含め、どこを明確に外すか
4. 各単位で何を確認すれば次へ進めるか

---

## Selected Approach

### 基本方針

最初の移行単位は、
`run-018` で `core` に分類された資産のうち、

- 巻き込みが少ない
- import 影響が読みやすい
- 検証が単純
- `legacy` や `viewer` を触らずに済む

ものから切る。

### planning 原則

- 最初の移行単位は 1〜3 単位に絞る
- 初手から `legacy` 再編や contract 抽出に入らない
- 迷い資産 3 点は明示的に保留する
- `viewer` は現位置維持とする
- Codex がそのまま build に移れる粒度にする

---

## Initial Migration Unit Policy

### Unit A: Framework Core Docs

最初の移行候補は、
`framework/core/` に入る明確文書資産である。

対象候補:

- `framework/operating-model.md`
- `framework/responsibility-matrix.md`

狙い:

- 文書移行単位として安全
- import 影響がない
- `core` の意味を repo 上で最初に可視化できる

除外:

- `framework/execution-model.md`
- `framework/overview.md`
- `framework/planning-patterns.md`
- `framework/templates/`
- `framework/agents/`

### Unit B: Python Core Contracts

次の移行候補は、
`src/apsf/core/` に入る明確コード資産である。

対象候補:

- `src/apsf/domain/models.py`
- `src/apsf/providers/base.py`
- `src/apsf/agents/base.py`
- `src/apsf/executors/base.py`

狙い:

- `core` をコード側でも最小構成で立ち上げられる
- ABC / domain model は比較的依存境界が明確

除外:

- provider 実装本体
- orchestration
- storage
- CLI
- viewer

### Unit C: Legacy Landing Cleanup

3 単位目が必要な場合だけ、
`legacy` 側の landing を読みやすくする計画単位を置く。

ただし今回は、
実際の `legacy` 再編を開始するより、
Unit A / B 後に何を安全に寄せられるかを定義する段階に留める。

対象候補:

- `framework/workflow/`
- `framework/templates/`
- `src/apsf/legacy/` の受け皿設計

除外:

- 実ファイル移動
- retirement 決定

---

## Deferred Assets Policy

次の 3 点は今回の初手から外す。

1. `framework/planning-patterns.md`
   - reusable guidance と current operational advice の混線が残る
2. `src/apsf/orchestration/pipeline.py`
   - `core` 抽出余地はあるが、現時点では legacy orchestration 本体
3. `src/apsf/storage/*`
   - contract 抽出を伴う可能性があり、初手の安全単位ではない

加えて次も保留する。

- `src/apsf/viewer/*`
- `framework/overview.md`
- `framework/experimental/redesign/`

---

## Implementation Order

順序は次で固定する。

1. Unit A: Framework Core Docs
2. Unit B: Python Core Contracts
3. Unit C: Legacy Landing Cleanup Planning

理由:

- Unit A は repo への可視的変更として最も安全
- Unit B はコード側 `core` の最小骨格を立ち上げられる
- Unit C は A / B を踏まえた後でないと設計がぶれやすい

---

## Risk-controlled Change Boundaries

### Unit A で触ってよいもの

- `framework/core/` の新設前提
- 上記 3 文書の移行計画
- 参照 README / index の最小更新計画

### Unit A で触らないもの

- `legacy` 文書群の大規模整理
- compare material の追加拡張

### Unit B で触ってよいもの

- `src/apsf/core/` の新設前提
- domain / base class の移行計画
- import 影響の列挙

### Unit B で触らないもの

- provider 実装本体
- orchestration / storage / CLI / viewer

### Unit C で触ってよいもの

- `legacy` 受け皿の配置計画
- readable legacy を保つための最低限の順序設計

### Unit C で触らないもの

- legacy retirement
- ambiguous asset の最終決着

---

## Verification Policy

各移行単位の検証観点は次で十分とする。

### Unit A

- `core` 文書が 1 箇所にまとまること
- `legacy` と責務混線を起こしていないこと
- compare 対象を増やしていないこと

### Unit B

- `src/apsf/core/` の import 影響が列挙されていること
- ABC / domain model の責務が維持されること
- `pytest` で最低限の整合確認が可能な形になっていること

### Unit C

- `legacy` が readable な現行運用として残ること
- `core` と `legacy` の境界が再び曖昧になっていないこと

---

## Completion Criteria

この run が完了とみなせるのは次の状態である。

1. 最初の移行単位が 1〜3 単位で確定している
2. 各単位に対象 / 非対象 / リスク境界がある
3. 実装順序に理由がある
4. 迷い資産 3 点を保留する理由が書かれている
5. 各単位に検証観点がある
6. 次の Codex implementation run の `plan.md` または `build.md` に転用できる

---

## Deliverables

- Initial migration unit proposal
- Ordered implementation sequence
- Risk-controlled change boundaries
- Verification and completion criteria

出力先は `result.md` にまとめる。

---

## Review Policy

今回は handoff 性が重要な run なので、
独立した `review.md` は必須としない。

代わりに `result.md` で次を明示的に回収する。

- 単位の妥当性
- 順序の妥当性
- 保留資産の扱い
- Codex 実装 run への接続可能性

---

## Expected Landing

この run の着地は、
`run-018` の分類結果が
**Codex が安全に着手できる実装単位**
へ変換された状態である。

つまり、

- 何から移すか
- 何を次に移すか
- 何をまだ移さないか
- どう確認しながら進めるか

が、そのまま次の実装 run の入力になることを目標とする。
