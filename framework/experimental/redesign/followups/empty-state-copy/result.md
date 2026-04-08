# Result

---

## Result Target

- Target series:
  `framework/experimental/redesign/followups/empty-state-copy`
- Included artifacts:
  - `goal.md`
  - `plan.md`
- Result type:
  follow-up result
- Result question:
  この follow-up は、
  空状態を
  `壊れて見えない`
  `まだ始めていないと自然に分かる`
  表示へ整理する narrow run として
  妥当に閉じられているか

---

## Final Verdict

- Verdict:
  Accept

この follow-up は、
small follow-up として妥当に成立している。

今回の主語は、
進捗 UI 全体の redesign ではなく、
空状態表示だけを
`未開始が自然に伝わるか`
という観点で見直すことであった。

`goal.md` と `plan.md` は、
この主語を narrow に保ったまま、
差し替え方向と判断基準を十分に定義できている。

また今回は、
変更範囲が小さく、
判断基準も明確であるため、
`review skip`
の運用判断も自然である。

---

## What Was Established

今回の follow-up で確立できたことは次のとおりである。

### 1. 問題はゼロ値そのものではなく、壊れて見えることである

今回の整理で重要だったのは、
`0 / 0`
という値の正しさを論じることではなく、
初見ユーザーにそれが
`未開始`
ではなく
`異常表示`
として読まれうる点を問題として切り出せたことである。

### 2. 空状態では数値より状態の意味を優先する

空状態では、
正確なゼロ値を見せることより、
`まだプレイ履歴はありません`
のように、
状態の意味が自然に通ることを優先すべきだと整理できた。

### 3. 次の一歩は短く添えるだけでよい

空状態の改善は、
大きな説明や複数導線を増やすことではない。

`最初の1問から始めましょう`
のように、
次に何をすればよいかが
1 行で分かる程度で十分である。

---

## Why This Follow-up Works

この follow-up が機能している理由は、
主語のサイズが適切だからである。

今回必要だったのは、
進捗 UI を広く見直すことではない。

必要だったのは、
空状態で
`壊れて見える`
を避け、
`未開始`
を自然に伝え、
必要なら
`次の一歩`
を一言で添えることだった。

そのため、
この系列は narrow に閉じたまま
Accept で終えることができる。

---

## Recommended Copy Direction

現時点で最も自然な方向は次である。

- Primary line:
  `まだプレイ履歴はありません`
- Secondary line:
  `最初の1問から始めましょう`

代替としては、

- Primary line:
  `まだクリア記録はありません`
- Secondary line:
  `まずは1問プレイしてみましょう`

も成立する。

ただし今回の方針では、
初回体験改善の流れと接続しやすい
`最初の1問`
の表現がやや優勢である。

---

## Boundaries Kept Intact

この result で重要なのは、
何を決めたかだけでなく、
何を決めていないかでもある。

今回の follow-up は以下を決定していない。

- 進捗 UI 全体の最終仕様
- 数値ロジックの変更
- 通常状態の表示方針
- 実績機能や履歴画面の redesign

これらは引き続き scope 外でよい。

---

## Stable Baseline

- 空状態では、
  数値の正しさより
  状態の意味が自然に伝わることを優先する
- `壊れて見えない`
  ことを最低条件に置く

---

## Open Conditional

- `プレイ履歴`
  と
  `クリア記録`
  のどちらが自然かは、
  実画面文脈で再確認の余地がある
- CTA を直接添えるかどうかは、
  他の導線との兼ね合いで調整余地がある

---

## Next Trigger

- 実画面で空状態がまだ硬く見える場合
- `プレイ履歴` より `クリア記録` の方が自然に見える evidence が出た場合
- 他の empty state にも同種の問題が見つかった場合

---

## Closing

この follow-up は、
空状態表示だけを対象にした軽量 run として十分に良い。

結論を広げすぎず、

- 壊れて見えない
- 未開始が自然に伝わる
- 次の一歩が短く見える

という3点を確定した状態で閉じるのが適切である。

したがって、
`framework/experimental/redesign/followups/empty-state-copy`
系列は
**Accept**
で完了としてよい。
