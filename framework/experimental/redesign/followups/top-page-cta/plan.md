# Plan

---

## Follow-up Context

- Parent series: SoChi BLOCKS 初回体験改善
- Previous result: tutorial video follow-up 完了。SNS 動画基盤は整備済み
- New trigger: トップページの CTA 整理と first-playable 導線の明確化
- Scope limit: `docs/index.html` の CTA 周辺のみ。遊び方ページ・viewer・React コンポーネントは触らない
- Non-goals: 遊び方ページ全面改修 / 3ステップ図解 / UI コンポーネント全般の刷新

---

## Run Metadata

- Follow-up: top-page-cta
- Goal: 主 CTA「まず1問やってみる」と副 CTA「遊び方を見る」の役割分担を明確にし、同じ意味の導線を繰り返さない構成に整理する
- Output focus: `docs/index.html` の差分（3箇所）
- Non-goal reminder: 遊び方ページの改修・3ステップ図解・viewer 側の変更はスコープ外

---

## Goal Readiness Check

- `docs/index.html` を読んで現状の CTA 配置を把握済み
- 重複している導線が特定できている
- 変更後の HTML 文言が準備できている

Decision: Proceed

---

## Problem Structure

### 現状の CTA 配置

```
[Hero]
  ├─ 主 CTA: まず1問やってみる → (hero-cta-primary)   ✅ 正しい
  └─ 副 CTA: 遊び方を見る      (hero-cta-secondary)  ✅ 正しい

[はじめての方へ セクション]
  └─ first-puzzle-card: 最初の1問を解いてみよう →      ❌ 主 CTA と同じ puzzle を指す重複

[パズル一覧上部]
  └─ 今日の1問バナー: featured-card                  △ 別セクション・別文脈なので許容
```

### 問題点の整理

| # | 問題 | 深刻度 | 対応 |
|---|---|---|---|
| A | 「はじめての方へ」カードが hero 主 CTA と同じ puzzle を指す | 高 | 削除 |
| B | `Cleared: 0 / 0` — HTML 初期値が 0/0 のまま DOM に残る | 中 | 初期値を空にする |
| C | Hero desc がゴール条件を明示していない | 低 | 1行追加 |

---

## Selected Approach

### 変更 1: 「はじめての方へ」セクション削除

削除対象（l.667–688）:
```html
<!-- ── [Task 1-2] はじめての方へ ── -->
<div class="first-puzzle-section"> ... </div>
```

理由:
- hero 主 CTA「まず1問やってみる」が同じ目的を果たしている
- 2つ並ぶことで「どちらを押せばよいか」の迷いが生まれる
- JavaScript 側の `setFirstPuzzleLinks` は hero-cta-primary に絞ってよい

### 変更 2: `Cleared: 0 / 0` 空状態の修正

現状の HTML の初期値:
```html
<span id="prog-total">0</span> / <span id="prog-max">0</span>
<span id="prog-total-en">0</span> / <span id="prog-max-en">0</span>
```

JS は `clearedTotal === 0` のとき `return` するため表示されないが、
CSS や timing 次第で `0 / 0` が一瞬見える可能性がある。

対応: 初期値を空文字に変更
```html
<span id="prog-total"></span> / <span id="prog-max"></span>
<span id="prog-total-en"></span> / <span id="prog-max-en"></span>
```

### 変更 3: Hero desc にゴール条件を 1 行追加

現状:
```html
<p class="hero-desc ja">3Dで考えるペントミノパズル</p>
<p class="hero-desc en">A 3D pentomino puzzle</p>
```

改善後:
```html
<p class="hero-desc ja">3Dで考えるペントミノパズル。全ピースを埋めたらクリア。</p>
<p class="hero-desc en">A 3D pentomino puzzle. Fit all pieces to win.</p>
```

---

## Scope Policy

この follow-up に含めるもの:
- 「はじめての方へ」セクションの削除
- `Cleared: 0 / 0` 初期値修正
- Hero desc へのゴール条件追加

この follow-up に含めないもの:
- 遊び方ページ（how-to-play.html）の改修
- step 2 / step 3 の ← → アイコン混在問題（要件 7）
- 3ステップ図解の追加
- 難易度カードの文言改善
- JS・React コンポーネントの変更

---

## Deliverables

- `docs/index.html` の差分（変更 1〜3）
- result での評価（導線が整理されたか・破損表示が消えたか）

---

## Review Checklist

- hero 主 CTA と同じ puzzle を指す重複リンクがなくなっている
- `Cleared: 0 / 0` の空状態が DOM に残らない
- 変更が `docs/index.html` に閉じている
- 遊び方・難易度・パズル一覧・About は変更していない

---

## Planned Output Shape

result は次の構成でまとめる:
1. 差分サマリー（変更箇所・行数）
2. 導線整理の評価（迷いが減ったか）
3. 今回スコープ外にした問題の記録（step 2/3 の ← → 混在、要件 7）
4. 形式評価

---

## Assumptions & Open Questions

Assumptions:
- `first-puzzle-card` の `setFirstPuzzleLinks` 呼び出しを hero-cta-primary のみに絞っても動作する
- 「今日の1問」バナーは returning user 向け機能として残してよい

Open questions:
- hero-cta-secondary「遊び方を見る」は `#how-to-play` アンカーで同ページ内スクロール。このままでよいか、`how-to-play.html` へのリンクに変えるかは今回判断外

---

## What This Follow-up Decides

- 「はじめての方へ」セクションを削除して CTA を hero に一本化する
- ゴール条件を hero desc に 1 行で明示する

## What This Follow-up Does Not Decide

- 遊び方ページの構成
- step 2 / step 3 の操作分離表現（要件 7）
- 3ステップ図解の有無
