# Plan

---

## Follow-up Context

- Parent series:
  軽量 follow-up 運用の実地検証
- Previous result:
  twitter-tag-improvement で「実装なし小タスク」に4点セットが機能することを確認済み
- New trigger:
  「散らばったピースが集まる冒頭演出」のパイプライン試作可能性が確認された
- Scope limit:
  `generate_puzzle_video.py` 冒頭フェーズの差分実装のみ
- Non-goals:
  動画全体の再設計 / 新規3Dエンジン / 複数バリアントの同時実装

---

## Run Metadata

- Follow-up:
  video-intro-assembly
- Goal:
  散らばったピースが集まって直方体になる冒頭演出を
  既存パイプライン上で試作し、初見理解フックとして機能するか確かめる
- Output focus:
  試作動画1本 + 3観点評価 + 形式評価
- Non-goal reminder:
  これは動画全体の再設計でも、複数バリアントの比較でもない

---

## Goal Readiness Check

- 試作対象が冒頭演出差分に限定されている
- 既存パイプラインで実装可能であることが確認済み
- 評価観点3点が定義されている
- 形式検証（実装を伴うタスクへの4点セット適合度）が二層目的として設定されている

Decision:

- Proceed

---

## Execution Intent

この follow-up の目的は二層ある。

### 表層: 冒頭演出の試作と評価

「散らばった → 集合 → 直方体」演出を1本試作し、
初見フックとして機能するかを3観点で評価する。

### 裏層: 形式検証

「小さめの実装を伴う small follow-up」に対して、
現行4点セットがどう機能するかを実地で記録する。

---

## Problem Structure

### 1. 実際のパイプライン構造（確認済み）

```
generate_sns_video.js (Playwright)
  → viewer.html?autoplay=1&sns=1 を headless 録画
  → useAutoPlayer.ts が game state を操作
      → snsDispatch('intro' | 'float' | 'snap' | 'victory')
  → SNSOverlay.tsx がイベントを受けて 2D overlay を表示
      → バッジ / テキスト / ドット / フラッシュ / Victory 画面
  → Playwright が画面録画 → ffmpeg で MP4 変換
```

### 2. 現状の制約

`SNSOverlay.tsx` は現時点で **2D overlay** のみ。

- バッジ・テキスト・フラッシュ・Victory 画面を切り替える
- 「複数ピースを散らばった 3D 位置に配置してアニメーション」は未実装
- これを実現するには Overlay 側に次が必要：
  - 複数ピースの位置状態管理
  - 初期 scatter 配置の定義
  - フレームごとの時間補間

### 3. 今回追加する実装

**useAutoPlayer.ts** に新しいイベント dispatch を追加：

```typescript
// assembly_intro イベント追加
snsDispatch('assembly_intro', { pieces: removedList });
await sleep(ASSEMBLY_HOLD_MS);
```

**SNSOverlay.tsx** に assembly_intro フェーズの描画を追加：

- `assembly_intro` イベント受信時に全 removed pieces を scatter 位置に配置
- 時間補間で scatter → 最終位置へ収束
- 既存の intro / float / snap フェーズはそのまま維持

### 4. scatter位置の定義

散らばった開始位置は次の方針で決める。

- 各ピースを放射状オフセットで配置（ピース数で方位角を均等分割）
- 初期位置はグリッド外側（X/Y 方向に広がった位置）
- 収束先はそれぞれのピースの正解配置位置

### 5. アニメーションの補間

smoothstep で scatter 位置 → 最終位置へ収束。

- t = 0: scatter 位置
- t = 1: 最終グリッド位置
- 補間: `smoothstep(t)` で自然な加速・減速

---

## Selected Approach

Approach:

`useAutoPlayer.ts` に `assembly_intro` dispatch を追加し、
`SNSOverlay.tsx` に複数ピースの scatter → 収束アニメーションを局所追加する。
`generate_sns_video.js` に `--mode assembly` フラグで切り替えられるようにする。

Reasoning:

