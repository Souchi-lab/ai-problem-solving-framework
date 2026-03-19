# Legacy Run Inventory

作成日: 2026-03-19
目的: `runs/` 直下に残る legacy run の棚卸し・分類・移行優先度案

---

## 移行済み（参考）

| taxonomy | 件数 |
|---|---|
| `fw-improvement/` | 10 run（003〜013） |
| `work/` | 1 run（001） |

---

## Legacy Run 一覧（移行対象）

| run 名 | 推奨 taxonomy | 優先度 | 移行注意点 | cross-ref 外部参照数 |
|---|---|---|---|---|
| `2026-03-15_sochi-blocks_sns-post-template` | work | P3 | 命名が旧形式（番号なし）。18 ファイルから参照される最多参照 run | 18（多） |
| `2026-03-16_sochi-blocks_sns-post-template‐v2` | work | P3 | 同上。旧命名形式。5 ファイルから参照 | 5（中） |
| `2026-03-17_apsf-dogfood_act-v0-1-apikeyless` | fw-improvement | P2 | `apsf-dogfood` 系。外部参照なし | 0（少） |
| `2026-03-17_apsf-dogfood_act-v0-validation` | fw-improvement | P2 | 同上。1 ファイルから参照 | 1（少） |
| `2026-03-17_apsf-dogfood_codex-pipe-test` | fw-improvement | P2 | 外部参照なし | 0（少） |
| `2026-03-17_apsf-dogfood_orchestrator-ux-check` | fw-improvement | P2 | 外部参照なし | 0（少） |
| `2026-03-17_apsf-dogfood_pipe-workflow-validation` | fw-improvement | P2 | 3 ファイルから参照 | 3（少） |
| `2026-03-17_apsf-dogfood_write-phase-test` | fw-improvement | P2 | 外部参照なし | 0（少） |
| `2026-03-17_apsf-dogfood_write-phase-ux-recheck` | fw-improvement | P2 | 外部参照なし | 0（少） |
| `2026-03-17_apsf-fw-dogfood_act-no-force-needed` | fw-improvement | P2 | 外部参照なし | 0（少） |
| `2026-03-18-001_sochi-blocks_caption-quality` | work | P2 | 3 ファイルから参照 | 3（少） |
| `2026-03-18-002_apsf_setup-plan-chaining` | fw-improvement | P2 | 1 ファイルから参照 | 1（少） |
| `2026-03-18-003_apsf_permission-boundary` | fw-improvement | P2 | 外部参照なし | 0（少） |
| `2026-03-18-004_sochi-blocks_auto-publish-removed-pieces` | work | P2 | 1 ファイルから参照 | 1（少） |
| `2026-03-18-005_sochi-blocks_caption-cleanup` | work | P2 | 4 ファイルから参照 | 4（中） |
| `2026-03-18-006_apsf_post-judge-verification-pattern` | fw-improvement | P2 | 外部参照なし | 0（少） |
| `2026-03-18-007_sochi-blocks_sns-inflow-video-experiment` | work | P2 | 外部参照なし | 0（少） |
| `2026-03-18-008_apsf_external-benchmark-input-improvement` | fw-improvement | P2 | 2 ファイルから参照 | 2（少） |
| `2026-03-18-008_sochi-blocks_hook-ab-experiment-design` | work | P2 | **番号重複（008）**。外部参照なし | 0（少） |
| `2026-03-18-009_sochi-blocks_tiktok-hook-test-execution` | work | P2 | 外部参照なし | 0（少） |
| `2026-03-18-010_apsf_external-input-build-alignment` | fw-improvement | P2 | 外部参照なし | 0（少） |
| `2026-03-18-011_apsf_external-input-framework-impl` | fw-improvement | P2 | 外部参照なし | 0（少） |
| `2026-03-18-012_sochi-blocks_tiktok-playwright-autopublish` | work | P2 | 外部参照なし | 0（少） |
| `2026-03-18-013_sochi-blocks_twitter-playwright-autopublish` | work | P2 | 外部参照なし | 0（少） |
| `2026-03-18-014_sochi-blocks_x-post-optimization` | work | P2 | 3 ファイルから参照 | 3（少） |
| `2026-03-18-015_apsf_parent-child-run-model` | fw-improvement | P2 | 4 ファイルから参照 | 4（中） |
| `2026-03-18-016_sochi-blocks_x-post-experiment` | work | P2 | **child run あり**（016c1/c2/c3）。parent ごと移動が必要。10 ファイルから参照 | 10（多） |
| `2026-03-18-016_sochi-blocks_x-post-experiment-execution` | work | P2 | **番号重複（016）**。外部参照なし | 0（少） |
| `2026-03-18-017_sochi-blocks_x-thread-post-impl` | work | P2 | 外部参照なし | 0（少） |
| `2026-03-18-018_sochi-blocks_cross-platform-shared-puzzle-publish` | work | P2 | 1 ファイルから参照 | 1（少） |
| `2026-03-19-002_apsf_build-auto-progression-policy-retrospective` | fw-improvement | P1 | 外部参照なし | 0（少） |
| `2026-03-19-005_sochi-blocks_publish-pipeline` | work | P1 | **本日クローズ済み**。child run（005c1/c2/c3）あり。2 ファイルから参照 | 2（少） |
| `2026-03-19-012_apsf_run-taxonomy-filesystem-exec` | fw-improvement | P1 | **本日クローズ済み**。1 ファイルから参照 | 1（少） |

