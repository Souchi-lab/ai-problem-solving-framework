# Plan

---

## Follow-up Context

- Parent series: SNS video generation / tutorial video
- Previous result: video-intro-assembly — assembly_intro を全モードに適用済み
- New trigger: how-to-play.html の tutorial 動画が 404。SNSOverlay が tutorial フェーズ未対応
- Scope limit: SNSOverlay.tsx の tutorial overlay 実装 + generate_sns_video.js tutorial モード追加 + ja/en 動画生成
- Non-goals: useAutoPlayer.ts の tutorial ロジック変更 / tutorial 以外のモード改修

---

## Run Metadata

- Follow-up: tutorial-video
- Goal: tutorial 系フェーズの overlay 責務を先に固定し、実装方針をぶれなく定義する
- Output focus: overlay 設計 → SNSOverlay.tsx 実装 → ja/en 動画生成 → docs/ 配置
- Non-goal reminder: 動画を生成することが主題ではない。overlay 設計の固定が先

---

## Goal Readiness Check

- tutorial 系フェーズ 7本の棚卸しが完了している
- 各フェーズに `lang` パラメータが渡されており ja/en 分岐の基盤がある
- 生成先（docs/sns_videos/tutorial_ja.mp4 / tutorial_en.mp4）が確定している
- 主実装対象が SNSOverlay.tsx であることが goal で明確になっている

Decision: Proceed

---

## Execution Intent

### 表層: tutorial overlay の実装と動画生成

SNSOverlay.tsx に tutorial 系フェーズの描画を追加し、
generate_sns_video.js で tutorial モードを有効化して ja/en 動画を生成する。

### 裏層: 形式検証

「設計判断を先行させる」アプローチが実装のぶれを防ぐかを記録する。

---

## Problem Structure

### 1. tutorial 系フェーズ棚卸し（useAutoPlayer.ts から）

| フェーズ | detail | hold 時間 | 現在の SNSOverlay |
|---|---|---|---|
| `tutorial_intro` | { lang } | 2200ms | 未対応 |
| `tutorial_problem` | { total, lang } | 1400ms | 未対応 |
| `tutorial_select` | { pieceIdx, total, lang } | 900ms | 未対応 |
| `tutorial_rotate` | { lang } | ~3340ms（7回転） | 未対応 |
| `tutorial_place` | { lang } | 550ms | 未対応 |
| `tutorial_fit` | { pieceIdx, total, lang } | 800ms | 未対応 |
| `tutorial_victory` | { total, lang } | 3500ms | 未対応 |

合計: 3ピース想定で約25秒。目標30秒と整合。

### 2. 各フェーズの overlay 設計方針

overlay の役割を **「手順ラベル + 注目点の誘導」** に絞る。
ゲーム画面を隠さない。情報は最小限。

| フェーズ | 表示内容 | ja | en |
|---|---|---|---|
| `tutorial_intro` | タイトル + サブ | 「遊び方」/「30秒でわかる！」 | "How to Play" / "Learn in 30s!" |
| `tutorial_problem` | 問題提示 + ピース数 | 「このパズルを解こう」/「ピース × {total}」 | "Solve this!" / "{total} pieces" |
| `tutorial_select` | ステップラベル + 指アイコン | 「① ピースを選ぶ 👇」 | "① Select a piece 👇" |
| `tutorial_rotate` | ステップラベル | 「② 向きを変える 🔄」 | "② Rotate it 🔄" |
| `tutorial_place` | ステップラベル | 「③ 位置を決める ✅」 | "③ Set the position ✅" |
| `tutorial_fit` | 正解フラッシュ | 「Fit! ✓」 | "Fit! ✓" |
| `tutorial_victory` | クリア + CTA | 「Solved! 🎉」/ URL | "Solved! 🎉" / URL |

### 3. SNSOverlay.tsx の変更範囲

