# Result

---

## Status

Completed

---

## 1. 実装差分サマリー

| 変更 | 内容 | 規模 |
|---|---|---|
| 「はじめての方へ」セクション削除 | hero 主 CTA と重複していたカードセクションを削除。JS の dead reference も除去 | −34行 |
| Hero desc ゴール条件追加 | 「全ピースを埋めたらクリア。/ Fit all pieces to win.」を追加 | +2行 |
| Cleared: 0 / 0 初期値修正 | `<span>0</span>` → `<span></span>` | +4行 |

ファイル: `docs/index.html` のみ。1 commit。

---

## 2. 評価

### Success Criteria に対して

| # | 基準 | 結果 |
|---|---|---|
| 1 | 主語が「CTA 整理」に留まっている | ✅ `docs/index.html` 1ファイルに閉じた |
| 2 | 主 CTA と副 CTA の役割分担が明確になっている | ✅ hero に「まず1問」と「遊び方を見る」が1セットで残り、他に競合する CTA がない |
| 3 | 同じ意味の導線を繰り返さない | ✅ 「はじめての方へ」削除により、first puzzle への導線が hero のみに一本化 |
| 4 | トップが「最初の1問へ入る入口」として再構成されている | ✅ hero CTA → how-to → 難易度 → 一覧 という流れが素直になった |
| 5 | 遊び方は補助導線として残しつつ邪魔しない | ✅ 副 CTA として hero 内に存在。セクションとしても how-to-play が続く |
| 6 | result で「初見の迷いが減ったか」を narrow に評価できる | ✅ 変更が小さいので before/after の因果が明確 |

---

## 3. 採用判断

採用。

- 3変更とも本番採用
- 「はじめての方へ」CSS クラス（`.first-puzzle-card` 等）は DOM に要素がないため無害。
  クリーンアップは次回以降の CSS 整理 run で対応（Open Conditional）

---

## 4. 形式評価

| 要素 | 評価 |
|---|---|
| goal | 「CTA 整理」という主語が最後まで保たれた。スコープの壁として機能した |
| plan | 現状の HTML を読んでから書いたことで、変更箇所が事前に正確に特定できていた。「実装で確認した方が早い」類のタスクにフィットした |
| review | skip で妥当。変更が小さく、before/after が自明なため review より result の記録の方が有用 |
| result | 小さい変更ほど因果が明確で、result に書きやすい。今後の narrow run の基準になる |

### 今回で確認できた形式知

> **「削除」系の変更は、何を足したかより何が消えたかを先に書く。**
> 追加した行数は少なくても、削除で解決した問題が主体のため。

---

## 5. Closing

### Stable Baseline

- トップページの first puzzle 導線は hero 主 CTA のみ（「はじめての方へ」セクションは廃止）
- hero desc はゴール条件（全ピースを埋めたらクリア）を含む
- `Cleared: 0 / 0` の壊れた初期表示は解消済み

### Open Conditional

- `.first-puzzle-card` 等の CSS クラスが HTML 消去後も残っている。
  CSS 全体整理の run が発生した場合にクリーンアップ対象とする
- hero-cta-secondary「遊び方を見る」は `#how-to-play` アンカー（同ページスクロール）。
  `how-to-play.html` へのリンクに変えるかは、遊び方ページ改修 follow-up で判断

### Next Trigger

- 遊び方ページの改修（step 2/3 の ← → 混在問題・初心者不安解消・3ステップ図解）
- FW改善: run-021c1（Planner assignment design）へ戻る
