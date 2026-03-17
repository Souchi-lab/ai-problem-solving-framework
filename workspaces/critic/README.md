# Workspace: Critic

## この workspace の役割

Critic role の実行拠点。
`build.md` と成果物を評価し、`review.md` を作成する。

**Critic は Builder と別系統のツールを使うことを推奨。独立した視点が品質を高める。**

---

## 担当 role

**Critic** — レビュー / 問題指摘 / 改善提案

推奨 execution type: **human** または **cli**（Builder と別系統）
推奨ツール: Builder が Anthropic 系なら → OpenAI / ChatGPT 系を使う

---

## 想定ツール例

| ツール | 用途 | 推奨度 |
|---|---|---|
| ChatGPT（ブラウザ）| 批判的レビュー | ★★★（Builder と別系統） |
| 人間によるレビュー | 判断が必要な評価 | ★★★ |
| Claude Code | 補助的なレビュー | ★★（Builder と同系統は注意） |

---

## ここに置くべきもの / 置かないべきもの

### 置いてよいもの
- レビュー作業のメモ
- Critic プロンプトの試行記録
- `review.md` の下書き

### 置かないべきもの
- **最終的な review.md はここに保存しない**
- 成果物の修正（それは次の Build の仕事）

---

## run ディレクトリとの関係

```
workspaces/critic/  ← レビュー作業を行う
       ↓
runs/<run-name>/review.md  ← 結果をここに書く
```

---

## 注意

- **Builder と同じツール / モデルで Critic をしない**（自己評価バイアスが生じる）
- 褒めることよりも「壊すこと」に集中する
- Critical / Major / Minor に分類して書く
- スコープ外の指摘は「参考情報」として分離する
