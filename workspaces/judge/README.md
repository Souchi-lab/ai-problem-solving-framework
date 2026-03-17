# Workspace: Judge

## この workspace の役割

Judge role の実行拠点。
`review.md` を読み、Goal の成功基準に照らして完了判定を行う。

**v0.1 では Judge は必ず人間が担当する。**

---

## 担当 role

**Judge** — 完了判定 / 最終評価

推奨 execution type: **human**（必須、v0.1 では AI 単独での判断は推奨しない）

---

## 想定ツール例

| ツール | 用途 |
|---|---|
| テキストエディタ | improve.md / result.md の記述 |
| AI（補助） | 評価サマリの生成補助（判断は人間が行う） |

---

## ここに置くべきもの / 置かないべきもの

### 置いてよいもの
- 評価作業のメモ
- result.md の下書き

### 置かないべきもの
- 最終的な result.md はここに保存しない

---

## run ディレクトリとの関係

```
workspaces/judge/  ← 評価・判断作業を行う
       ↓
runs/<run-name>/improve.md  ← 続けるか終わるかの判断
runs/<run-name>/result.md   ← ループ完了時の最終記録
```

---

## Judge の判断フロー

```
review.md を読む
  ↓
Goal の Success Criteria と照合する
  ↓
  ├─ 満たしている → result.md を書いてループ完了
  └─ まだ足りない → improve.md を書いて次 iteration へ
                      ↓
                    改善余地 / リソースを確認
                      ├─ 続ける → Plan or Build から再開
                      └─ 中断 → result.md に理由を記録
```

---

## 注意

- **AI に最終判断を委ねない**（v0.1）
- 成功基準は `goal.md` に書いたものと照合する
- `result.md` の **Generalization** と **Reusable Prompt** は必ず書く
- フレームワーク自体への改善提案も `result.md` に残す
