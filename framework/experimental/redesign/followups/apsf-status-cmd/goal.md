# Goal

---

## Follow-up Context

- Parent series: APSF GUI / CLI 寄り運用改善
- Previous result: `apsf init-followup <slug>` と `apsf list-followups` により、follow-up 作成と一覧確認の最小導線が CLI に着地した
- New trigger: 一覧表示だけでは「今どこが未完了か」「次に何を見るべきか」が分かりにくく、GUI 的な status view の前段が欲しい
- Scope limit: `apsf status` の最小設計と確認に限定する
- Non-goals: GUI 実装、全 run taxonomy の完全統合、viewer の再設計

---

## Goal Statement

GUI 中心の「ポチポチ運用」へ寄せる次の小実験として、
`apsf status`
コマンドを導入し、
現在の run / follow-up 状態を
「何が完了で、何が未完了で、次に何を見るべきか」
として軽く把握できるようにする。

今回の主語は、
完全な dashboard を作ることではない。

扱うのは、
CLI 上で最小の status view を成立させ、
`list` より一歩 GUI 的な
`current state + next attention`
を出せるかどうかである。

---

## Why This Follow-up Exists

`init-followup` は作成コストを下げた。
`list-followups` は存在確認をしやすくした。

ただし、
今の CLI にはまだ

- どこが in-progress か
- どこが review-skipped か
- どこを次に見ればよいか

を 1 画面で把握する入口が弱い。

これは北極星として置いている
GUI 中心運用の
`run type / required checks / next trigger`
にまだ十分近づいていないことを意味する。

したがって今回の follow-up は、
GUI の前段として
CLI で status 的な見え方を 1 歩先取りできるかを試すためにある。

---

## Success Criteria

1. `apsf status` の主語が「現在状態の要約」に固定されている
2. `list-followups` と役割が重複しすぎていない
3. `complete / in-progress / review-skipped` のような運用上意味のある見え方が得られる
4. 必要なら `next attention` を短く出せる
5. GUI 的 status view の前段として使えるかを result で評価できる

---

## Expected Outputs

- `goal.md`
- `plan.md`
- 必要なら `review.md` を省略
- `result.md`
- 最小の CLI 変更

---

## Non-Goals

- full dashboard
- viewer との統合
- 全 taxonomy / 全 phase の完全 status 表示
- GUI 実装そのもの

---

## Constraints

- `apsf status` は小さく始める
- `list-followups` の置き換えではなく補完にする
- 情報量より「次にどこを見るか」の分かりやすさを優先する
- 北極星に寄せるが、CLI の範囲で完結させる

---

## Notes For Planner

- 最初に決めるべきは、`status` が何を 1 行で表すかである
- `run type / required checks / next trigger` を全部入れようとしすぎない
- 今回は follow-up 群を中心にするのか、全 run を薄く横断するのかを早めに固定する
