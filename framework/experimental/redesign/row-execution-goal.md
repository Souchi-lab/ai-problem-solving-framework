# Goal

---

## Goal Statement

APSF 再構築の representative concrete row execution run として、
代表的な既存 asset に対して
classification row を実際に作成し、
mapping / classification package で定義したルールが
具体例に対してどのように機能するかを evidence として残す。

今回の目的は、repo を移行することではなく、
設計済みの分類手法を実例に当て、
どの asset が素直に分類でき、
どの asset が caution・hold・compare routing を必要とするかを
行単位で明示することである。

---

## Background

ここまでに、`framework/experimental/redesign/` には
次の3段の設計パッケージが揃っている。

- reconstruction design package
- mapping package
- classification package

これにより、

- `core / legacy / experimental / viewer / docs/compare`
  という配置候補
- `Immediate Placement / Legacy-For-Now / Extraction Candidate / Hold / Review Later`
  という outcome category
- `asset / proposed destination / outcome category / one-line rationale / caution`
  という row 構造
- `compare routing reason` の記録

が定義済みである。

しかし現時点では、
これらはまだ design package としての妥当性確認に留まっており、
具体例に対して row が並んだ状態の evidence はまだない。

そのため今回は、
representative concrete row execution を行い、
分類手法そのものを concrete evidence に変える。

---

## Success Criteria

今回の goal は、次の条件を満たす concrete classification 成果物を作れる状態になること。

1. 代表的な既存 asset に対して、
   実際の classification row が作成されている
2. 各 row が少なくとも次を含んでいる
   `asset / proposed destination / outcome category / one-line rationale / caution`
3. compare-worthy な例については、
   `compare routing reason` が残されている
4. 各 row について、
   その例が主に rule を confirm する例か、
   rule を stress する例かが分かる
5. hotspot asset が routine asset と同じ温度で処理されていない
6. `Hold / Review Later` が必要な場面で正当に使われている
7. `shared` が fallback 先として使われていない
8. viewer と durable Markdown authority の責務が concrete row 上でも混線していない
9. この run があくまで design-oriented evidence 生成に留まり、
   migration readiness 判定に化けていない

---

## Expected Outputs

この run で目指す出力は次である。

- representative concrete row table
- hotspot caution list
- updated hold list
- updated extraction-candidate list
- compare candidate list

各 row は、少なくとも次の項目を持つこと。

- asset
- proposed destination
- outcome category
- one-line rationale
- caution

必要な場合のみ追加で持つ項目:

- compare routing reason
- rule confirm / rule stress note

---

## Non-Goals

今回の run では次はやらない。

- repo 全件分類
- ファイル移動
- import path の変更
- package rename
- CLI 切替
- viewer 改修
- compare 文書の完成
- migration readiness の最終判定
- `experimental` の canonical 化

---

## Constraints

- classification package の fixed decision sequence に従う
- row ごとの判断を ad hoc で増やしすぎない
- `confidence` のような新しい評価軸は増やさない
- outcome category / caution / compare routing reason で確度を表現する
- `shared` を fallback にしない
- viewer と durable Markdown の責務を混同しない
- hotspot は routine asset より慎重に扱う
- compare 候補が増えすぎた場合は、row を増やす前に rule 側を疑う

---

## Execution Principle

この run は、
設計した分類手法を concrete row に落とし込む run である。

したがって評価すべきなのは、
「何件分類したか」ではなく、
「rule が具体例に対して無理なく適用できるか」である。

良い結果とは、
多数の `Immediate Placement` を並べることではなく、
必要な場所で `Legacy-For-Now` `Extraction Candidate` `Hold / Review Later`
を健全に使い分けられている状態を指す。

---

## Explicit Caution

この run の row 群は、
設計判断を concrete evidence として残すためのものであり、
そのまま移行順序や実装着手の承認にはならない。

また、複数の row で同種の ad hoc 例外が必要になる場合は、
row 側で吸収するのではなく、
classification rule 側を見直すべきである。

---

## Notes For Planner

Planner は次を明確化すること。

- 今回扱う representative asset の最終セット
- 各 asset の selection reason
- 各 row の proposed destination
- 各 row の outcome category
- one-line rationale
- caution
- compare routing reason の有無
- その row が rule confirm か rule stress か

特に次の hotspot は慎重に扱うこと。

- `framework/overview.md`
- `framework/planning-patterns.md`
- `src/apsf/storage/run_repository.py`
- `src/apsf/storage/markdown_repository.py`
- `src/apsf/orchestration/phase_detector.py`
- `src/apsf/orchestration/next_instruction_builder.py`
- `src/apsf/viewer/api.py`
