# Workspace: Builder

## この workspace の役割

Builder role の実行拠点。
`plan.md`（+ JuniorBuilder の下書き）をもとに、最終的な成果物を作る。

**この workspace が最も高付加価値な工程。高性能ツールを集中投入する。**

---

## 担当 role

**Builder** — 実装 / 具体化 / 統合

推奨 execution type: **cli**（高品質ツールを使う）
推奨ツール: **Claude Code**（コーディング・文書生成に最適）

---

## 想定ツール例

| ツール | 用途 | 推奨度 |
|---|---|---|
| Claude Code | コード・文書・コンテンツの生成 | ★★★ |
| Cursor | コード編集・補完 | ★★★ |
| ChatGPT（ブラウザ） | 文書・コンテンツ生成 | ★★ |

---

## ここに置くべきもの / 置かないべきもの

### 置いてよいもの
- 作業中の成果物（コード・文書・設計）
- `plan.md` と `handoff.md` の参照コピー（一時利用）
- Claude Code / ツールの設定ファイル（`.claude/` 等）

### 置かないべきもの
- **最終的な build.md はここに保存しない**（`runs/<run-name>/build.md` に置く）
- 他の role の記録

---

## run ディレクトリとの関係

```
workspaces/builder/  ← Claude Code / CLI で作業する
       ↓
runs/<run-name>/build.md   ← 記録をここに書く
runs/<run-name>/[成果物]   ← 成果物の参照先をここに記録する
```

---

## 注意

- **この workspace に最も高性能なツールを集中投入すること**（コスト・品質の最大化）
- JuniorBuilder の下書きは「参考」として使い、品質向上は Builder が行う
- 完璧主義は禁物。Critic に渡せる状態を優先する
- 成果物の決定版は `runs/<run-name>/` に記録する
