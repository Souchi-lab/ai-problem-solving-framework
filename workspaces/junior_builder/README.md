# Workspace: JuniorBuilder

## この workspace の役割

JuniorBuilder role の実行拠点。
`plan.md` をもとに複数の候補案・下書きを生成する作業を行う場所。

---

## 担当 role

**JuniorBuilder** — 候補出し / 下書き / 整理

推奨 execution type: **cli**（速度重視・軽量モデルで十分）

---

## 想定ツール例

| ツール | 用途 |
|---|---|
| Gemini CLI | 候補案の高速生成 |
| ChatGPT（ブラウザ） | バリエーション生成 |
| Claude Code | 下書き・整理 |

---

## ここに置くべきもの / 置かないべきもの

### 置いてよいもの
- 候補案・バリエーションの下書き（一時ファイル）
- CLI へのプロンプト試行メモ
- `build_draft.md`（Builder に渡す下書き）

### 置かないべきもの
- **最終的な build.md はここに保存しない**
- 完成品のつもりのファイルを蓄積しない

---

## run ディレクトリとの関係

```
workspaces/junior_builder/  ← 候補案を生成する（一時的な作業空間）
       ↓
runs/<run-name>/build_draft.md  ← Builder への参照ファイルとして渡す
```

JuniorBuilder の出力は**完成品ではなく素材**。
Builder が判断・統合・品質向上を行う。

---

## 注意

- 完璧を目指さない。Builder が選んで仕上げる前提でよい。
- ここが「高品質な出力」を出す場所ではない（それは Builder の workspace）。
- 速度とバリエーションを重視する。
