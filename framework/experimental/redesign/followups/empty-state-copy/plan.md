# Plan

---

## Follow-up Context

- Parent series:
  SoChi BLOCKS 初回体験改善
- Previous result:
  初回導線では
  `説明量`
  より
  `迷わず始められること`
  を優先する方向が見えている
- New trigger:
  `Cleared: 0 / 0`
  のような空状態表示が、
  未開始ではなく
  `壊れている表示`
  に読まれる可能性がある
- Scope limit:
  空状態の文言と見せ方の整理のみ
- Non-goals:
  進捗システム redesign / 数値ロジック変更 / 実装全体の再設計

---

## Run Metadata

- Follow-up:
  empty-state-copy
- Goal:
  空状態を
  `壊れて見えない`
  `まだ始めていないと自然に分かる`
  表示へ整理する
- Output focus:
  空状態文言の改善方針と差し替え案
- Non-goal reminder:
  進捗 UI 全体の redesign ではない

---

## Goal Readiness Check

- 主語は
  `空状態表示の改善`
  に固定されている
- scope は narrow で、
  文言と見せ方に留まっている
- result では
  `不安を減らしそうか`
  を narrow に評価できる
- 最大の drift risk は
  `進捗 UI 全体を直したくなること`
  である

Decision:
Proceed

---

## Execution Intent

今回やるのは、
進捗システムを作り直すことではない。

やることは、
未開始状態で
`0 / 0`
のような数値を見せることが
初見にとって自然かを見直し、
必要なら
`未開始`
を言葉で伝える方向へ寄せることである。

出力の中心は、
`何を表示するべきか`
より先に、
`何を表示しない方が自然か`
を決めることである。

---

## Problem Structure

今回の問題は、
値がゼロであること自体ではない。

問題は、
そのゼロ表示が
初見ユーザーにとって
`未開始`
として読まれるか、
それとも
`壊れている`
と読まれるかである。

したがって今回の観点は次の3つで十分である。

1. Meaning clarity
   - 空状態の意味が自然に伝わるか
2. Broken-looking risk
   - UI が不具合のように見えないか
3. Next-step guidance
   - 次に何をすればよいかが一言で分かるか

---

## Selected Approach

Approach:
空状態では、
数値の提示を優先せず、
`まだ始めていない`
という状態の意味を短く伝える文言へ置き換える。

Reasoning:
初回体験改善の文脈では、
正確なゼロ値の可視化より、
迷いと不安を減らすことの方が重要である。

---

## Scope Policy

この follow-up に含めるもの:

- 空状態文言の改善
- 空状態での短い補助文
- 必要なら最小限の CTA 接続

この follow-up に含めないもの:

- 進捗表示ロジックの変更
- 実績や履歴画面の redesign
- 通常状態の UI 文言見直し
- データ構造の変更

---

## Improvement Direction

### 1. ゼロ値の直表示を避ける

空状態では、
`Cleared: 0 / 0`
のような数値表現をそのまま前面表示しない方がよい。

### 2. 未開始を状態として見せる

空状態は
`まだプレイ履歴はありません`
のように、
意味が自然に通る言い方へ寄せる。

### 3. 次の一歩を短く出す

必要なら
`最初の1問から始めましょう`
のように、
次の行動を短く添える。

---

## Candidate Output Shape

### Current Read

- 現状表示:
  `Cleared: 0 / 0`
- 問題:
  未開始より壊れ表示に見えやすい

### Proposed Replacement

- Primary line:
  `まだプレイ履歴はありません`
- Secondary line:
  `最初の1問から始めましょう`

### Optional Variant

- Primary line:
  `まだクリア記録はありません`
- Secondary line:
  `まずは1問プレイしてみましょう`

---

## Deliverables

- 空状態改善の判断方針
- 差し替え候補文言
- `壊れて見えない` ための判断基準
- narrow result に渡せる着地案

---

## Review Checklist

- 主語が空状態表示に留まっている
- `未開始`
  が自然に読める方向になっている
- 進捗 UI 全体の redesign に広がっていない
- 次の一歩が短く見える
- 数値ロジック変更を前提にしていない

---

## Planned Output Shape

- Current issue
- Improvement direction
- Replacement copy candidates
- Narrow evaluation
  - 壊れて見えにくくなったか
  - 次の行動が見えやすくなったか

---

## Assumptions & Open Questions

Assumptions:

- 初見ユーザーは
  `0 / 0`
  を進捗ゼロではなく異常表示として読む可能性がある
- 空状態では、
  数値より状態の意味を優先した方が自然である

Open questions:

- 空状態に CTA を直接添えるべきか
- `プレイ履歴`
  と
  `クリア記録`
  のどちらが自然か

---

## What This Follow-up Decides

- 空状態で優先すべき表示原則
- 差し替え文言の方向

---

## What This Follow-up Does Not Decide

- 進捗 UI 全体の最終仕様
- データの持ち方
- 通常状態のコピー方針
