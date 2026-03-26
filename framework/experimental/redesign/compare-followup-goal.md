# Goal

---

## Goal Statement

APSF 再構築の follow-up として、
`docs/compare` に送るべき対象と、その送付理由を整理する。

今回の目的は compare 文書を完成させることではなく、
row-execution で浮いた compare overlap と boundary stress を、
`docs/compare` 側で扱うべき候補として小さく固定することである。

---

## Background

row-execution package により、
代表 row 群から次の傾向が見えている。

- `framework/planning-patterns.md`
  は justified compare overlap
- `src/apsf/viewer/api.py`
  は strongest boundary stress and justified compare overlap
- `src/apsf/storage/run_repository.py`
  は justified hold with conditional compare

この結果から、
次段で必要なのはルール改善そのものより先に、
「何を compare に送るか」
「なぜ compare に送るのか」
を明示することだと分かる。

したがって今回は、
`docs/compare` 側の受け皿を作るための比較候補整理を対象にする。

---

## Success Criteria

今回の goal は、次の条件を満たす compare-oriented 成果物を作れる状態になること。

1. compare 候補 asset が識別されている
2. 各候補について、
   compare に送る理由が一行で説明できる
3. 強い compare 候補と条件付き compare 候補が分けられている
4. compare 候補が structural ambiguity に基づくものか、
   単なる未読・未確認に基づくものかを分けて扱える
5. `docs/compare` に送るべきものと、
   まだ compare に送るべきでないものが分かれている
6. compare は fallback ではなく、
   構造差や責務差を説明するための限定的な出力先として保たれている
7. この run が compare prose の本格執筆ではなく、
   compare routing design に留まっている

---

## Expected Outputs

この run で目指す出力は次である。

- compare candidate shortlist
- compare routing reason list
- strong compare candidate list
- conditional compare candidate list
- compare 非対象メモ

---

## Non-Goals

今回の run では次はやらない。

- `docs/compare` 文書本文の完成
- storage / viewer ルール改修そのもの
- file move や import change
- row table の全面再判定
- migration readiness 判定

---

## Constraints

- compare を増やしすぎない
- compare 候補は structural difference の説明価値がある場合に限る
- 単なる未読・未確認は compare 理由にしない
- `docs/compare` を `shared` の代替にしない
- evidence package の結論を壊さない

---

## Notes For Planner

Planner は次を明確化すること。

- どの asset が strong compare candidate か
- どの asset が conditional compare candidate か
- compare に送る理由
- compare に送らない理由
- compare 後続runに渡すべき未確定論点

特に次を中心に扱うこと。

- `framework/planning-patterns.md`
- `src/apsf/viewer/api.py`
- `src/apsf/storage/run_repository.py`
