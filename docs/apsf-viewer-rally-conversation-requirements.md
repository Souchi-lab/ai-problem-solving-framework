# APSF Viewer Rally Conversation Requirements

## Purpose

APSF Viewer の `Auto-Loop` 周辺で、run の進行状況を人間が一目で追えるようにする。

この機能は単なる artifact 一覧ではなく、

- 今だれが担当なのか
- 今ほんとうに実行されているのか
- どこまで進んで、次に何が未作成なのか
- Builder / Critic / Judge のラリー内容がどう流れたのか

を短時間で把握できることを目的とする。

---

## Target Screen

Viewer の run detail 画面内、`Auto-Loop` セクション。

---

## Core User Problems

現状の問題は次のとおり。

1. `build.md` / `review.md` / `improve.md` / `result.md` は存在しても、一覧表示だけではラリーの流れが読みにくい。
2. 「Current Worker」が次担当なのか、実行中の担当なのかが分かりづらい。
3. `Elapsed` が「実行時間」なのか「待機時間」なのか分かりづらい。
4. 未作成 artifact が全部並ぶと、現在地よりノイズが勝つ。
5. markdown 全文は長すぎるため、現在地確認には不向き。

---

## Feature Scope

この機能で提供したいもの:

- `View Rally` ボタン
- `Rally Conversation` modal
- `Current Worker / Status / Elapsed` の明確表示
- Builder / Critic / Judge の artifact を会話風に読む UI
- markdown 全文ではなく短い要約表示

この機能で提供しないもの:

- artifact の編集
- auto-loop の内部ログ全文表示
- markdown の完全レンダリングを conversation modal 上で主用途にすること
- 実行プロセス監視の完全なジョブ管理画面

---

## Functional Requirements

### 1. Worker Status Card

`Auto-Loop` セクションには次の情報を常時表示する。

- `Current Worker`
- `Status`
- `Elapsed`

表示ルール:

- `Current Worker`
  - `run_state.json.current_owner` を優先する
  - 無い場合は phase から推定した next role を使ってよい

- `Status`
  - `phase_status == in_progress` の場合: `実行中`
  - `phase_status == pending` の場合: `待機中`
  - その他は state の値をそのまま人間向け表示してよい

- `Elapsed`
  - 実行中の場合は、現在の action 実行開始からの経過時間を出す
  - 待機中の場合は、`run_state.phase_entered_at` からの経過時間を出す
  - 値は `mm:ss` か `hh:mm:ss` 相当でよい

### 2. Actual Execution Truth

UI は「次担当」と「実行中」を混同してはいけない。

解釈ルール:

- `current_owner = Builder` かつ `phase_status = pending`
  - 表示上は「Builder が担当だが、まだ実行中ではない」
- `current_owner = Builder` かつ `phase_status = in_progress`
  - 表示上は「Builder がいま作業中」

### 3. View Rally Button

`Auto-Loop` セクションに `View Rally` ボタンを置く。

押したときに `Rally Conversation` modal を開く。

### 4. Rally Conversation Modal

modal は artifact 一覧ではなく、会話形式に見える feed を表示する。

見た目ルール:

- `B` = Builder
- `C` = Critic
- `J` = Judge
- `R` = Result / Goal

表示イメージ:

```text
B
text1

        C
        text2

B
text3
```

つまり、

- Builder 系は左寄せ
- Critic 系は右寄せ
- Judge / Result は左寄せでもよい

### 5. Artifact-to-Speaker Mapping

最低限、次の対応を持つ。

- `goal.md` -> `R`
- `plan.md` -> `J` または planning lane
- `build.md` -> `B`
- `build_review.md` -> `J`
- `review.md` -> `C`
- `review_review.md` -> `J`
- `improve.md` -> `J`
- `improve_review.md` -> `J`
- `result.md` -> `R`

### 6. Summary Instead of Full Markdown

