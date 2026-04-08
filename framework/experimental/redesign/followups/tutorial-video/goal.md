# Goal

---

## Follow-up Context

- Parent series: SNS video generation / tutorial video
- Previous result: tutorial 再生ロジック自体は既存の `useAutoPlayer.ts` にあり、動画生成基盤も存在する
- New trigger: tutorial 動画を生成したいが、`SNSOverlay.tsx` は `tutorial_intro` / `tutorial_problem` などの tutorial 系フェーズに対して実質未対応で、何を見せるかの設計が未固定
- Scope limit: tutorial 動画生成に必要な overlay 設計と、それを前提にした実装方針の固定まで
- Non-goals: SNS 動画基盤全体の再設計 / tutorial 以外のモード改修 / 完全な動画マーケ戦略の設計

---

## Goal Statement

tutorial 動画生成に向けて、
tutorial 系フェーズで **何を overlay として見せるべきか** を先に固定し、
その設計に基づいて実装方針をぶれなく定義する small-to-medium run を定義する。

今回の主題は、
単に動画を 2 本生成することではない。

主題は、
`SNSOverlay.tsx` における tutorial 系表示の責務を明確にし、
`generate_sns_video.js` の tutorial モード追加と
ja / en 動画生成までを支える **設計判断を先に揃えること** である。

---

## Background

現状、作業サイズとしては video-intro-assembly と同程度で、
small-to-medium に収まる見込みである。

ただし中身を見ると、
主たる判断点は単なる生成実行ではなく、
`SNSOverlay.tsx` に tutorial 系フェーズをどう描画させるかにある。

現時点で想定される作業は次のとおり。

- `generate_sns_video.js` への tutorial モード追加
- `SNSOverlay.tsx` への tutorial 系 overlay 実装
- 動画生成 × 2（ja / en）
- `docs/sns_videos/` へのコピー

このうち、
`useAutoPlayer.ts` 側には tutorial ロジックがすでに存在する一方で、
`SNSOverlay.tsx` は tutorial 系フェーズをほぼ描画しない状態である。

そのため、
先に goal で
**tutorial では何を見せるべきか**
を固定しないと、
実装の途中で overlay 設計がぶれやすい。

---

## Success Criteria

1. tutorial 動画で扱う overlay の責務が明確になっている
2. tutorial 系フェーズごとに、何を表示し何を表示しないかの方針が定義されている
3. `SNSOverlay.tsx` が今回の主要実装対象であることが明確になっている
4. `generate_sns_video.js` の tutorial モード追加は、overlay 設計に従う従属作業として位置づけられている
5. 出力対象が ja / en の 2 本であることと、`docs/sns_videos/` への配置までスコープに含まれている
6. tutorial 動画生成そのものより前に、表示設計の固定が優先されることが明記されている

---

## Expected Outputs

- tutorial 動画用 overlay 設計の主語固定
- tutorial 系フェーズごとの表示方針
- `SNSOverlay.tsx` 実装の主要判断点
- `generate_sns_video.js` tutorial モード追加の位置づけ
- ja / en 動画生成と配置まで含めた narrow な実行スコープ

---

## Non-Goals

- SNS 動画システム全体の再設計
- tutorial 以外の video mode の見直し
- `useAutoPlayer.ts` の基礎ロジック再設計
- 動画コピー全体のブランド戦略設計
- 音声 / BGM / 全演出の包括改善
- UI コンポーネント全般の整理

---

## Constraints

- 主語は tutorial 動画全体ではなく tutorial overlay 設計に置く
- 実装判断は `SNSOverlay.tsx` を中心に整理する
- 既存の `useAutoPlayer.ts` tutorial ロジックは前提資産として扱い、今回の主対象にしない
- 対象モードは tutorial に限定する
- 出力は ja / en の 2 本に限定する
- run は small-to-medium に留め、動画基盤全体へ広げない

---

## Notes For Planner

Planner は次を先に明確化すること。

- tutorial 系フェーズとして何が存在し、各フェーズで何を見せるべきか
- overlay の役割を「進行説明」「注目点の誘導」「手順理解補助」のどこまで持たせるか
- どの情報を overlay に出し、どの情報は出さないか
- `SNSOverlay.tsx` に閉じて解決できる部分と、他ファイルに触れる必要がある部分の境界
- `generate_sns_video.js` の tutorial モード追加をどの粒度で行うか
- ja / en 2 本生成時に文言差分をどう扱うか