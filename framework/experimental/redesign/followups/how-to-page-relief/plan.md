# Plan

---

## Follow-up Context

- Parent series: SoChi BLOCKS 初回体験改善
- Previous result: top-page-cta — 主 CTA「まず1問やってみる」確立、「はじめての方へ」削除済み
- New trigger: 副 CTA 着地先の遊び方ページが「操作手順の列挙」のままで、初心者の不安解消として機能していない
- Scope limit: `docs/how-to-play.html` のみ。viewer / React / トップページは触らない
- Non-goals: 動画制作 / UI 実装 / ゲームルール変更

---

## Run Metadata

- Follow-up: how-to-page-relief
- Goal: 遊び方ページを「初心者の不安解消」中心に再構成し、動画なしで理解できる最小構成にする
- Output focus: `docs/how-to-play.html` の差分
- Non-goal reminder: 操作の完全説明に戻らない。動画は補足として残す

---

## Goal Readiness Check

- `docs/how-to-play.html` を読んで現状の構造と問題点を把握済み
- 変更箇所が特定できている
- 変更後の文言が準備できている

Decision: Proceed

---

## Problem Structure

### 現状の構造と問題点

```
[現状]
1. ページタイトル「遊び方」
2. サブタイトル: 「動画でルールと操作を確認しよう。30秒で全部わかる！」← 動画が主
3. 動画ブロック
   └─ ※動画がない場合は下の手順を  ← テキストが補足扱い
4. セクション「操作手順」           ← 網羅感・説明書感
5. Step ① ピースを選ぶ
6. Step ② 向きを変える  [← →]     ← 回転
7. Step ③ 配置して確定  [← →]     ← 位置選択（同じキー表記）
8. CTA「パズルを選んで挑戦！」
```

| 問題 | SC 違反 | 深刻度 |
|---|---|---|
| ゴール条件がどこにもない | SC-3 | 高 |
| セクション名が「操作手順」→ 網羅感 | SC-1,2 | 高 |
| Step 2/3 が同じ `← →` 表記 | SC-4 | 高 |
| 動画が主・テキストが補足 | SC-5 | 中 |
| 不安解消メッセージがゼロ | SC-2 | 中 |

---

## Selected Approach

### 新しいページ構造

```
[改善後]
1. ページタイトル（変更なし）
2. ゴール条件バナー (NEW)
3. 不安解消メッセージ + セクション見出し (REVISED)
4. Step ① ピースを選ぶ（軽微修正）
5. Step ② 向きを回す 🔄（アイコン・文言・キー注記を分離）
6. Step ③ 置く場所を決める 📍（回転と明確に分離）
7. 動画ブロック → 補足として steps の後へ移動 (MOVED)
8. CTA「パズルを選んで挑戦！」（変更なし）
```

---

### 変更 1: ゴール条件バナー追加

steps の前に挿入。CSS `.goal-banner` を新規追加。

```
ja: 「ゴール ： すべての空きスペースにピースをはめたらクリア」
en: "Goal: Fit all pieces into the empty spaces to win"
```

### 変更 2: サブタイトルを不安解消に書き換え

```
現状: 「動画でルールと操作を確認しよう。30秒で全部わかる！」
改善: 「3ステップで始められます。全部覚えなくて大丈夫。」
  en: "Just 3 steps to get started. No need to memorize everything."
```

### 変更 3: セクション見出し変更

```
「操作手順」/ "Steps"  →  「始め方」/ "How to Start"
```

### 変更 4: Step 2 / Step 3 の明確分離

**Step 2（回転）:**
- 見出し: 「向きを回す」/ "Rotate"
- アイコン: 🔄
- ja 本文: `[←][→] ボタンで回転させて、空きスペースに合う向きを探します。`
- キー注記: 「← → は回転」と明示

**Step 3（配置）:**
- 見出し: 「置く場所を決める」/ "Place It"
- アイコン: 📍
- ja 本文: `[←][→] で場所を移動して、[Set] をタップして確定。全ピースを埋めたらクリア！`
- キー注記: 「← → はカーソル移動」と明示し、回転との違いを伝える

### 変更 5: 動画ブロックを steps の後へ移動

steps 完了後に補足セクションとして配置。

```
見出し: 「動画でも確認できます」/ "Watch the tutorial (optional)"
```

---

## Scope Policy

この follow-up に含めるもの:
- ゴール条件バナーの追加（HTML + CSS）
- サブタイトルの書き換え
- セクション見出し変更
- Step 2/3 のアイコン・文言・キー注記の分離
- 動画ブロックの steps 後への移動

この follow-up に含めないもの:
- インタラクティブな図解の追加
- 動画の差し替え・再制作
- viewer.html の UI 改修
- トップページの変更
- JS ロジックの変更

---

## Deliverables

- `docs/how-to-play.html` の差分（HTML + CSS）
- result での SC 1〜6 評価

---

## Review Checklist

- ページ冒頭にゴール条件が見える
- セクション見出しが「操作手順」ではない
- Step 2 と Step 3 で `← →` の意味が区別できる
- 動画なしでも 3 ステップだけで理解できる構成になっている
- 変更が `docs/how-to-play.html` に閉じている

---

## What This Follow-up Decides

- 遊び方ページの骨格を「操作説明」から「不安解消 + 最小理解補助」に変える
- ゴール条件・不安解消メッセージ・Step 分離の確定

## What This Follow-up Does Not Decide

- インタラクティブ図解の有無
- 難易度説明の追加
- トップページとの動的連携
