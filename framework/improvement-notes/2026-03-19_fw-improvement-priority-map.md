# FW Improvement Priority Map

Date: 2026-03-19
Scope: APSF framework improvement backlog
Purpose: 次の FW 改善 run を切るための優先度付き論点整理

---

## One-Line Summary

最優先は **phase / artifact / role の責務境界を締めること** であり、その次に **template と CLI / 文書の二重管理ズレを減らすこと**、その次に **実験系 run と親子 run 導入を見据えた運用拡張** を整理するのがよい。

---

## Priority Overview

| Priority | Theme | Why now |
|---|---|---|
| P0 | phase責務・artifact責務・role責務の境界整理 | ここが曖昧だと全 run に影響し、他の改善も設計しにくい |
| P1 | template間の重複整理 | 運用のたびに解釈ズレが増える |
| P1 | CLI と framework 文書の乖離整理 | 実装済み挙動と文書がズレると dogfood が壊れる |
| P1 | run 運用の暗黙知の明文化 | フレームワーク利用時の再現性が落ちる |
| P2 | transcript / result / review / judge 境界の再定義 | phase責務整理の派生だが、二次成果物と最終判断のズレが目立つ |
| P2 | 実験系 run に弱い箇所の整理 | 既に SoChi BLOCKS 系 run で需要が見えている |
| P2 | 再利用しづらいルール・命名規則の整理 | 規模が大きくなるほど効いてくる |
| P3 | 親子 run 導入時に衝突しそうな箇所の先回り整理 | 既に提案 run はあるが、本体 FW への反映は未整理 |

---

## P0: 責務境界の再整理

### 1. Phase Responsibility Ambiguity

**Issue**

- `framework/workflow/v0.1.md` と `framework/workflow/v0.2.md` で phase 数や責務が異なる
- `build / review / improve / verify / result` の境界が run ごとに解釈されやすい
- `framework/overview.md` はパターン集として有用だが、phase責務の正規定義として読むと粒度が混ざる

**Why priority is high**

- phase責務が曖昧だと template 改善も CLI 改善も全部ぶれる
- user が気にしている `review / judge / result / transcript` 境界問題の根本でもある

**Likely improvement run**

- `apsf_phase-responsibility-clarification`

**Expected deliverable**

- v0.1 / v0.2 を横断した責務比較表
- 「各 phase でやること / やらないこと」一覧
- 人間 Judge と Critic の境界を 1 文で固定した定義集

---

## P1: 重複と乖離の削減

### 2. Template Overlap

**Issue**

- `framework/templates/` と `runs/_template/` の二層構造は明示されているが、更新責務はまだ運用依存
- `result.md` / `transcript.md` / `review.md` / `improve.md` などに似た説明が分散している
- v0.2 用の `research-input.md` や `improve-plan.md` はあるが、どの run で使うかが暗黙知寄り

**Evidence**

- [`runs/README.md`](C:/Users/PC_User/PRJ/ai-problem-solving-framework/runs/README.md)
- [`framework/templates/plan.md`](C:/Users/PC_User/PRJ/ai-problem-solving-framework/framework/templates/plan.md)
- [`framework/templates/transcript.md`](C:/Users/PC_User/PRJ/ai-problem-solving-framework/framework/templates/transcript.md)

**Likely improvement run**

- `apsf_template-dedup-and-layering`

**Expected deliverable**

- template責務マップ
- 原本とコピー用 template の同期ルール
- optional template の利用条件表

### 3. CLI vs Framework Doc Drift

**Issue**

- CLI 実装は [`src/apsf/cli/main.py`](C:/Users/PC_User/PRJ/ai-problem-solving-framework/src/apsf/cli/main.py) が実態だが、利用者は `README.md` や `framework/workflow/*.md` を先に読む
- `generate-transcript` と `transcript` の両方が見えるなど、説明の入口がやや散っている
- v0.2 で `verify` や `improve-plan` が議論されている一方、CLI 側の phase 実装はまだ v0.1 中心

**Why priority is high**

- dogfood で最も「使ってみてズレる」体験を生みやすい
- framework の信用を落とすのは機能不足より説明ズレ

**Likely improvement run**

- `apsf_cli-framework-alignment-audit`

**Expected deliverable**

- CLI 実装 vs 文書仕様の差分表
- obsolete / future / current のラベル整理
- README と workflow の導線再設計案

### 4. Implicit Run Operations

**Issue**

- 「いつ transcript を書くか」
- 「いつ improve で止めてよいか」
- 「どの run で v0.2 optional phases を使うか」
- 「外部観察が必要かどうか」

などが文書上は部分的にあるが、実運用ではかなり暗黙知になっている

**Evidence**

