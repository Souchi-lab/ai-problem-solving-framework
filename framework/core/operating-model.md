# Operating Model

## ねらい

APSF は、役割分担・判断境界・ durable artifact を明確にして、
AI と人間が同じ run を安全に引き継げるようにする運用モデルです。

特に重要なのは次の 3 点です。

- role と provider / model を混同しない
- canonical artifact を phase ごとに分ける
- handoff や model choice は「必要なときだけ」記録する

> 重要: APSF で最も強い build 実行権限を持つモデルは Build に集中させる。
> Plan / Review / Improve は判断責務を保ち、Builder の代わりに phase をまたいで書かない。

---

## role / provider / model の分離

```text
role     = 何をするか   (Planner / JuniorBuilder / Builder / Critic / Judge)
provider = どこの API を使うか   (OpenAI / Anthropic / Gemini)
model    = どのモデルを使うか   (gpt-4o / claude-sonnet / gemini-flash など)
```

悪い例:

```text
ClaudeBuilder
GeminiPlanner
```

良い例:

```text
Builder uses AnthropicProvider(model="claude-sonnet")
Critic uses OpenAIProvider(model="gpt-4o")
```

run ごとの具体割当は、必要に応じて `model-assignment.md` に記録する。

---

## 標準 role

| role | 役割 | 備考 |
|---|---|---|
| Planner | 問題の整理、選択肢比較、方針決定 | build 境界を決める |
| JuniorBuilder | 任意の補助 build | main build の代替ではない |
| Builder | 実装・生成・ build 記録 | 最も強い build 権限を持つ |
| Critic | 独立レビュー | build の代わりに直さない |
| Judge | accept / iterate の判断 | 最終判断責務 |
| Human | 必要に応じて各 role を兼任 | governance の最終責任者 |

---

## Artifact Trigger Policy

軽量化後の APSF では、`handoff.md` と `model-assignment.md` を残しつつ、
無条件 boilerplate としては扱わない。

### `handoff.md`

次の role が canonical artifact だけでは transfer context を失う場合に使う。

Required when:

- role / model / tool / person / session の境界をまたぎ、文脈落ちのリスクがある
- 次の role に非自明な review focus、execution caution、open issue、constraint を渡す必要がある
- canonical artifact に残っていない運用上の注意を transfer しないと downstream 判断がぶれる

Skippable when:

- 同じ operator が同じ session で継続し、transfer risk が実質ない
- `plan.md` / `build.md` / `review.md` などの canonical artifact だけで次 role が動ける
- handoff を書いても既存 artifact の言い換えにしかならない

`handoff.md` は transfer note であり、phase artifact の代替ではない。

### `model-assignment.md`

model choice 自体が run の品質、独立性、コスト、再現性に影響する場合に使う。

Mandatory when:

- 複数 provider / model や non-default role assignment を意図的に使う
- review independence を distinct model/provider choice で担保する
- capability / safety / policy 制約のため model choice を明示記録する必要がある

Recommended when:

- cost / latency / availability tradeoff が run の進め方に影響する
- external critic、parallel review、provider comparison を予定している
- rerun 時に「なぜその setup を選んだか」を残す価値が高い

Optional when:

- obvious default setup で、model choice が outcome にほぼ影響しない
- multi-model tradeoff を後から参照する必要がない

Template references:

- [`framework/templates/handoff.md`](../templates/handoff.md)
- [`framework/templates/model-assignment.md`](../templates/model-assignment.md)

---

## モデル割当の指針

以下は標準指針であり、run ごとに必要なら上書きしてよい。

| role | 標準候補 | 意図 |
|---|---|---|
| Planner | GPT-4o / Claude Opus / Human | 比較・判断・方針言語化 |
| JuniorBuilder | Gemini Flash / GPT-4o mini | 軽量補助作業 |
| Builder | Claude Sonnet / Claude Opus | 強い build 実行 |
| Critic | GPT-4o / Human | Builder と独立した視点 |
| Judge | Human | accept / iterate の最終責任 |

Builder と Critic は、可能なら異なる model / provider を使う。
同系統モデルを使う場合でも、review independence が落ちないかを意識する。

---

## handoff の重要性

handoff は「常に作るもの」ではなく、「必要な transfer risk があるときにだけ作るもの」です。

典型例:

```text
Planner -> (handoff.md if needed) -> Builder
Builder -> (handoff.md if needed) -> Critic
Critic  -> (handoff.md if needed) -> Judge / Improve
```

書くなら次の 3 点に絞る。

- 何が決まっているか
- 何が未決か
- 次の role は何を優先確認すべきか

---

## run ごとの model assignment

`model-assignment.md` は毎 run 強制ではない。
上の trigger policy に従い、必要な run だけ記録する。

使う価値が高いケース:

- role ごとに provider / model を分ける run
- critique independence が重要な run
- cost / latency / provider choice が outcome に効く run
- 後から rerun / comparison したい run

---

## 人間が入るべき局面

| タイミング | 理由 |
|---|---|
| Goal | 問題設定と成功条件の最終責任 |
| Planner が迷うとき | 方針判断の境界確認 |
| Judge | accept / iterate の最終判断 |
| Improve | 差し戻し範囲の最終決定 |

AI が強いのは Plan / Build / Review の実務支援だが、
Goal と Judge を人間が押さえることで運用の安定性が上がる。

---

## まとめ

APSF の operating model は次のように解釈する。

- phases が purpose と stop condition を定義する
- roles が誰がどの artifact を書けるかを定義する
- artifacts が durable record を定義する
- `handoff.md` と `model-assignment.md` は trigger-based に使う

今後の framework 更新で文書が衝突した場合は、
この operating model を正本として alignment する。
