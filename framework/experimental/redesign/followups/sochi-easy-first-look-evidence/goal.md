# Goal

---

## Follow-up Context

- Parent series:
  SoChi BLOCKS 初回体験改善
- Previous result:
  easy 問題は
  `easy label`
  ではなく
  `初見向け easy として機能するか`
  で見るべきであり、
  stable baseline として
  `discoverability / first move clarity / early success expectation / rules ambiguity pressure`
  の4軸が定義された
- New trigger:
  4軸は定義できたが、
  representative な easy 問題に実際に当てた evidence はまだない
- Scope limit:
  representative な easy 問題 1 件に対する first-look evidence の取得
- Non-goals:
  easy 群全体の横断評価 / difficulty rebalance / implementation

---

## Goal Statement

SoChi BLOCKS の representative な easy 問題 1 件に対して、
既に定義済みの 4軸を実際に当て、
`初見向け easy` 評価枠が
concrete evidence として機能するかを確認する
small follow-up を定義する。

今回の主題は、
新しい評価軸を増やすことではない。

主題は、
既存の 4軸が
実問題に対して十分に使える観察枠になるかどうかである。

---

## Background

前段の `sochi-easy-first-look` 系では、
次が固定された。

- `easy label` と `first-time usability` は分けて扱う
- 初見向け easy は
  `discoverability / first move clarity / early success expectation / rules ambiguity pressure`
  の4軸で見る
- representative な easy 問題の粒度で扱う
- compare は補助に留める

したがって次に必要なのは、
抽象議論を増やすことではなく、
この 4軸を実際の easy 問題に当てて、
何が見えるかを narrow に確認することである。

---

## Success Criteria

今回の goal は、
次の条件を満たす形で定義されていればよい。

1. 主題が
   `4軸を実問題に適用して evidence を得る`
   に固定されている
2. 対象が
   representative な easy 問題 1 件
   に限定されている
3. 新しい評価軸の追加や taxonomy 議論へ広がっていない
4. 出力が
   各軸ごとの観察結果または保留点
   を残せる形になっている
5. compare を使う場合も、
   `easy-looking but confusing`
   と
   `actually entry-friendly`
   の切り分け補助に留まっている
6. 後続 plan で、
   evidence の取り方と
   result の閉じ方を narrow に定義できる

---

## Expected Outputs

この run で期待する出力は次のとおり。

- representative easy 問題 1 件に対する evidence run の framing
- 4軸を実データに当てるための最小観察単位
- 観察結果として何を残すかの形
- 今回扱うこと / 扱わないこと の明確化

---

## Non-Goals

今回の run でやらないことは次のとおり。

- easy 群全体の横断評価
- difficulty taxonomy の見直し
- 全問題の rebalance
- UI / tutorial / copy 改善案の設計
- 実装変更や puzzle 差し替え判断
- 新しい評価軸の増設

---

## Constraints

- scope は representative な easy 問題 1 件に限定する
- 既存の 4軸を使い、
  新しい抽象軸を増やさない
- 主題は
  `評価枠の適用`
  であり、
  `難易度一般の再議論`
  ではない
- small follow-up として扱い、
  broad redesign に広げない

---

## Notes For Planner

Planner は次を先に固定すること。

- 今回の run は
  評価枠の有効性を concrete に見るものであり、
  評価枠自体の再設計ではない
- 対象は representative easy 問題 1 件で十分である
- 出力は
  軸ごとの観察結果 / ambiguity / open question
  を残せる形にする
- compare を使うとしても、
  confusion source の切り分け補助を超えないようにする
- ここで broad puzzle review や onboarding redesign に広げない
