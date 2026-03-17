# Operating Model — マルチモデル運用の思想

## なぜマルチモデル運用か

AI モデルは一枚岩ではない。
「すべての工程を同一モデルに任せる」は、コスト・品質・依存リスクの観点から非最適である。

このフレームワークは以下の考え方に基づく：

> **高性能モデルは Build のような高付加価値工程に集中投入する。
> それ以外の工程には、目的に合った適切なモデルを使う。**

---

## role / provider / model の関係

3 層を明確に分離する。

```
role     = 何をするか（Planner / Builder / Critic など）
provider = どの会社の API を使うか（OpenAI / Anthropic / Gemini）
model    = 具体的なモデル名（gpt-4o / claude-sonnet-4-6 / gemini-2.0-flash など）
```

**NG 設計の例:**
```
ClaudeBuilder  → role と provider が密結合
GeminiPlanner  → 差し替えのたびにコードを変更しなければならない
```

**OK 設計の例:**
```
BuilderAgent uses AnthropicProvider(model="claude-sonnet-4-6")
CriticAgent  uses OpenAIProvider(model="gpt-4o")
```

role を変えずに provider だけ差し替えられることが重要。
`model-assignment.md` でこの割当を run ごとに定義する。

---

## 推奨 role 構成

| role | 役割 | 推奨モデル特性 |
|---|---|---|
| **Planner** | 問題分解・計画立案 | 推論力 / 構造化力。人間が入ると品質が安定しやすい |
| **JuniorBuilder** | 候補出し・下書き・整理 | 速度重視。軽量モデルで十分 |
| **Builder** | 実装・具体化・統合 | **高品質モデル推奨**。最も付加価値が高い工程 |
| **Critic** | レビュー・問題指摘 | Builder と**別系統**のモデルを推奨 |
| **Judge** | 完了判定・最終評価 | v0.1 では**人間が担当**することで品質が安定 |

---

## 推奨モデル帯のガイドライン

これは指針であり、run ごとに `model-assignment.md` で上書きしてよい。

| role | 推奨帯 | 理由 |
|---|---|---|
| Planner | GPT-4o / Claude Opus / 人間 | 計画の質が後工程全体に影響する |
| JuniorBuilder | Gemini Flash / GPT-4o mini | 候補出しは速度重視でよい |
| Builder | **Claude Sonnet / Claude Opus** | 高品質アウトプットが必要な工程 |
| Critic | GPT-4o / 人間 | Builder と別視点・別モデルで独立性を確保 |
| Judge | 人間（v0.1） | 判断の最終責任は人間が持つ |

### 高コストモデルの使いどころ

```
┌─────────────────────────────────────────────────┐
│  Plan  │ JuniorBuild │    Build    │   Review    │
│  中コスト│   低コスト   │  高コスト   │   中コスト   │
│        │             │ ← ここに集中│             │
└─────────────────────────────────────────────────┘
```

全工程に最高性能モデルを使う必要はない。
**Build に投資し、JuniorBuilder で省コスト化する**のが基本戦略。

---

## Critic を別モデルにする意義

同一モデルが Builder と Critic を兼ねると、自分のアウトプットを評価することになり、
バイアスがかかりやすい。

**推奨:**
- Builder = Anthropic 系
- Critic = OpenAI 系（または人間）

異なる学習データ・アーキテクチャのモデルを組み合わせることで、
見落としを補完し合うレビューになる。

---

## 人間が介入すべき箇所

| タイミング | 理由 |
|---|---|
| **Goal 定義**（必須） | 「何を解くか」は人間の判断が不可欠 |
| **Planner**（推奨） | 計画の方向性は人間が承認することで品質が安定 |
| **Judge**（v0.1 必須） | 成功判定・完了判断の最終責任は人間が持つ |
| **Improve 判断**（必須） | 続けるか終わるかの意思決定 |

AI が全自動で回してよいのは **Plan → Build → Review の実行部分**であり、
入口（Goal）と出口（Judge / Improve）は人間が担当することが品質の安定につながる。

---

## handoff の重要性

モデルを分けるほど、role 間の受け渡し（handoff）の品質が重要になる。

**失敗パターン:**
- Builder が何を作ったか Critic に伝わっていない
- Planner の意図が Build に引き継がれていない
- Critic の指摘が Improve に反映されていない

**このフレームワークの解決策:**
`handoff.md` を role 間の受け渡し文書として使う。
Markdown が人間と複数 AI の**共通言語**になる。

```
Planner → handoff.md → Builder
Builder → handoff.md → Critic
Critic  → handoff.md → Judge/Improve
```

handoff.md には「何が決まっているか」「何が未決か」「次の role は何をすべきか」を明記する。

---

## run ごとの model assignment

1 run の開始時に `model-assignment.md` を作成する。

これにより:
- どの run でどのモデルを使ったかが記録される
- run 間の比較・分析が可能になる
- コスト意識が自然に生まれる

テンプレート: [`framework/templates/model-assignment.md`](templates/model-assignment.md)
