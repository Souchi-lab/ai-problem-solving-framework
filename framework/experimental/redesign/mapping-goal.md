# Goal

---

## Goal Statement

APSF 再構築の follow-up planning run として、
現 repo 内の主要要素を新構造候補へどう配置するかを
repo-specific に設計する。

今回の目的は、実ファイルを移動することではなく、
現実の repo 構造を前提に
`core / legacy / experimental / viewer / docs/compare`
のどこへ置くべきかを、
責務根拠つきで判断できる配置方針を作ることである。

---

## Background

前段の reconstruction design package では、
三層構造そのものと、その責務境界は定義できた。

ただし現時点では、
その設計原則が repo 実物にどう当たるかはまだ十分に具体化されていない。

特に次の点は、repo 実物ベースで明確化する必要がある。

- 既存ファイル群をどの新構造候補に置くか
- `shared` に入れないものをどう明示するか
- `viewer` を独立支援層として保ちながら比較可能性をどう維持するか
- 後続の classification table と `docs/compare` を作るための配置骨格をどう作るか

したがって今回は、
再構築そのものではなく、
repo-specific directory mapping proposal を設計対象とする。

---

## Success Criteria

今回の goal は、次の条件を満たす設計成果物を作れる状態になること。

1. 現 repo の主要要素について、
   新構造候補への配置案が示されている
2. 各配置案について、
   「どこへ置くか」だけでなく「なぜそこに置くか」の責務根拠が説明されている
3. 少なくとも代表的な既存要素について、
   `core / legacy / experimental / viewer / docs/compare / shared非対象`
   のいずれに属するかを判断できる
4. `shared` に置くべきでない要素が、
   例つきで明示されている
5. `viewer` は独立支援層として扱われ、
   durable Markdown の canonical responsibility と混同されていない
6. 配置判断のうち、
   即決できるもの、保留すべきもの、抽出対象として扱うものが分かれている
7. 同一テーマの run を旧構造と新候補構造で比較できる前提が壊れていない
   粒度を保つ
8. この run が design-oriented に留まり、
   実装や移行許可へ膨らまない

---

## Expected Outputs

この run で目指す出力は次である。

- repo-specific directory mapping proposal
- 代表要素の配置一覧
- 配置ごとの責務根拠
- `shared` 非対象一覧
- 保留項目一覧

なお、本 run は主要要素と代表例を中心に扱い、
repo 全要素の完全分類を必須成果物とはしない。

これらは後続の
representative asset classification table、
`docs/compare`、
implementation-planning acceptance criteria
の土台になることを意図する。

---

## Non-Goals

今回の run では次はやらない。

- 実際のファイル移動
- import path の変更
- CLI entrypoint の変更
- viewer 実装の改修
- template 本文の書き換え
- migration 手順の確定
- `experimental` を canonical 扱いする判断
- 全面移行の開始判断

---

## Constraints

- 設計runとして扱い、実装runにしない
- 現行 repo を壊さず、並走可能性を維持する
- 比較可能性を壊さない
- `experimental` をまだ canonical とみなさない
- `viewer` と durable Markdown の責務を混同しない
- `shared` を便利箱にしない
- 現 repo の実物に即した判断にする

---

## Mapping Principle

配置判断は、現在どこにあるかではなく、
その要素がどの責務を持つかによって行う。

したがってこの run では、
「現行にあるから legacy」
「新しく見えるから experimental」
という雑な分類は採用しない。

判断基準は次とする。

- stable contract なら `core`
- current operating shape なら `legacy`
- discardable redesign draft なら `experimental`
- inspection / comparison / operator support なら `viewer`
- transitional compare material なら `docs/compare`
- 最小共有に当たらない共通化欲求は `shared` に入れない

---

## Explicit Caution

この run は、repo-specific mapping を決める run であって、
移行着手を許可する run ではない。

配置案が作られても、
それは設計上の推薦であり、
そのままファイル移動や import 変更の許可にはならない。

---

## Notes For Planner

Planner は次を明確化すること。

- 主要既存要素をどこへ置くか
- その配置の責務根拠
- `shared` に入れない理由
- 比較運用を壊さない配置条件
- 保留すべき要素
- 後続runに渡すべき未確定論点

特に、
次のような要素は一律即決ではなく、
「legacy 仮置き」「core 抽出候補」「compare 対象」
のどれとして扱うかを慎重に書き分けること。

- `framework/overview.md`
- `framework/planning-patterns.md`
- `src/apsf/storage/*`
- `src/apsf/orchestration/*`