---

## 注意事項

### 命名形式が旧形式（番号なし）
- `2026-03-15_sochi-blocks_sns-post-template`
- `2026-03-16_sochi-blocks_sns-post-template‐v2`
- `2026-03-17_apsf-dogfood_*`（8 run）
- `2026-03-17_apsf-fw-dogfood_act-no-force-needed`

これらは現在の命名規則（`YYYY-MM-DD-NNN_case_topic`）に合っていないため、移行後も命名はそのまま維持する（rename は別判断）。

### 番号重複 run
- `2026-03-18-008_apsf_...` と `2026-03-18-008_sochi-blocks_...` が同じ 008 を使用
- `2026-03-18-016_sochi-blocks_x-post-experiment` と `2026-03-18-016_sochi-blocks_x-post-experiment-execution` が同じ 016 を使用

移行時に混乱が起きないよう注意。rename は今回スコープ外。

### child run を持つ parent run
- `2026-03-18-016_sochi-blocks_x-post-experiment`（016c1/c2/c3）: parent ディレクトリごと `work/` に移動する
- `2026-03-19-005_sochi-blocks_publish-pipeline`（005c1/c2/c3）: 同上

---

## 統計

| 推奨 taxonomy | 件数 |
|---|---|
| fw-improvement | 14 run |
| work | 19 run |
| **合計** | **33 run** |

---

## 次に移すべき候補トップ 5

外部参照が少なく、クローズ済みで移行リスクが低いものを優先。

| 順位 | run 名 | taxonomy | 理由 |
|---|---|---|---|
| 1 | `2026-03-19-002_apsf_build-auto-progression-policy-retrospective` | fw-improvement | 本日クローズ済み・外部参照 0・移行コスト最小 |
| 2 | `2026-03-19-012_apsf_run-taxonomy-filesystem-exec` | fw-improvement | 本日クローズ済み・外部参照 1・移行コスト最小 |
| 3 | `2026-03-19-005_sochi-blocks_publish-pipeline` | work | 本日クローズ済み・child run あり（まとめて移動）・外部参照 2 |
| 4 | `2026-03-17_apsf-dogfood_*`（外部参照 0 の 7 run） | fw-improvement | 一括移動可能・外部参照なし・cross-ref 更新不要 |
| 5 | `2026-03-18-003_apsf_permission-boundary` / `2026-03-18-006_apsf_post-judge-verification-pattern` | fw-improvement | 外部参照 0・単独移動でリスクなし |
