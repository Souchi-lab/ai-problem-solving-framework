# _template

## run の始め方

```bash
apsf init-run YYYY-MM-DD_case-key_topic
# または手動で:
cp -r runs/_template runs/YYYY-MM-DD_case-key_topic
```

---

## ファイルを埋める順番

**run 開始前に `execution-assignment.md` と `model-assignment.md` を作成すること。**
「どうやって実行するか」と「どのモデルを使うか」を決めずに進めない。

```
0. execution-assignment.md  ← run 開始前：各 role の実行手段を決める（★ 最初に）
   model-assignment.md      ← run 開始前：各 role のモデルを決める（CLI 実行では参考情報）
1. goal.md              ← 何を解くかを明確にする（人間が書く）
2. plan.md              ← Planner が作成
3. handoff.md           ← Planner → Builder へ引き渡し（初回）
4. build.md             ← Builder が作成
5. handoff.md           ← Builder → Critic へ更新
6. review.md            ← Critic が作成
7. handoff.md           ← Critic → Judge へ更新
8. improve.md           ← 人間（Judge）が判断
9. result.md            ← ループ完了時に人間が作成
──────────────────────────────────────────────────
[補助] transcript.md   ← result.md 完了後に生成（optional / 初回 run では強く推奨）
```

---

## execution-assignment.md について

### いつ埋めるか

**run を切る前（`apsf init-run` の直後）に記入する。**

goal.md を書く前に実行手段を決めておくことで、
「このステップは誰がどのツールで実行するか」を全員（と自分）が共有できる。

### model-assignment.md との違い

| ファイル | 問い | 主な用途 |
|---|---|---|
| `execution-assignment.md` | **どうやって実行するか** | cli / human / future-api の選択 |
| `model-assignment.md` | **どのモデルを使うか** | OpenAI / Anthropic / Gemini の選択 |

v0.1 では CLI / Human 実行が主体のため、`execution-assignment.md` が中心。
`model-assignment.md` は将来 future-api executor を使う際の参考情報として残す。

### handoff.md との関係

`execution-assignment.md` は **run 全体の実行手段設定**（変わらない）。
`handoff.md` は **ステップ間の受け渡し内容**（step ごとに更新する）。

```
execution-assignment.md  → 「Builder は claude CLI で実行する」という設定
handoff.md               → 「Builder へ: plan.md のこの部分を重点的に」という指示
```

handoff.md を更新するタイミング:
- Planner → Builder へ渡すとき
- Builder → Critic へ渡すとき
- Critic → Judge へ渡すとき

---

## transcript.md について

### 何か

run 完了後に一次記録（goal.md 〜 result.md）を**役割別の発言形式で再構成した可読化文書**（二次成果物）。
正式記録の置き換えではなく、読みやすさ・共有性・振り返り性を高めるための補助ファイル。
逐語ログでも会話の再現でもない。正確な情報が必要な場合は必ず一次記録を参照すること。

### いつ作るか

**result.md を書いた後**。途中生成は事実が不完全になるため避ける。

### 何を書くか

以下の問いに会話形式で答える:
- Planner は何を構造化したか（problem structure・品質基準・handoff 内容）
- JuniorBuilder はどんな叩き台を出したか（該当する場合）
- Builder は何を完成させたか（成果物・採用した判断・逸脱）
- Critic は何を指摘したか（Critical / Major / Minor の要点）
- Judge はどう決めたか（採用・修正・却下、その理由）
- Result として何が一般化されたか（Generalization の要点）

### どう書くか

役割別の発話ブロックで記述する。各引き継ぎ（handoff）は引用ではなく要約で書く。

```
**Planner**: goal.md を読んで X・Y・Z を構造化した。採用アプローチは A。

Planner から Builder への引き継ぎ要点:
変数形式・トーン・カテゴリ分類を決定した。
ハッシュタグ戦略は未解決のまま Builder に委ねた。

**Builder**: A・B・C を作成した。Plan から逸脱した点は D（理由: E）。

Builder から Critic への引き継ぎ要点:
F の観点を重点的に評価してほしい。G は未検討のため Critic の判断に委ねた。

**Critic**: Critical なし、Minor 2 点。G の点に改善余地あり（Low）。

Critic から Judge への引き継ぎ要点:
採用推奨。Minor 2 点は次 run での対応を提案。

**Judge**: 採用。Minor は次 run で対応する。
```

**引用ブロック（>）を使うのは、元ファイルの原文を「そのまま」転記する場合のみ。**
迷ったら引用より要約が安全。

### 参照するファイル

```
execution-assignment.md / goal.md / plan.md / handoff.md /
build.md / review.md / improve.md / result.md
（必要に応じて workspaces/*/draft-*.md も参照）
```

### 生成方法

**手動**:
1. `transcript.md` のひな型を開く
2. 各セクションを対応ファイルを参照しながら記述する
3. 事実ベースで書く。元ファイルにない内容は書かない

**CLI 補助**:
```bash
apsf generate-transcript <run-name>
# 参照ファイル一覧と各セクションの記入ガイドを表示する
```

---

## 各ファイルの参照先

| ファイル | 原本テンプレート | 担当 | 種別 |
|---|---|---|---|
| `execution-assignment.md` | `framework/templates/execution-assignment.md` | 人間（run 開始前） | 一次記録 |
| `model-assignment.md` | `framework/templates/model-assignment.md` | 人間（run 開始前） | 一次記録 |
| `goal.md` | `framework/templates/goal.md` | 人間 | 一次記録 |
| `plan.md` | `framework/templates/plan.md` | Planner | 一次記録 |
| `handoff.md` | `framework/templates/handoff.md` | 各 role が更新 | 一次記録 |
| `build.md` | `framework/templates/build.md` | Builder | 一次記録 |
| `review.md` | `framework/templates/review.md` | Critic | 一次記録 |
| `improve.md` | `framework/templates/improve.md` | 人間 | 一次記録 |
| `result.md` | `framework/templates/result.md` | 人間 | 一次記録 |
| `transcript.md` | `framework/templates/transcript.md` | 人間（or AI 補助） | **二次成果物** |

---

## framework/templates/ と runs/_template/ の違い

| パス | 役割 |
|---|---|
| `framework/templates/` | **設計資産の原本**。仕様書。直接書き込まない。 |
| `runs/_template/`（このフォルダ）| **run 開始時にコピーする用紙**。実際の記録はコピー先に書く。 |

---

## チェックリスト（run 開始前）

> **パターン適用の判断**: `framework/pattern-application-checklist.md` を参照する（optional / Planner や run designer に有用）。

- [ ] 命名規則に従っているか（`YYYY-MM-DD_case-key_topic`）
- [ ] `cases/` 配下のケースの `context.md` / `goals.md` を確認したか
- [ ] `execution-assignment.md` を作成したか（実行手段の決定）
- [ ] `model-assignment.md` を作成したか
- [ ] `goal.md` の成功基準が具体的・検証可能か
- [ ] `apsf dry-run <run-name>` で role → executor マッピングを確認したか

## チェックリスト（run 完了時）

- [ ] `result.md` を書いたか
- [ ] `result.md` の **Generalization** と **Reusable Prompt** を書いたか
- [ ] `runs/README.md` のテーブルに追記したか
- [ ] `transcript.md` を生成したか（初回 run・重要 run では強く推奨）
