Date: 2026-03-29
Scope: APSF lightweight operation principles
Purpose: APSF を無駄な儀式にしないために、軽量化しても壊してはいけない核と削る対象を整理する

---

## One-Line Summary

APSF は全部を毎回フルで回すと重い。標準運用は軽量であるべきで、完全版は難案件にだけ使う。

---

## Why This Memo Exists

APSF の価値は phase / role / artifact の分離にあるが、そのままでは記録コストが先に立ちやすい。

特に次の失敗パターンが起きやすい。

- phase を毎回フルで通すことが目的になる
- artifact を埋めること自体が仕事になる
- 小タスクでも重い運用を要求して速度を落とす
- review より result や transcript の整形が優先される

このメモは、軽量化しても残すべき核と、削ってよい儀式を分けるための設計メモである。

---

## Design Position

軽量化の基本方針は次の一文に尽きる。

> 正しさを削らず、儀式だけ削る。

ここでいう正しさとは、少なくとも以下を指す。

- 何を成功とみなすかが明示されている
- 何を作るかが事前に決まっている
- 実際に何を変えたかが追える
- 作った本人とは別視点で疑う工程がある

---

## Principles

### 1. Standard Mode Must Be Lightweight

標準運用は軽量版にする。完全版は例外であり、複雑案件・高リスク案件・長期案件にだけ上げる。

毎回フル運用を前提にすると、APSF は problem solving framework ではなく documentation framework になる。

### 2. Keep Only Decision-Changing Artifacts

artifact は「次の意思決定を変えるもの」だけを残す。

残す価値が高いもの:

- `goal.md`
- `plan.md`
- `build.md`
- `review.md`

任意寄りまたは条件付きに落としやすいもの:

- `handoff.md`
- `plan_review.md`
- `build_review.md`
- `review_review.md`
- `improve_review.md`
- `improve.md`
- `result.md`
- `transcript.md`

### 3. Preserve Role Separation Even In Lightweight Mode

軽量化しても Builder と Critic の分離は残す。

AI 運用では self-check が independent review の代わりに扱われやすいが、ここを混同すると APSF の価値が薄れる。

### 4. Manage Phases By Stop Conditions

phase 名を増やすより、「何が揃ったら止まるか / 次へ進むか」を明示する。

例:

- 実装物がまだないなら `BUILD_NEEDED`
- 実装物はあるが独立レビューがまだなら `REVIEW_NEEDED`
- 致命的指摘があれば `BUILD_NEEDED` に戻す
- 軽微指摘のみなら accept 候補に進む

### 5. Define Small-Task Exemptions Explicitly

小タスク免除は運用者の気分ではなく制度として明文化する。

例:

- 30 分以内で終わる
- 変更が 1 ファイル程度
- 失敗しても高リスクではない
- 再利用性より即時性が重要

これらに該当する作業は軽量モードを標準とする。

### 6. Review Is Closer To Mandatory Than Result

`result.md` や `transcript.md` より `review.md` の方が重要である。

最終まとめはあとから作れるが、独立した批判は飛ばすと失われる。

### 7. Templates Must Help Thinking, Not Force Completion

テンプレートは全欄記入前提ではなく、必要箇所だけで回る設計にする。

空欄があっても run が壊れないことを優先する。

### 8. One Run Should Still Mean One Problem-Solving Cycle

軽量化しても run の単位は曖昧にしない。

run が複数の問題を抱え始めると、記録を薄くした分だけ再利用性と検証性が落ちる。

---

## Minimal Core

軽量 APSF でも残すべき最小核は次の 4 点である。

- success criteria
- chosen approach
- build record
- independent review

文書名で言えば、原則として以下が最小核になる。

- `goal.md`
- `plan.md`
- `build.md`
- `review.md`

---

## Anti-Patterns

次の状態は軽量化に失敗しているサインである。

- 毎回 `handoff.md` を作らないと進まない
- `*_review.md` が常設 artifact のように扱われている
- `result.md` を書くために review を省略する
- phase を人が毎回解釈し直さないと進行できない
- 小タスクでもフル run を回すのが当然になっている

---

## Proposed Follow-Up

このメモを実運用に落とすなら、次の順で効く。

1. standard / lightweight / full の 3 段階運用を明文化する
2. small-task exemption rule を `workflow` または `overview` に入れる
3. template を「必須」「条件付き」「補助」に再分類する
4. `review.md` を軽量運用でも外しにくい位置づけにする
5. `improve` / `result` / `transcript` の既定値を optional 側に寄せる

---

## Decision Summary

軽量 APSF の要点は次の通り。

- 標準は軽量、完全版は例外
- artifact は意思決定を変えるものだけ残す
- role 分離、特に build と review の分離は残す
- phase は名称より停止条件で扱う
- 小タスク免除を制度化する

要するに、APSF は「全部やると重いが、核だけ残して削ると強い」。
