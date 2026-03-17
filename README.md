# AI Problem Solving Framework (APSF)

> AIを使った問題解決プロセスを一般化・再利用可能にするフレームワーク

---

## このプロジェクトの目的

「AIを使ってコードを書く」ためのツールではない。

**AIを役割ごとに組み合わせて、問題解決の進め方そのものを再利用可能な型として保存すること**が目的である。

ドメインが変わっても、チームが変わっても、使うAIモデルが変わっても、
同じ問題解決ループを回せる構造を目指す。

---

## マルチモデル運用前提

このフレームワークは単一AIへの依存を前提としない。

```
Planner    → 人間 + OpenAI (GPT-4o)
JuniorBuilder → Gemini (Flash)
Builder    → Anthropic (Claude Sonnet)
Critic     → OpenAI (GPT-4o) — Builder と別系統で運用
Judge      → 人間
```

**role と provider を分離する**ことがこのフレームワークの設計核心。
`ClaudeBuilder` のような密結合は作らない。
どの role に何を使うかは run ごとに `model-assignment.md` で定義する。

詳細: [`framework/operating-model.md`](framework/operating-model.md)

---

## なぜ SoChi BLOCKS が最初の実験環境なのか

SoChi BLOCKS はブロック系パズルゲームを中心とした Web プロダクトで、
以下の理由からフレームワークの最初の検証場として最適である。

- **マルチドメイン**: Engineering / Design / Algorithm / Content / Marketing を含む
- **ミニスタートアップ構造**: 1〜少人数で全レイヤーを担当する現実がある
- **課題が具体的**: 直帰率・UX・パズル品質など実際の問題が積み上がっている
- **フィードバックが速い**: 小規模ゆえに変更の効果を素早く確認できる
- **失敗コストが低い**: 試行錯誤がしやすい

ただし **SoChi BLOCKS 専用設計ではなく、SoChi BLOCKS から始める汎用問題解決 OS** として設計する。

---

## ディレクトリ構成

```
ai-problem-solving-framework/
├── README.md                    # このファイル
├── pyproject.toml               # Python プロジェクト設定
├── .env.example                 # 環境変数サンプル
├── framework/                   # フレームワーク設計資産（ドメイン非依存）
│   ├── overview.md              # 全体像・設計思想
│   ├── operating-model.md       # マルチモデル運用モデル
│   ├── workflow/v0.1.md         # ワークフロー定義
│   ├── agents/                  # 各 role の責務・プロンプト草案
│   └── templates/               # 各ステップのひな型（設計資産・原本）
├── cases/                       # ドメイン固有の知識
│   └── sochi-blocks/            # 最初の検証ケース
├── runs/                        # 実行ログ（1フォルダ = 1 problem solving cycle）
│   ├── README.md
│   └── _template/               # 新しい run を切るときにコピーする
└── src/apsf/                    # Python 実行基盤
    ├── config/                  # 設定・環境変数
    ├── domain/                  # ドメインモデル（Role / Provider / RunContext 等）
    ├── providers/               # API接続層（OpenAI / Anthropic / Gemini）
    ├── agents/                  # 各 role の実装
    ├── prompts/                 # プロンプト読み込み・レンダリング
    ├── storage/                 # Markdown read/write / run 管理
    ├── orchestration/           # pipeline / assignment / handoff
    └── cli/                     # CLI エントリポイント
```

---

## 使い始め方

### 1. 環境構築

```bash
cp .env.example .env
# .env に各 API キーを記入する

pip install -e ".[dev]"
# または: uv pip install -e ".[dev]"
```

### 2. 環境確認

```bash
apsf check-env
```

### 3. フレームワーク構造の確認

```bash
apsf show-structure
```

### 4. 最初の run を作る

```bash
apsf init-run 2026-03-15_sochi-blocks_sns-post-template
```

### 5. goal.md を書いてループを開始する

```
runs/2026-03-15_sochi-blocks_sns-post-template/
  model-assignment.md  ← 最初にどの role に何を使うかを決める
  goal.md              ← 次に何を解くかを書く
  plan.md              ← Planner が作成
  build.md             ← Builder が作成
  review.md            ← Critic が作成
  improve.md           ← 人間が判断
  result.md            ← ループ完了時に記録
  handoff.md           ← role 間の受け渡し記録
```

---

## v0.1 でできること / まだやらないこと

| 機能 | v0.1 | v0.2+ |
|---|---|---|
| Markdown ベースのループ運用 | ✅ | |
| CLI で run 初期化 | ✅ | |
| multi-model assignment 定義 | ✅（手動） | 自動スケジューリング |
| handoff.md による role 間受け渡し | ✅（手動） | 自動生成 |
| Provider stub / 骨格実装 | ✅ | 実 API 完全接続 |
| Pipeline dry-run | ✅ | 実行自動化 |
| Judge による自動評価 | ❌ | ✅ |
| 並列 Build 比較 | ❌ | ✅ |

---

## 今後の発展方針

| バージョン | 主な追加 |
|---|---|
| v0.1 | Markdown基盤・multi-model骨格・CLI・SoChi BLOCKSケース |
| v0.2 | 実API接続・Judge独立化・定量metrics |
| v0.3 | 複数ケース対応・pipeline自動実行 |
| v1.0 | Multi-agent オーケストレーション・完全自動化 |

---

## 関連

- [フレームワーク全体像](framework/overview.md)
- [マルチモデル運用モデル](framework/operating-model.md)
- [SoChi BLOCKSケース](cases/sochi-blocks/README.md)
- [最初の run 推薦](cases/sochi-blocks/goals.md)
