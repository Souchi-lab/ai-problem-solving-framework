# Workspace: Planner

## この workspace の役割

Planner role の実行拠点。
`goal.md` を読み込み、`plan.md` を作成する作業を行う場所。

---

## 担当 role

**Planner** — 問題を分解し、解決アプローチを設計する

推奨 execution type: **human**（人間が入ることで品質が安定しやすい）

---

## 想定ツール例

| ツール | 用途 |
|---|---|
| ChatGPT / Claude.ai（ブラウザ） | plan を生成する |
| テキストエディタ | plan.md を直接書く |
| Claude Code / Cursor | 整理・構造化の補助 |

---

## ここに置くべきもの / 置かないべきもの

### 置いてよいもの
- plan 作成のための一時メモ・下書き
- プロンプト試行のメモ
- 参照用の goal.md のコピー（一時利用）

### 置かないべきもの
- **最終的な plan.md はここに保存しない**（`runs/<run-name>/plan.md` に置く）
- 他の role の作業ファイル
- 長期的に保管すべきデータ

---

## run ディレクトリとの関係

```
workspaces/planner/    ← ここで作業する（一時的な作業空間）
       ↓
runs/<run-name>/plan.md  ← 成果物をここにコピー / 移動する
```

作業が完了したら成果物を `runs/<run-name>/` に移し、`handoff.md` を更新する。

---

## 注意

- workspaces は「作業場」。成果物の最終保管場所ではない。
- ここに実データを蓄積しすぎない。
- run ごとに作業ファイルを整理する習慣を持つ。
