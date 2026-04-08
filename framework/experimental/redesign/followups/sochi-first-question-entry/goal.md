# Goal

---

## Goal Statement

SoChi BLOCKS の初回体験改善系列 follow-up として、
「遊び方ページを読まなくても最初の1問に入れるか」を扱う。

今回の目的は、SoChi BLOCKS の初回導線において、
説明ページの読了を前提にしなくても、
最初の playable question に自然に入れるかどうかを
評価可能な問いとして定義することである。

---

## Background

これまでの redesign 系では、
構造整理、mapping、classification、row execution、compare writing まで進み、
抽象設計を増やすよりも、
必要なときだけ限定 follow-up を切る運用に移っている。

今回のテーマはその方針に合っている。

- 新系列を大きく増やす話ではない
- SoChi BLOCKS の既存文脈に接続している
- UX / entry / explainability の concrete follow-up として扱える
- compare や redesign 全体を再展開せずに、小さく試しやすい

そのため今回は、
SoChi BLOCKS の初回導線に絞った follow-up として、
最初の1問への入口体験を問いとして固定する。

---

## Success Criteria

今回の goal は、次の条件を満たす問いを定義できる状態になること。

1. 改善対象が
   「遊び方ページを読まなくても最初の1問に入れるか」
   に限定されている
2. この問いが
   SoChi BLOCKS の初回体験改善として妥当である理由が説明できる
3. 説明不足の問題と、導線設計の問題を混同しない
4. 「最初の1問に入れる」の意味が、
   少なくとも `entry / clarity / playable transition` の観点で扱える
5. この follow-up が
   redesign 全体の再整理や migration 議論に広がらない
6. 後続の plan で、
   改善対象、比較対象、非対象を切り分けられる形になっている

---

## Expected Outputs

この run で目指す出力は次である。

- SoChi BLOCKS 初回体験改善の問いの固定
- entry 問題としてのスコープ定義
- この follow-up で扱うこと / 扱わないこと
- 後続 plan に渡せる観点の整理

---

## Non-Goals

今回の run では次はやらない。

- SoChi BLOCKS 全体 UX の再設計
- puzzle difficulty 調整そのもの
- onboarding 全体設計の全面見直し
- migration や framework redesign 全体への接続議論
- 実装着手

---

## Constraints

- scope は SoChi BLOCKS の初回導線に限定する
- 主題は「最初の1問への入口」であり、説明資料全体の評価に広げない
- playable transition を主題にし、一般的な UI 感想文にしない
- small follow-up として扱い、新しい抽象系列に膨らませない

---

## Notes For Planner

Planner は次を明確化すること。

- 何をもって「遊び方ページを読まなくても入れる」とみなすか
- 何が entry 問題で、何が別問題か
- compare が必要なら何を比較するか
- この follow-up で見る UX の最小観点

特に、
「説明があるか」と
「説明を読まないと最初の1問に入れないか」は
同じではないことを区別すること。
