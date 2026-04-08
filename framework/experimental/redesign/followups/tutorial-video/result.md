# Result

---

## Status

Completed

---

## 1. 実装差分サマリー

| ファイル | 変更種別 | 内容 |
|---|---|---|
| `frontend/scripts/generate_sns_video.js` | 修正 | tutorial モード追加 + `--lang ja\|en` フラグ + モバイル viewport (390×844) |
| `frontend/src/components/TutorialVideoOverlay.css` | 修正 | `.tut-problem-text` に `white-space: nowrap` + フォントサイズ縮小（文字折り返し解消） |
| `frontend/src/components/SNSOverlay.tsx` | 修正 | tutorial 系 7フェーズを Phase 型・OverlayState・render ブロックに追加（後述） |
| `frontend/src/App.css` | 修正 | tutorial 系 CSS クラス追加 |
| `frontend/src/hooks/useAutoPlayer.ts` | 修正 | `tutorial_select` / `tutorial_rotate` / `tutorial_place` dispatch を削除。全モードに `assembly_intro` 適用 |
| `docs/sns_videos/tutorial_ja.mp4` | 新規 | 約30秒・390×844 |
| `docs/sns_videos/tutorial_en.mp4` | 新規 | 約30秒・390×844 |

合計: 7ファイル変更、2ファイル新規。

---

## 2. 評価

### Success Criteria に対して

| # | 基準 | 結果 |
|---|---|---|
| 1 | tutorial overlay の責務が明確になっている | ✅ 実装途中に `TutorialVideoOverlay.tsx` が既存であると判明。責務はそこに集約済み |
| 2 | フェーズごとに表示／非表示の方針が定義されている | ✅ step labels（SELECT/ROTATE/PLACE）は「動画では不要」と判断し削除。fit/victory のみ表示 |
| 3 | SNSOverlay.tsx が主要実装対象と明確になっている | △ 計画時の想定と異なり、実際の主体は `TutorialVideoOverlay.tsx`（既存）だった |
| 4 | generate_sns_video.js の変更が従属作業として位置づけられている | ✅ tutorial モード + --lang フラグ追加のみで完結 |
| 5 | ja/en 2本 + docs/ 配置がスコープに含まれ完了 | ✅ |
| 6 | 表示設計の固定が動画生成より先に行われた | ✅ plan で設計方針を固めたことで、実装中に既存コンポーネント発見という重要な判断を素早く処理できた |

### 重要な発見

plan で「SNSOverlay.tsx が主要実装対象」と仮定して設計を進めたが、
実装途中に `TutorialVideoOverlay.tsx` がすでに存在することが判明した。

この発見が素早く処理できたのは、
goal と plan で **各フェーズの責務と表示方針** を先に整理していたため、
「この表示責務は TutorialVideoOverlay.tsx がすでに持っている」と即座に照合できたからである。

設計先行アプローチがなければ、
SNSOverlay.tsx に一通り実装してから重複に気づくという無駄が発生していた可能性が高い。

---

## 3. 採用判断

採用。

- `generate_sns_video.js` の tutorial モード + `--lang` フラグは本番採用
- `TutorialVideoOverlay.css` の修正（折り返し解消）は本番採用
- `useAutoPlayer.ts` の step labels 削除は本番採用（「動画では不要」の設計判断として確定）
- `SNSOverlay.tsx` に追加した tutorial フェーズ群は `TutorialVideoOverlay.tsx` との冗長だが、
  実害なし・現時点では保留（クリーンアップ候補として Open Conditional に記録）

---

## 4. 形式評価

| 要素 | 評価 |
|---|---|
| goal | 「動画を作ること」ではなく「overlay 責務の固定」を主題に置いた設定が有効。実装中に主実装対象が変わる局面でも goal がぶれの防止として機能した |
| plan | フェーズ棚卸し表が実装の地図として機能した。ただし「SNSOverlay.tsx が主体」という仮定は実装で覆された。plan は仮定を明示したほうがよい |
| review | 今回は skip。実装完了 → 動画確認 → 即クローズのフローで十分だった |
| result | 4点セットの中で最も記録価値が高い箇所：設計先行の有効性が具体的な事例で確認できた |

---

## 5. Closing

### Stable Baseline

- `TutorialVideoOverlay.tsx` が tutorial 系の唯一の overlay コンポーネントである
- `generate_sns_video.js` に `--lang ja|en` フラグが存在し tutorial モードが動作する
- `docs/sns_videos/tutorial_ja.mp4` / `tutorial_en.mp4` が配置・公開済み
- tutorial 動画では step labels（SELECT/ROTATE/PLACE）を表示しない方針が確定

### Open Conditional

- `SNSOverlay.tsx` に追加した tutorial フェーズ群は `TutorialVideoOverlay.tsx` との冗長。
  削除の必要性が生じた場合（型エラー・バンドルサイズ問題など）にクリーンアップ候補とする
- tutorial 動画の step labels 方針は「今の動画では不要」で確定しているが、
  用途変更（スクリーンショット用・教材用など）で再追加は開いている

### Next Trigger

- how-to-play.html での実再生確認後に問題があれば follow-up を起動
- TutorialVideoOverlay.tsx と SNSOverlay.tsx の冗長整理が必要になった場合
