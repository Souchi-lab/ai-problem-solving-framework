# Result

---

## Status

Completed

---

## 1. 実装差分サマリー

### 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `src/apsf/legacy/cli/main.py` | `status` コマンド追加（約45行） + docstring に2行追記 |

### 変更量

- コマンド本体: 約45行
- docstring 更新: 2行（`list-followups` と `status` の説明追加）

既存コマンドへの変更ゼロ。settings.py・外部ファイルへの変更なし。

---

## 2. 動作確認結果

| ケース | 結果 |
|---|---|
| `apsf status` — in-progress が先頭に来る | ✓ |
| `apsf status` — `Next: write X` が出る | ✓ |
| `apsf status` — ヘッダで全体件数が見える | ✓ |
| `apsf status` — complete は下部に簡潔表示 | ✓ |
| `apsf list-followups` との役割が重複しすぎていない | ✓ |

実出力（確認時点）:

```
Status: 13 follow-ups — 1 in-progress, 12 complete
========================================================================
In-Progress:
  apsf-status-cmd
    Next: write review.md  (Missing: review.md, result.md)

Complete:
  empty-state-copy  [complete (review-skipped)]
  ...
```

---

## 3. 採用判断

**採用** — このまま常用に入る。

---

## 4. goal.md の Success Criteria 照合

| 条件 | 結果 |
|---|---|
| `status` の主語が「現在状態の要約」に固定されている | ✓ |
| `list-followups` と役割が重複しすぎていない | ✓（存在確認 vs 現在状態・次の注意点） |
| `complete / in-progress / review-skipped` の見え方が得られる | ✓ |
| `next attention` を短く出せる | ✓（`Next: write X` 形式） |
| GUI 的 status view の前段として使えるかを result で評価できる | ✓（下記） |

---

## 5. GUI 北極星への評価

### 今回が前段として機能した理由

- **フィルタ**: in-progress だけを先頭に引き上げることで、「どこを見るか」の判断が不要になった。
- **next attention**: `Next: write X` により、開くファイルを考える必要がなくなった。
- **全体感**: ヘッダの `N in-progress / N complete` で状態の概要が 1 行で把握できた。

これは GUI の `run type / required checks / next trigger` に向けた「判断導線の先取り」として機能している。

### まだ CLI の限界である部分

- follow-up を開く操作はまだ手動（`cd` + `code`）
- 複数 in-progress があるときの優先順を自動判断する手段がない
- phase 推定は `result.md` の有無だけであり、plan.md まで書いたかは区別しない

これらは今回の Non-Goals として意図的に除外した範囲であり、問題ではない。

---

## 6. 役割分離の確定

| コマンド | 役割 |
|---|---|
| `apsf list-followups` | 何が存在するかを確認する（存在確認） |
| `apsf status` | 今どれが未完了で、次にどこを見るべきかを確認する（現在状態・next attention） |

この分離は今後も維持する。

---

## 7. Closing

### Stable Baseline

- `apsf status` が常用コマンドとして利用可能
- `list-followups` との役割分離が確定した
- CLI 拡張タスクには 4点セット（review skip）が適合する（init-followup-cmd に続いて2例目）

### Open Conditional

- in-progress が複数になったとき、優先順の表示が欲しくなったら `--sort` オプションを検討する
- `plan.md` の有無で「着手済み」と「未着手 in-progress」を分けたい場合はフェーズ推定を細かくする
- 全 run 横断 status（taxonomy 対応）は別 follow-up で扱う

### Next Trigger

- `apsf status` を日常的に使い始めて「見えにくい」と感じた点が出たら改訂する
- GUI 的 status view の次の1歩として、follow-up をそのまま開く導線（`apsf open <slug>` 相当）が候補になる