- [`runs/README.md`](C:/Users/PC_User/PRJ/ai-problem-solving-framework/runs/README.md)
- [`framework/workflow/v0.1.md`](C:/Users/PC_User/PRJ/ai-problem-solving-framework/framework/workflow/v0.1.md)
- [`framework/workflow/v0.2.md`](C:/Users/PC_User/PRJ/ai-problem-solving-framework/framework/workflow/v0.2.md)

**Likely improvement run**

- `apsf_run-operations-implicit-rules`

**Expected deliverable**

- run運用の暗黙ルール集
- 初回利用者向け「迷いやすい判断点」一覧
- run archetype ごとの推奨 phase 構成

---

## P2: 実運用拡張に向けた整理

### 5. Transcript / Result / Review / Judge Boundary

**Issue**

- `transcript.md` は二次成果物と明記されているが、summary と result の責務境界がまだ読者依存
- `review.md` と `improve.md` は Critic / Judge の分離を前提にしているが、Judge の最終記録が `result.md` にどう落ちるかは run ごとの差が大きい
- v0.2 では `verify` が入ることでさらに境界が増える

**Likely improvement run**

- `apsf_artifact-boundary-transcript-result-review-judge`

**Expected deliverable**

- artifact責務表
- 一次記録 / 二次成果物 / 判定記録の定義
- transcript 自動生成が参照すべき正規ソースの固定

### 6. Weakness for Experimental Runs

**Issue**

- 既存 APSF は直列改善に強いが、探索型・実験型・比較型 run では Build / Review の意味が変わりやすい
- `framework/overview.md` や SoChi BLOCKS 系 run に知見は散っているが、実験系 archetype としては未整理

**Likely improvement run**

- `apsf_experimental-run-patterns`

**Expected deliverable**

- 実験系 run archetype 集
- 比較型 Review / acceptance型 Verify の使い分け
- 実験ログを run に落とす最小構造

### 7. Reuse-Unfriendly Rules and Naming

**Issue**

- run 命名規則は実装上はシンプルだが、実運用では suffix や variant の足し方が安定していない
- case-key / topic / version / experiment suffix の持たせ方が run ごとに揺れやすい

**Evidence**

- [`src/apsf/storage/run_repository.py`](C:/Users/PC_User/PRJ/ai-problem-solving-framework/src/apsf/storage/run_repository.py)
- [`src/apsf/cli/main.py`](C:/Users/PC_User/PRJ/ai-problem-solving-framework/src/apsf/cli/main.py)

**Likely improvement run**

- `apsf_reusable-naming-and-rulebook`

**Expected deliverable**

- 命名規則の階層化
- suffix / version / experiment 用法のルール
- 再利用しやすい run archetype 名のカタログ

---

## P3: 親子 run 導入を見据えた衝突点

### 8. Parent/Child Run Collision Map

**Issue**

- 既に `2026-03-18-015_apsf_parent-child-run-model` で提案は整理済み
- ただし本体 framework 側では、phase / naming / transcript / result / CLI / README のどこに衝突するかが未マッピング
- 特に child run が `runs/` 直下へ並列配置されると、論理上の親子関係が filesystem 上で失われる

**Likely collision points**

- run naming validator
- run directory topology
- `runs/README.md` の run lifecycle 説明
- transcript の参照順
- result / verify / aggregation の責務
- `apsf next` の phase 判定前提

**Likely improvement run**

- `apsf_parent-child-collision-audit`

**Expected deliverable**

- parent/child run 導入時の衝突点一覧
- 親 run 配下に child run を置くかどうかの topology ルール
- 後方互換を壊さない導入順序
- 既存 CLI / template への影響マップ

---

## Recommended Order

### First wave

1. `apsf_phase-responsibility-clarification`
2. `apsf_cli-framework-alignment-audit`
3. `apsf_template-dedup-and-layering`

### Second wave

4. `apsf_artifact-boundary-transcript-result-review-judge`
5. `apsf_run-operations-implicit-rules`
6. `apsf_experimental-run-patterns`

### Third wave

7. `apsf_reusable-naming-and-rulebook`
8. `apsf_parent-child-collision-audit`

---

## Suggested Next Run

最初に切るならこれが一番効く。

**`apsf_phase-responsibility-clarification`**

理由:

- あなたが気にしている論点の半分以上がここにぶら下がっている
- transcript / result / review / judge 境界もここから整理しやすい
- parent/child run や experimental run の設計にも下地として効く

その次は

**`apsf_cli-framework-alignment-audit`**

がよい。設計と実装のズレを先に可視化しておくと、以降の FW 改善が無駄撃ちになりにくい。

---

## Notes

- このメモは issue 一覧ではなく、**次の APSF 改善 run 候補を優先度順に並べた backlog** として使う
- P0 / P1 は framework の基礎整備、P2 は運用拡張、P3 は将来衝突の先回り、という位置づけで読むと分かりやすい
