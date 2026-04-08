# Plan

---

## Follow-up Context

- Parent series:
  SoChi BLOCKS 初回体験改善
- Previous result:
  初回導線は first playable moment を優先して評価すべきである
- New trigger:
  遊び方ページ先読みに hidden dependency がある可能性
- Scope limit:
  first-question entry のみ
- Non-goals:
  full onboarding redesign / implementation

---

## Run Metadata

- Follow-up:
  SoChi BLOCKS first-question entry
- Goal:
  遊び方ページを先に読まなくても、
  最初の playable question に入れるかどうかを評価するための
  follow-up 枠組みを定義する
- Output focus:
  `entry / clarity / playable transition` による観点整理
- Non-goal reminder:
  これは full UX redesign や implementation plan ではない

---

## Goal Readiness Check

- 問いは具体的である
- scope は first-question entry に限定されている
- 「説明が存在すること」と「説明を先に読まないと入れないこと」の違いが明示されている
- 新しい抽象系列ではなく、小さな follow-up として扱える

Decision:

- Proceed

---

## Execution Intent

この follow-up の目的は、
次の狭い UX 問いを扱えるようにすることである。

初回ユーザーは、
専用の「遊び方」ページを先に読まなくても、
自然に最初の playable question に入れるか。

重要なのは、
どこにも説明が不要だと主張することではない。

区別したいのは次の2つである。

- 説明があると安心して進める状態
- 説明を先に読まないと最初の1問に入れない状態

したがってこの follow-up では、
説明資料全体ではなく、
最初の playable entry 条件を主題にする。

---

## Problem Structure

この問いは、次の3つに分けて扱う。

### 1. Entry

ユーザーは、どこから始めればよいか分かるか。

### 2. Clarity

始めた直後に、次に何をすればよいかが分かるか。

### 3. Playable Transition

「来た」状態から、
「最初の1問を実際に試している」状態へ、
別ページ読了を挟まずに移れるか。

この3つは関連するが同一ではない。

---

## Selected Approach

Approach:

この問題を、一般的な documentation 問題ではなく、
first-question entry 問題として扱う。

Reasoning:

- 専用の遊び方ページ自体には価値がありうる
- しかし、その存在が「先に読まないと遊べない」ことを意味してはいけない
- 最も強い UX 問いは、最初の playable moment が自走可能かどうかである
- この切り方なら、follow-up を小さく保てる

これを broad onboarding review より優先する理由:

- whole-product UX redesign へ膨らみにくい
- 最初のプレイ遷移という concrete な単位に結びつく
- 後で `read first` と `play first` の差を比較しやすい

---

## Scope Policy

この follow-up に含めるもの:

- 最初の playable entry point
- 最初のアクション直後の分かりやすさ
- landing context から first-question attempt への遷移
- optional explanation と required explanation の役割差

この follow-up に含めないもの:

- full tutorial system design
- later-session mastery UX
- puzzle difficulty balancing 全般
- complete information architecture redesign
- marketing / acquisition flow

---

## Compare Policy

compare を使うのは、次を切り分けるのに役立つ場合だけにする。

- optional explanation と required explanation
- `play first` entry と `read first` dependency
- entry friction と general documentation weakness

compare を使わないもの:

- broad UX opinion gathering
- speculative redesign expansion
- first-question entry と無関係な問題

---

## Working Definitions

後続の follow-up では、少なくとも次の定義を使う。

### 「最初の1問に入れる」

ユーザーが、専用の説明ページを先に読まなくても、
最初の playable question の開始点を見つけて、
実際に最初の操作へ入れること。

### 「遊び方ページを先に読む」

最初の問題に入る前に、
別導線へ移動して説明を読まないと、
最初の1問を試せる状態にならないこと。

### 「optional explanation」

理解や安心感を高めるが、
最初の1問への entry には必須ではない説明。

### 「required explanation」

それを先に読まないと、
最初の1問への entry が成立しない説明。

---

## Evaluation Focus

後続では、少なくとも次の問いを見る。

- 最初の entry point は視覚的にも挙動的にも明確か
- 最初の1問は prior reading なしで行動を誘発できるか
- 次の1アクションは文脈内で理解できるか
- ユーザーの停止は entry friction 由来か、それとも deeper rules ambiguity 由来か
- 遊び方ページは optional support か、required prerequisite か

---

## Deliverables

この follow-up で作るもの:

- first-question entry 問題の framing
- entry / clarity / playable transition の分解
- optional explanation と required explanation の区別
- included / excluded scope
- 後続評価に使える最小観点

---

## Review Checklist

- first-question entry が中心に保たれている
- explanation presence と explanation dependency を混同していない
- onboarding 全体 redesign に膨らんでいない
- compare は entry 問題を明確にする時だけ使っている
- 出力が small follow-up として使える

---

## Planned Output Shape

出力は次の順でまとめる。

1. entry problem framing
2. `entry / clarity / playable transition` の分解
3. optional vs required explanation の区別
4. included vs excluded scope
5. evaluation questions

---

## Assumptions & Open Questions

Assumptions:

- 遊び方ページは存在してもよいが、first play の必須条件である必要はない
- first-question entry は独立した UX 評価単位として意味がある
- broad onboarding redesign より small follow-up の方が妥当である

Open questions:

- first-question friction の主因は discoverability か rules comprehension か
- 現在の first-play path は hidden reading dependency を含んでいるか
- 適切な compare は
  `with how-to-play page / without it`
  なのか、
  `optional page / required page`
  なのか

---

## What This Follow-up Decides

- first-question entry 問題の scope
- optional explanation と required explanation の区別
- 後続評価のための最小観点

---

## What This Follow-up Does Not Decide

- final UX solution
- final onboarding structure
- implementation changes
- 遊び方ページ自体を残すかどうか
- broader SoChi BLOCKS product strategy
