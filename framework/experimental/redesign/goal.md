# Goal

---

## Goal Statement

APSF 再構築に向けて、現行 framework を壊さずに並走できる
ディレクトリ設計方針を定義する。

今回の目的は実装や全面移行ではなく、
`core / legacy / experimental` 三層型を前提に、
「何を残すか」「何を現行保持するか」「何を実験対象として切り出すか」
を責務ベースで明確化することである。

---

## Background

現行 APSF では、framework 文書、Markdown durable artifact、CLI 導線、
viewer、改善メモ、テンプレート群が一つの repo 内で同時に育っている。

この状態には強みがある一方で、次の課題が見えている。

- 不変に近い価値と、現行運用都合の実装詳細が同じ層に置かれやすい
- 現行を保守しながら新設計を試すときに、境界が曖昧になりやすい
- 冗長部分を切り捨てたいが、比較可能性まで失う危険がある
- viewer と durable な Markdown の責務が混線すると、記録系の設計を壊しやすい

そのため今回は、全面改変案ではなく、
現行を残したまま比較運用できる再構築設計を作る必要がある。

---

## Success Criteria

今回の goal は、次の条件を満たす設計文書を作れる状態になること。

1. `framework/` と `src/apsf/` に対して、
   `core / legacy / experimental` の三層構成案が示されている
2. 各層について、
   「どこに置くか」だけでなく「なぜそこに置くか」の責務根拠が説明されている
3. 主要既存要素について、
   少なくとも代表例を列挙したうえで
   `core` `legacy` `experimental` `viewer` のどこに属するかを判断できる
4. `shared` に置くべきものと置かないものの基準が明示されている
5. viewer は UI / inspection 支援層であり、
   durable な canonical record writer ではないことが明示されている
6. `core` に入れないものが禁止事項として定義されている
7. 現行を壊さず、比較可能性を残し、実験段階に留めるという制約が守られている
8. この run で決めること / 決めないことが分かれており、
   設計 run が実装 run に暴走しない

---

## Non-Goals

今回の run では次はやらない。

- 実際のファイル移動
- import path の変更
- CLI entrypoint の切替
- viewer API と experimental 設計の接続実装
- 既存テンプレート本文の全面書き換え
- 現行 framework の廃止判断
- 全面移行時期の決定
- 再構築案の最終採用決定

---

## Constraints

- 既存 repo の全面改変案にしない
- 現行 APSF を壊さず並走可能であること
- 冗長部分を後から切り捨てやすいこと
- ただし旧版との比較運用は維持すること
- 同一テーマの run を旧版と新版候補で対照できる粒度を保つこと
- viewer と durable な Markdown の責務を混同しないこと
- 今回は設計に止め、実装は対象外とすること

---

## Core Design Principle

分離は進めるが、断絶は起こさない。

そのため今回の再構築では、
`core` を「変更されにくい責務境界と契約」、
`legacy` を「比較可能な現行」、
`experimental` を「切り捨て可能な試験場」
として扱う。

また、viewer は `experimental` や `legacy` の内部要素ではなく、
比較・閲覧・操作を支える独立支援層として扱う。

---

## Explicit Rule For Core

`core` に入るのは、変更されにくい責務境界と契約のみであり、
現行運用を成立させる都合上の実装詳細は入れない。

`core` 禁止事項:

- Markdown ファイル構成依存の処理
- CLI entrypoint 依存
- viewer API 依存
- template 本文依存の分岐

---

## Notes For Planner

Planner は次を明確化すること。

- `framework` と `src/apsf` の三層ディレクトリ案
- 各ディレクトリの責務境界
- 既存要素の配置方針
- `shared` の最小範囲
- 比較運用を維持するための設計前提
- 今回の run で決めること / 決めないこと

特に、
`planning-patterns` 系のような「今後も育つ可能性があるが、現時点では現行運用寄り」
の要素については、当面 `legacy` 仮置きとし、
将来の invariant 抽出対象として扱う前提を明記すること。

また、
`shared` は最小共有を原則とし、
移行都合の比較表や対応表は `docs/compare` 側で扱うこと。
