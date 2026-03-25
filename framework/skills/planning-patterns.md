# Skill: Planning Patterns

## このスキルは何か

`framework/planning-patterns.md`（定義資産）の **使い方ガイド**。
定義ファイルは「各 P-TYPE とは何か」を説明し、このスキルは「plan.md を書くときにどう使うか」を手順として示す。二重管理を避けるため、P-TYPE の定義・例はすべて `framework/planning-patterns.md` を参照すること。

`framework/pattern-application-checklist.md` は overview.md 系パターン（P-01〜P-10）の判断補助であり、このスキルとは対象が異なる。

---

## いつ使うか（trigger）

- **plan.md を書き始めるとき** — P-TYPE を選んで Execution Plan と Implementation Readiness を組み立てるとき
- **P-TYPE に迷ったとき** — Recognition Signals を照合して判断したいとき
- **Review で「plan の構造が P-TYPE と合っているか」を確認するとき**

> このスキルは **user-triggered** を原則とする。agent が暗黙に起動することを想定しない。

---

## 手順

### Step 1: 主目的を 1 文で言い切る

goal.md の Goal Statement を読み、「今回の run は〇〇をする」を 1 文で言い切る。

- ✅ 「`RunRepository` に child run API を追加する」
- ✅ 「legacy run を taxonomy filesystem へ移行する」
- ❌ 「CLI を改善して taxonomy にも対応できるようにする」（主目的が 2 つ混在）

主目的が 2 つ以上になる場合は、run 分割を検討する。

### Step 2: Recognition Signals で P-TYPE 候補を絞る

以下のクイックリファレンスを使い、Step 1 の 1 文に合う P-TYPE を 1〜2 型に絞る。

| P-TYPE | Recognition Signals（キーワード） |
|---|---|
| P-01 Feature Implementation | 「新しく〜できるようにする」「〜を追加する」「新規能力」「新 API」 |
| P-02 Bug Fix | 「壊れている」「想定どおり動かない」「修正する」「regression」 |
| P-03 Refactoring | 「整理したい」「挙動は変えない」「構造改善」「保守性向上」「直〇〇を除去」 |
| P-04 Migration | 「移す」「移行する」「新方式へ切り替える」「配置変更」「legacy」 |
| P-05 Document / Template Update | 「README に反映」「template 更新」「文書を変更」「docs 追記」 |
| P-06 Design-only | 「設計だけ先に固める」「比較して決める」「実装は次 run」「handoff」 |
| P-07 Retrospective / Analysis | 「棚卸し」「振り返り」「inventory」「分析」「audit」「優先度整理」 |
| P-08 Research / Discovery | 「候補を収集する」「探索して選定する」「外部知見を取り込む」「shortlist」 |

> **Recommended Planner Tool（任意参照）**: P-TYPE が確定したら `framework/planning-patterns.md` の該当 P-TYPE の `Recommended Planner Tool` フィールドを確認できる。推奨は提示のみであり、Planner が自分の判断で別ツールを選んでよい。

### Step 3: Boundary で 1 型に確定する

候補が 2 型残った場合、`framework/planning-patterns.md` の該当 P-TYPE の `Non-Examples / Boundary` を読んで 1 型に絞る。

**よくある境界ケース**:

| 判断ポイント | 型 |
|---|---|
| 新能力を追加するか、既存挙動を直すか | P-01 vs P-02 |
| 外部挙動を変えるか、内部構造を整理するだけか | P-01 vs P-03 |
| 構造整理か、配置・保存先の移行か | P-03 vs P-04 |
| 設計を決めるか、決まった設計を書くか | P-05 vs P-06 |
| 内向きの振り返りか、外部からの探索か | P-07 vs P-08 |

primary pattern が確定したら、必要な場合のみ secondary pattern を 1 つ添える。

### Step 4: Execution Plan Shape を plan.md に写す

`framework/planning-patterns.md` の確定した P-TYPE の `Execution Plan Shape` を参照し、plan.md の `## Execution Plan` の骨格として使う。

```
# 例: P-04 Migration の場合
Execution Plan Shape: 方式確定 → 実装 → 限定移行 → cross-reference 更新 → 回帰確認

→ plan.md に:
- [ ] Step 1: 移行方式・対象一覧の確定
- [ ] Step 2: 移行スクリプト / 手順の実装
- [ ] Step 3: 限定移行（1〜2 件で動作確認）
- [ ] Step 4: cross-reference 更新
- [ ] Step 5: 回帰確認（テスト全件パス）
```

### Step 5: Readiness Implications を Implementation Readiness に接続する

`framework/planning-patterns.md` の確定した P-TYPE の `Readiness Implications` を読み、plan.md の `## Implementation Readiness` の観点として使う。

```
# 例: P-04 Migration の場合
Readiness Implications: 移行単位、legacy policy、fallback 順序を build 前に固定する。参照更新範囲を事前に列挙する。

→ Implementation Readiness の確認項目に:
- [ ] 移行単位が確定している
- [ ] legacy fallback 方針が決まっている
- [ ] cross-reference 更新対象を列挙できる
```

---

## 注意事項

- **過剰適用しない**: すべての run に P-TYPE を機械的に当てはめる必要はない。Planner の思考補助が目的であり、分類自体が目的にならないようにする。
- **1 run 1 primary pattern**: primary が 2 つになる場合は run 分割を検討する。secondary は補助的に 1 つまで。
- **P-TYPE は手段**: pattern 名が先に決まると run 設計が歪む。主目的から選ぶ。
- **このスキルは user-triggered**: Planner が plan.md を書くときに参照するもの。agent が自動起動することを想定しない。
