# GUI Operation North Star

---

## Purpose

この文書は、
APSF の今後の設計判断を揃えるための北極星を明文化するための
原則メモである。

これは願望メモではない。
redesign / follow-up / small experiment を
今後ぶらさず進めるための
設計判断用の基準として置く。

---

## North Star

APSF の将来像は、
CLI や文書中心の運用ではなく、
GUI 中心の「ポチポチ運用」へ着地できることに置く。

ここでいう GUI 中心運用とは、
単に画面があることではない。

人間が問題解決の主導権を持ったまま、
必要な判断だけを GUI 上で選び、
AI はその判断を支える形で使われる運用を指す。

この将来像は、
durable record を消すことを意味しない。

GUI は判断導線の前面に立ち、
文書や記録は
判断の根拠と履歴を残す durable layer として後ろに残る。

---

## Ideal Interaction

理想の操作感は次のようなものである。

- GUI で run 種別を選ぶ
- 選んだ run 種別に応じた goal の型が自動で出る
- follow-up なら軽い形式が出る
- 実験系なら必要な確認だけが出る
- result を見て、次 trigger を押す

つまり、
毎回人間が文書構造を手で再発明するのではなく、
判断の骨格が先にあり、
文書や記録はそれを支える形に後退している状態が理想である。

---

## Why This Matters Now

現在進めている

- redesign
- follow-up の軽量化
- small experiment

は、
個別最適の作業ではない。

これらはすべて、
将来この GUI 中心運用へ移るための土台づくりである。

core / legacy / experimental の整理も、
follow-up を軽く切る工夫も、
small experiment を局所的に回す運用も、
あとで GUI に載せやすい判断単位へ分解するための作業として位置づける。

---

## Design Implication

今後の設計判断では、
**「あとでポチポチ化できるか」**
を重要な判断基準の1つに置く。

ここでいう「ポチポチ化できるか」は、
少なくとも次の 3 単位に落ちるかで見る。

- run type
- required checks
- next trigger

避けるべきもの:

- 文書が増えすぎる設計
- 判断単位が曖昧な設計
- 毎回人間が構造を再発明しないと回らない設計

優先すべきもの:

- run 種別が明確であること
- 必要な確認が限定されていること
- 次 trigger が自然に定義できること
- GUI 上で出し分けやすい判断単位に分解されていること

---

## Current Connection

今の redesign 文脈では、
この原則は次に接続する。

- `core / legacy / experimental`
  の切り方を、
  将来の GUI 上の責務分離としても読めるようにする
- follow-up の軽量化を、
  GUI で型を出し分ける前提で考える
- small experiment を、
  「必要な確認だけを出す run」の試験台として使う

つまり今の文書整理は、
文書のための文書整理ではなく、
将来 GUI が判断骨格を出せるようにするための整理でもある。

---

## Operational Principle

今後 APSF で新しい設計判断をするときは、
少なくとも次を確認する。

1. この判断単位は、あとで GUI で選択可能な単位になっているか
2. この run は、必要な確認だけを出す形に分解できているか
3. result から次 trigger へ自然につながるか

この3つに答えにくい設計は、
ポチポチ運用への着地を難しくする可能性が高い。

---

## Position

この文書は、
現時点では `experimental/redesign` に置くのが妥当である。

理由は、
まだ repo 全体の正式 core 原則として固定しきる段階ではなく、
まずは redesign 判断を揃えるための北極星として使う段階だからである。

ただし今後、
この原則が複数の redesign / follow-up / experiment で
安定して機能することが確認できた場合は、
`core/principles` 側へ昇格させる候補になりうる。

---

## Reusable Takeaway

APSF の redesign は、
文書中心運用を洗練すること自体が最終目的ではない。

最終的に目指すのは、
人間主体を保ちながら、
判断の骨格を GUI で自然に扱える
「ポチポチ運用」へ着地することである。
