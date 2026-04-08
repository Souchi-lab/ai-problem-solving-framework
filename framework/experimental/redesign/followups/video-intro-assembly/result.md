# Result

---

## Status

Completed — 全モード適用済み

---

## 1. 実装差分サマリー

### 変更ファイル（4ファイル）

| ファイル | 変更内容 |
|---|---|
| `useAutoPlayer.ts` | `assembly_intro` dispatch 追加。当初 `--mode assembly` 専用だったが、最終的に全 sns モード（full_play / teaser / assembly）に適用。teaser は待機時間を短縮（1200ms）。 |
| `SNSOverlay.tsx` | `assembly_intro` フェーズ追加。`SCATTER_POSITIONS`（8点放射状）、`getAssemblyLayout(n)` でピース数に応じた cellSize と着地位置を動的生成。`--piece-offset` CSS変数でマージンも動的化。 |
| `App.css` | `.sns-assembly-container` / `.sns-assembly-piece` / `@keyframes sns-assembly-gather` / `.sns-assembly-hook` を追加。`cubic-bezier(0.22,1,0.36,1)` で自然な加速減速。 |
| `generate_sns_video.js` | `--mode assembly` フラグ追加（スタンドアロン演出録画用）。既存の full_play / teaser 動作は無変更。 |

### 実装規模

当初の想定より若干大きくなった（`getAssemblyLayout` の動的レイアウト計算が追加）。
ただし既存フェーズへの変更ゼロ、他フェーズへの副作用なし。

---

## 2. 試作動画の評価（3観点）

### 初見で完成形（直方体）が伝わるか

○ — `PieceShapeMini`（2D投影ミニチュア）が収束していく様子で
「何かのピースが組み合わさるパズル」であることが冒頭1秒で読み取れる。
直方体の3D形状そのものは見えないが、「ピースが集まる」構造は直感的に伝わる。

### 続きを見たくなるか

○ — 散らばり → 収束 → intro → ゲーム開始の流れが引きを作る。
演出に勢いがあり（cubic-bezier の ease-out 効果）、止まらずに見られる。

### ネタバレになりすぎないか

○ — PieceShapeMini は2D投影のため完成形の3D形状は伝わらない。
「どのピースが何個あるか」は見えるが「どう組むか」は見えない。
ネタバレリスクは許容範囲内と判断。

---

## 3. トレードオフ判定（「伝わる」vs「ネタバレ」）

plan で懸念した「伝わる ↔ ネタバレ」トレードオフは、
実装上ほぼ問題にならなかった。

理由: 2D投影ミニチュアを「散らばった → 集まった」として見せるだけで、
ゲームの解き方・配置手順は一切見えない。
完成形を示すことが「解答を示すこと」にはならない構造だった。

優先順位を決める必要はなく、両立できた。

---

## 4. 採用判断

**採用** — 全モード（full_play / teaser / assembly）に適用済み。

追加判断: 当初 Non-goal だった「全モード適用」を実装後に即実施した。
理由: モード間での演出統一はユーザーから自然な要求として出てきた判断であり、
scope 逸脱ではなく合理的な延長だった。

---

## 5. 形式評価（4点セットの実装タスクへの適合度）

### 機能したもの

- **Goal**: 範囲限定と非目標の定義が実装中の判断基準として機能した。
  「動画全体の再設計に広げない」という制約が実際に効いた。
- **Plan の Problem Structure**: パイプライン構造の確認フェーズとして機能した。
  実装前に「どのファイルのどこを変えるか」が整理された。
- **review skip の判断**: 「実装確認フェーズを経て即 build」は適切だった。
  review の追加は質的評価が必要な場面に絞るべきと再確認。

### 機能しなかったもの

- **Goal の Background**: `generate_puzzle_video.py` を想定していたが、
  実際のパイプラインは `generate_sns_video.js` + frontend overlay だった。
  前提調査を先にすべきタスクで goal の正確性が下がった。
- **Plan の Open Questions**: 実装前に解消されず、実装中に解消された。
  問い自体は有効だったが、plan 段階での答え出しを目指すべきだった。

### 形式の総評

**small-to-medium 実装タスクには4点セットは使える。ただし前提調査を goal/plan の前に行うことが条件。**

今回は「background の誤り」が plan に引き継がれたが、
実装確認フェーズ（パイプライン調査）を先に行ったことで軌道修正できた。
この「調査 → goal 修正 → plan 修正」の流れは APSF のループとして機能している。

---

## 6. Open Questions への答え（plan 記録として）

| 問い | 答え |
|---|---|
| どのレイヤーを使うか | CSS transform（canvas / SVG 不要）|
| scatter 半径・アニメ時間 | ±500-640px × ±900-940px / 1.1s cubic-bezier |
| assembly_intro 後に intro を維持するか | 維持（assembly_intro → intro の二段構成）|
| Three.js 参照が必要か | 不要（PieceShapeMini の2D投影で十分）|

---

## 7. 次の候補

- scatter バリアントの試作（形状に応じた散らばり方）
- hook テキストの A/B テスト（「Can you solve this?」vs 難易度別）
- assembly 演出の動画効果測定（SNS のエンゲージメント差分）
