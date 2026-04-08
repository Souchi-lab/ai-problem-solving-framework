# Plan

---

## Follow-up Context

- Parent series: APSF GUI / CLI 寄り運用改善
- Previous result: `apsf init-followup <slug>` と `apsf list-followups` により、作成と一覧確認の最小導線は CLI に着地した
- New trigger: 一覧確認はできるが、「今どこが未完了で、次に何を見るべきか」を 1 画面で把握する入口がまだ弱い
- Scope limit: `apsf status` の最小 CLI 実装に限定する
- Non-goals: GUI 実装、viewer 統合、全 run taxonomy の完全 dashboard 化

---

## Goal Readiness Check

- `goal.md` は `apsf status` を最小 status view として定義している
- `list-followups` がすでにあり、役割差分を設計できる前提がある
- 今回の主語は feature implementation であり、設計だけで閉じない
- GUI 北極星は参照するが、今回は CLI で 1 歩寄せる段に留める

Decision: Proceed

---

## Problem Structure

今回先に固定すべき論点は 2 つである。

### 1. `status` が何を 1 行で表すか

今回の `status` は、
詳細一覧ではなく
`current state + next attention`
を短く返すものとして扱う。

したがって 1 行は、
少なくとも次のどちらかを持つべきである。

- 状態要約
  - `complete`
  - `in-progress`
  - `review-skipped`
- 次に見るべき点
  - `Missing: result.md`
  - `Next: write result.md`

### 2. スコープをどこまで広げるか

今回は **follow-up 群中心** にする。

理由:

- すでに `init-followup` / `list-followups` が follow-up 軸で存在している
- GUI 北極星に寄せるにも、最初は狭い運用単位で試した方がよい
- 全 run 横断にすると taxonomy / phase 差分まで一度に扱う必要が出て、初回として重い

したがって今回の `apsf status` は、
まず `framework/experimental/redesign/followups/` を対象にして、
`list-followups` より一歩先の見え方を与えることを目的とする。

---

## Selected Approach

### 役割分担

- `apsf list-followups`
  - 何が存在するかを見る
- `apsf status`
  - 今どれが未完了で、次にどこを見るべきかを見る

`status` は `list` の置き換えではなく、
「いま注意が必要なものだけを絞る」補完コマンドとして置く。

### 最小出力形

今回は次の形で十分とする。

- ヘッダ
  - follow-up 全体件数
  - `in-progress` 件数
- 本文
  - `in-progress` の follow-up を優先表示
  - `complete (review-skipped)` は簡潔表示または省略
  - 必要なら `Missing:` を添える

つまり `list` より少なく、
status と next attention に寄せる。

### 変更対象

初手は最小限で進める。

- `src/apsf/cli/main.py`

必要なら既存の follow-up 走査ロジックを再利用する。
repository 層の新設や viewer 連携は今回は持ち込まない。

---

## Working Definitions

今回の `status` で使う意味は次で固定する。

- `complete`
  - `result.md` があり、`review.md` もある
- `complete (review-skipped)`
  - `result.md` はあるが `review.md` はない
- `in-progress`
  - `result.md` がない

`next attention` は、
`in-progress` に対してだけ短く出す。

例:

- `Missing: result.md`
- `Missing: plan.md, result.md`

今回は phase 推定を細かくしすぎない。
既存の `list-followups` と同じ判定軸を使い、
見せ方だけを status 寄りに変える。

---

## Execution Plan

### Step 1. 出力仕様を固定する

`status` が 1 行で何を表すか、
follow-up 中心でどこまで出すかを先に固定する。

### Step 2. 変更対象を確定する

`src/apsf/cli/main.py` のみで完結できるか確認する。
追加の repository 変更は初手では避ける。

### Step 3. `apsf status` を実装する

follow-up 群を走査し、
`current state + next attention`
を返すコマンドを追加する。

### Step 4. 動作確認を行う

少なくとも手動で次を確認する。

- `apsf status` が起動する
- `in-progress` が優先して見える
- `review-skipped` が自然に表現される
- `list-followups` と役割重複しすぎていない

### Step 5. result で運用価値を評価する

北極星に対して、
GUI 的 status view の前段として意味があるかを短く評価する。

---

## Scope Policy

### 含めるもの

- `apsf status` コマンドの新規追加
- follow-up 群の状態要約
- `next attention` の最小表示

### 含めないもの

- GUI 実装
- viewer 連携
- 全 run 横断 status
- taxonomy / phase の完全統合表示

---

## Deliverables

- `goal.md`
- `plan.md`
- 最小 CLI 実装
- 手動確認
- `result.md`

---

## Review Policy

今回は実装規模が小さいため、
`review.md` は必須にしない。

代わりに `result.md` で次を回収する。

- `status` が `list` と差別化できているか
- follow-up 運用で本当に見やすくなったか
- GUI 北極星への 1 歩として妥当か

---

## Expected Landing

この run の着地は、
CLI で `apsf status` を打つと
「今どれが未完了で、次にどこを見るべきか」
が軽く見える状態である。

これはまだ GUI ではない。
ただし、
GUI の `status view`
に近い判断導線を CLI 上で先取りする
小さな 1 歩として十分である。