conversation modal では markdown 全文をそのまま見せない。

代わりに:

- artifact ごとに短い要約を表示する
- 可能であれば日本語で表示する
- 要約は current status を把握するのに十分な長さに止める

要約ルールの例:

- `plan.md` -> 「計画」+ 主要 bullet 2〜3 件
- `build.md` -> 「実装報告」+ 実装項目 2〜3 件
- `review.md` -> 「判定」+ finding 要約 2〜3 件
- `improve.md` -> 「判断」+ next step
- `result.md` -> 「結果」+ closeout 要約

### 7. Missing Artifact Display Rule

未作成 artifact は全部表示しない。

表示ルール:

- 既に存在する artifact は表示する
- 未作成 artifact は **直近の 1 件だけ** 表示する
- 表示文言は `_未作成_` でよい

例:

- `goal.md`, `plan.md` あり
- `build.md`, `review.md`, `improve.md`, `result.md` なし

この場合の表示:

- `goal.md`
- `plan.md`
- `build.md` -> `_未作成_`

`review.md` 以降の未作成は出さない。

### 8. Current Phase Visibility

Rally modal を開いた時点で、

- run name
- 現在の phase

が分かること。

---

## UX Requirements

### 1. Readability First

この modal は「読んで把握する」ためのものなので、

- artifact 名の正確さ
- だれの発話か
- 直近で何が起きたか

が最優先である。

### 2. Low Noise

未作成 artifact を全部見せてはいけない。

理由:

- 現在地より未来の空欄が目立つ
- ユーザーが「いまどこまで進んだか」を見失う

### 3. Japanese Preference

要約文・状態ラベルは可能な限り日本語を優先する。

対象:

- `実行中`
- `待機中`
- `計画`
- `実装報告`
- `判定`
- `結果`
- `_未作成_`

---

## Non-Functional Requirements

### 1. Source of Truth

状態判定の source of truth は次を優先する。

1. `run_state.json`
2. viewer backend の execution status
3. artifact existence

artifact の有無だけで「実行中」と判定してはいけない。

### 2. Failure Handling

artifact 読み込みに失敗した場合:

- modal は閉じない
- エラー内容を 1 発話として表示してよい

### 3. Build Safety

フロント変更後は `npm run build` が通ること。

---

## Acceptance Criteria

### Scenario A: Plan only

状態:

- `plan.md` まで存在
- `build.md` 未作成
- `phase = BUILD_NEEDED`
- `phase_status = pending`

期待:

- Worker card は `Builder / 待機中 / phase経過時間`
- Rally modal は
  - `goal`
  - `plan`
  - `build -> _未作成_`
  - それ以降は出さない

### Scenario B: Build complete, review pending

状態:

- `build.md` 存在
- `review.md` 未作成
- `phase = REVIEW_NEEDED`

期待:

- Rally modal は
  - `goal`
  - `plan`
  - `build`
  - `review -> _未作成_`

### Scenario C: Review returned to build

状態:

- `build.md`
- `review.md`
- `build_review.md`

期待:

- Rally modal 上で `B -> C -> J` の順が見える
- `Judge` の返しが会話として追える

### Scenario D: In Progress

状態:

- `phase_status = in_progress`
- 実行 action が走っている

期待:

- Worker card は `実行中`
- `Elapsed` は action 開始から増え続ける

---

## Suggested Future Extensions

- artifact 要約を backend 側で生成し、frontend は表示だけにする
- `View Rally` に phase filter を追加する
- `Builder only / Critic only / All` の lane 切り替え
- auto-loop log と conversation feed の連携

---

## One-Line Handoff Summary

APSF Viewer に、run の artifact ラリーを `B / C / J / R` の会話形式で、日本語要約ベース・低ノイズ・現在地重視で読める `Rally Conversation` modal を提供し、同時に `Current Worker / Status / Elapsed` で今ほんとうに誰が作業中かを明確に見せる。