- 既存の intro / float / snap / victory フェーズは変更しない
- `assembly_intro` イベントは新規追加のみ（既存イベントと衝突しない）
- フラグなしで起動すると現行動作のまま
- SNSOverlay への追加は局所的で、他フェーズの描画に影響しない

当初の想定との差分:

- 当初想定: `generate_puzzle_video.py`（matplotlib Python）の座標補間流用
- 実際: Playwright + Three.js パイプラインのため、frontend overlay 実装が必要
- 結果: タグ改善より一段重い「small-to-medium 実験」に分類を修正
- first version の目標: 完成度より feasibility 確認に絞る

---

## Scope Policy

この follow-up に含めるもの:

- `useAutoPlayer.ts` への `assembly_intro` dispatch 追加
- `SNSOverlay.tsx` への scatter → 収束アニメーション追加（局所実装）
- `generate_sns_video.js` への `--mode assembly` フラグ追加
- 試作動画1本の生成
- 3観点評価

この follow-up に含めないもの:

- 既存フェーズ（intro / float / snap / victory）の変更
- 複数 scatter パターンの同時試作
- Three.js シーン全体の再設計
- TikTok / Instagram 向けの個別最適化
- 最終採用の決定

---

## Working Definitions

### 「初見で完成形が伝わる」

視聴者が冒頭3秒以内に「これは直方体に組み立てるパズルだ」と
読み取れる状態。

### 「続きを見たくなる」

演出が止まらず先を見たい感覚を生む状態。
具体的には: 組み上がる瞬間に達成感・驚きがある。

### 「ネタバレになりすぎない」

完成形が一瞬見えるが、「どう解くか」の手順は見えない状態。
完成形を見せることが「解答を見せること」にならない。

### 「scatter位置」

グリッド外側の開始座標。各ピースが視覚的に「離れた位置」から
来ていると分かる距離。

---

## Deliverables

この follow-up で作るもの:

- `useAutoPlayer.ts` 差分（assembly_intro dispatch 追加）
- `SNSOverlay.tsx` 差分（scatter → 収束アニメーション追加）
- `generate_sns_video.js` 差分（`--mode assembly` フラグ追加）
- 試作動画1本（`--mode assembly` で生成）
- 3観点評価（result で記録）
- 形式評価（small-to-medium 実装タスクへの4点セット適合度）

---

## Review Checklist

- 実装変更が冒頭フェーズ差分に限定されている
- 既存フェーズ（Phase 1〜3）が変更されていない
- `--intro-mode` フラグなしで現行動作が維持されている
- 3観点評価が result で答えられる状態になっている
- 形式評価の観点が定義されている

---

## Planned Output Shape

result は次の構成でまとめる。

1. 実装差分サマリー（変更箇所・変更量）
2. 試作動画の評価（3観点）
3. トレードオフ判定（「伝わる」vs「ネタバレ」）
4. 採用判断（採用 / 非採用 / 条件付き採用）
5. 形式評価（4点セットの実装タスクへの適合度）

---

## Assumptions & Open Questions

Assumptions:

- SNSOverlay.tsx に CSS/canvas アニメーションで scatter → 収束を追加できる
- scatter 位置は放射状均等配置で視覚的に「散らばった感」が出る
- `--mode assembly` フラグ追加は既存 full_play / teaser の動作に影響しない
- first version は完成度より feasibility 確認を優先する

Open questions:

- SNSOverlay.tsx でどのレイヤー（CSS transform / canvas / SVG）を使うか
- scatter の半径・アニメーション時間はどの程度が自然か（試作で確認）
- assembly_intro 後に既存 intro フェーズを維持するか省略するか
- Three.js シーンのピース位置情報を Overlay 側でどう参照するか

---

## What This Follow-up Decides

- ASSEMBLY_INTRO フェーズの実装方針
- scatter 位置の定義
- 試作1本の評価と採用判断

---

## What This Follow-up Does Not Decide

- 全パズルへの一括適用
- 複数 scatter バリアントの採用
- TikTok / Instagram 向け最適化
- 動画全体の再設計