- `Phase` 型に 7フェーズを追加
- `OverlayState` に `tutorialLang` と `tutorialTotal` を追加
- `showMain` の除外リストに tutorial 系フェーズを追加
- 各フェーズの render ブロックを追加（既存フェーズと完全に独立）
- CSS: tutorial 専用クラス（`.sns-tutorial-*`）を App.css に追加

### 4. generate_sns_video.js の変更範囲（従属）

- validation に `tutorial` を追加
- suffix: `_tutorial_ja` / `_tutorial_en`
- URL: `&video_mode=tutorial&lang=ja|en`
- `--lang ja|en` フラグを追加（tutorial モード時のみ使用）

### 5. ja/en 生成と配置

```
node generate_sns_video.js <puzzle_id> --mode tutorial --lang ja
node generate_sns_video.js <puzzle_id> --mode tutorial --lang en
```

生成物を `docs/sns_videos/tutorial_ja.mp4` / `tutorial_en.mp4` として配置。

---

## Selected Approach

Approach:

SNSOverlay.tsx に tutorial 系フェーズの render ブロックを局所追加する。
既存フェーズ（intro / float / snap / victory）は変更しない。
generate_sns_video.js は tutorial モードと `--lang` フラグを追加する従属変更。

Reasoning:

- tutorial 系フェーズは既存フェーズと完全に独立した描画なので干渉しない
- `lang` パラメータは useAutoPlayer.ts が既に URL から読んで dispatch している
- generate_sns_video.js の変更は validation 追加 + フラグ追加のみで小さい

---

## Scope Policy

この follow-up に含めるもの:

- `SNSOverlay.tsx` への tutorial 系 overlay 実装（7フェーズ）
- `generate_sns_video.js` への tutorial モード + `--lang` フラグ追加
- tutorial_ja.mp4 / tutorial_en.mp4 の生成
- `docs/sns_videos/` への配置

この follow-up に含めないもの:

- `useAutoPlayer.ts` の tutorial ロジック変更
- tutorial 以外のモードへの影響
- how-to-play.html の動画プレーヤー UI 改修
- 音声・BGM の追加

---

## Deliverables

- `SNSOverlay.tsx` 差分（tutorial 系 overlay 7フェーズ）
- `generate_sns_video.js` 差分（tutorial モード + --lang フラグ）
- `tutorial_ja.mp4` / `tutorial_en.mp4`（docs/sns_videos/ 配置済み）
- result での評価（overlay 設計の妥当性 + 動画品質）

---

## Review Checklist

- overlay 設計が「手順ラベル + 注目点の誘導」に絞られている
- 既存フェーズ（intro / float / snap / victory）が変更されていない
- ja / en の文言差分が SNSOverlay 側で完結している
- `generate_sns_video.js` の変更が tutorial に閉じている

---

## Planned Output Shape

result は次の構成でまとめる。

1. 実装差分サマリー（変更ファイル・変更量）
2. overlay 設計の評価（各フェーズで意図が伝わるか）
3. 動画品質確認（ja / en 各30秒程度になっているか）
4. how-to-play.html での再生確認
5. 形式評価（overlay 設計先行アプローチの有効性）

---

## Assumptions & Open Questions

Assumptions:

- `lang` パラメータは URL の `?lang=ja|en` から useAutoPlayer が取得して dispatch している
- `docs/sns_videos/` への自動コピーは既存処理で対応可能
- tutorial 用パズルは既存パズルを流用（新規作成不要）

Open questions:

- `tutorial_fit` は全ピース分発火するため、overlay が点滅しないよう表示制御が必要
- `tutorial_victory` の CTA に URL を含めるか（SNS 動画ではないので省略も選択肢）

---

## What This Follow-up Decides

- tutorial 系フェーズの overlay 責務と表示内容
- SNSOverlay.tsx の tutorial 実装方針
- ja/en 文言の最終定義

---

## What This Follow-up Does Not Decide

- tutorial 動画の公開タイミング・マーケ戦略
- how-to-play.html の動画プレーヤー UI
- tutorial 以外のモードへの横展開
