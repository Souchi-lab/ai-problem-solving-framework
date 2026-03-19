# FW Improvement Note

Date: 2026-03-19
Theme: Build 自動進行ポリシーの明文化
Scope: APSF phase boundary / CLI behavior / run operating rules

---

## One-Line Summary

`plan.md` 作成後に Builder が build に進む挙動は、現状では「便利だが暗黙」であり、
FW としては **許可条件つきで明文化する** か **明示承認なしでは禁止する** かを決める必要がある。

---

## Trigger

SoChi BLOCKS の運用中に、

- Planner で `plan.md` を整えたあと
- Builder / 実行担当が build にそのまま進む
- しかしその判断が framework 上の正式ルールとして明記されていない

というズレが露出した。

特に実験系 run では、

- build を止めるべきケース
- build まで自動で進んでよいケース
- publish まで進めてよいケース

の境界が重要になる。

---

## Current State

### 文書上

- [`framework/cli-orchestrator.md`](C:/Users/PC_User/PRJ/ai-problem-solving-framework/framework/cli-orchestrator.md#L125) では `apsf act <run-name>` は 1 回の実行で 1 phase のみ処理すると書かれている
- 同時に Auto 担当 phase は `plan.md / build.md / review.md` とされており、どこまで連続進行してよいかは曖昧
- [`framework/templates/plan.md`](C:/Users/PC_User/PRJ/ai-problem-solving-framework/framework/templates/plan.md#L79) には Build 開始前チェックがあるが、承認の要否は固定されていない

### 実運用上

- 実験系 run では `plan -> build準備 -> publish` を連続で扱いたい圧力が強い
- 一方で code / docs 系 run では phase を勝手に跨ぐと責務境界が緩みやすい
- 現状は user / operator の期待と AI 側の自律進行が run ごとにぶれる

---

## Problem

以下が未定義のまま運用されている。

1. `plan.md` が埋まったら Builder は build に進んでよいのか
2. build までで止まるのか、publish / execute まで進んでよいのか
3. どの条件を満たせば「自動進行可」と判断するのか
4. その判断を run ローカルではなく FW の共通規約としてどこに置くのか

このままだと、

- phase 境界レビューがしにくい
- `plan.md` の粒度が run ごとに変わる
- CLI 説明と実運用が再び乖離する

---

## Design Options

### Option A: 明示承認があるまで build 自動進行を禁止

**Rule**

- Planner は `plan.md` まで
- Builder は人または CLI の明示的な build 開始でのみ動く

**Pros**

- phase 境界が最も明確
- 監査しやすい

**Cons**

- 実験系 / コンテンツ系 run ではテンポが悪い
- 実運用で「結局毎回許可する」形になりやすい

### Option B: `plan.md` に Build 許可条件が書かれていれば自動進行可

**Rule**

- Planner は `plan.md` に `Build / Publish Policy` と停止条件を書く
- Builder はその条件を満たす場合のみ build に進む
- publish 実行まで進んでよいかは別フィールドで明示する

**Pros**

- 自律性と境界管理のバランスがよい
- 実験系 run に向く
- `plan.md` の品質要求が上がる

**Cons**

- template と CLI の両方を更新しないと中途半端になる

### Option C: run archetype ごとに既定値を持つ

**Rule**

- code run / experiment run / content run など archetype を定義
- archetype ごとに build 自動進行の既定値を持つ

**Pros**

- 実験系 run の使い勝手がよい

**Cons**

- archetype 導入コストが高い
- v0.1 のシンプルさを崩しやすい

---

## Recommendation

現時点では **Option B** が妥当。

理由:

- 既存 APSF は phase 境界を重視しており、全面自動進行の既定化は強すぎる
- しかし実験系 run では build を毎回手動確認にすると運用負荷が高い
- `plan.md` に build 許可条件と停止条件を書かせれば、run ごとの判断を一次記録に残せる

---

## Proposed Rule Draft

`plan.md` に以下が明記されている場合のみ、Builder は build に自動進行してよい。

- build 対象成果物
- build 開始前チェック
- build に進んではいけない停止条件
- publish / execute まで進めるかどうか
- 外部入力の参照元

逆に、上記が欠けている場合は build に進まず Planner へ差し戻す。

---

## Expected Framework Changes

### 文書

- `framework/templates/plan.md`
  `Build / Publish Policy` または同等セクションを追加
- `framework/agents/builder.md`
  build 自動進行の許可条件と差し戻し条件を追加
- `framework/cli-orchestrator.md`
  `1 phase だけ処理` と `Auto phase` の関係を整理

### 実装

- phase 実行時に `plan.md` の build 許可条件を評価できる設計にする
- 将来的には `NextInstructionBuilder` 側で「次は build 可能 / 不可」を返せるとよい

---

## Suggested Follow-Up Run

- `apsf_build-auto-progression-policy`

目的:

- build 自動進行ポリシーの正規定義
- plan template 更新
- builder prompt / CLI 説明の整合

---

## Related Evidence

- [`framework/cli-orchestrator.md`](C:/Users/PC_User/PRJ/ai-problem-solving-framework/framework/cli-orchestrator.md#L123)
- [`framework/templates/plan.md`](C:/Users/PC_User/PRJ/ai-problem-solving-framework/framework/templates/plan.md#L79)
- [`framework/agents/builder.md`](C:/Users/PC_User/PRJ/ai-problem-solving-framework/framework/agents/builder.md#L35)
- [`plan.md`](C:/Users/PC_User/PRJ/ai-problem-solving-framework/runs/2026-03-18-016_sochi-blocks_x-post-experiment/plan.md#L75)
