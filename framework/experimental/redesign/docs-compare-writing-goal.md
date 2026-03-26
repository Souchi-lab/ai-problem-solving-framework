# Goal

---

## Goal Statement

APSF 再構築の次段として、
`docs/compare` 本文化の着手範囲を定義する。

今回の目的は compare 本文を無制限に広げることではなく、
compare routing で strong または conditional と判断された asset のうち、
本当に `docs/compare` に送るべき対象だけを使って、
structural ambiguity または structural difference を
説明可能な形で残すことである。

---

## Background

ここまでの evidence package により、
compare follow-up は execution result まで完了している。

その結果、compare 候補は次のように整理されている。

- `framework/planning-patterns.md`
  - strong compare candidate
- `src/apsf/viewer/api.py`
  - strong compare candidate
- `src/apsf/storage/run_repository.py`
  - conditional compare candidate

また、compare の正当化は

- structural ambiguity
- structural difference
- boundary stress
- extraction-versus-whole-placement explanation

に限定されており、
未読・未確認・単なる難しさは compare 理由として扱わない前提が成立している。

したがって次段では、
compare routing evidence を prose に落とす範囲を固定し、
`docs/compare` 本文化の最初の安全なスコープを定義する必要がある。

---

## Success Criteria

今回の goal は、次の条件を満たす compare-writing 着手条件を作れる状態になること。

1. compare 本文の対象 asset が shortlist ベースで限定されている
2. 主対象が
   `framework/planning-patterns.md`
   `src/apsf/viewer/api.py`
   であることが明確になっている
3. `src/apsf/storage/run_repository.py` は conditional 扱いのままであり、
   compare 本文の主役に昇格していない
4. compare 本文の目的が、
   structural ambiguity / structural difference の説明であると明示されている
5. compare 本文が rule refinement や migration judgment に化けないよう、
   scope が限定されている
6. compare 本文化は routing evidence の文章化であり、
   新たな compare 候補探索ではないことが明確になっている

---

## Expected Outputs

この run で目指す出力は次である。

- compare writing scope definition
- compare writing target list
- primary compare subject list
- conditional compare subject note
- compare writing exclusion note

---

## Non-Goals

今回の run では次はやらない。

- compare 文書本文の完成
- 新しい compare 候補の追加
- storage / viewer ルール改修
- migration readiness 判定
- file move や import change

---

## Constraints

- compare 本文化の対象は shortlist 採用済み asset に限る
- compare の主役は strong compare candidate を優先する
- conditional compare candidate は条件付き扱いのまま保つ
- compare 本文は structural explanation に留める
- rule refinement を compare 本文の中で始めない
- compare を `shared` の代替にしない

---

## Notes For Planner

Planner は次を明確化すること。

- compare 本文の対象 asset
- 主対象と条件付き対象の区別
- compare 本文化の目的
- compare 本文化で扱わないこと
- `docs/compare` 側で最初に書くべき説明の型

特に次を中心に扱うこと。

- `framework/planning-patterns.md`
- `src/apsf/viewer/api.py`
- `src/apsf/storage/run_repository.py`
