# Result

---

## Status

Completed

---

## 判定

**`framework/execution-model.md` → `legacy`**

---

## 読解サマリー

| セクション | 内容 | 性質 |
|---|---|---|
| execution type の定義 | cli / human / future-api の 3 類型、v0.1 での扱い付き | v0.1 限定の運用設計 |
| cli / human / future-api の違い | v0.1 具体例（subprocess コマンド等） | 現行 CLI 前提の実装説明 |
| v0.1 で CLI/Human を選んだ理由 | API キー不要・human executor 品質・後方互換等 | v0.1 意思決定の記録 |
| workspaces を分ける意味 | `planner/`・`builder/` ディレクトリ構造 | 現行 CLI 前提の運用形状 |
| role と executor の分離 | 「executor だけを差し替えられる」原則 | 原則は安定だが説明文 |
| execution-assignment.md の位置づけ | 現行 artifact の運用説明 | 現行運用形状 |
| 将来 API executor を足すときの考え方 | 具体的なファイル変更手順（現行パス前提） | 現行構造依存 |

---

## 判定根拠

### legacy 根拠

1. タイトルが「CLI / Human 前提の実行設計」と宣言しており、文書全体が現行 v0.1 実行環境に基づいている
2. v0.1 明示セクションが複数存在し、バージョン固有の運用判断が記述されている（redesign plan Rule 2 に該当）
3. `workspaces/` 構造・`execution-assignment.md` の具体的扱い・CLI subprocess 例 — いずれも現行 CLI 前提
4. 「将来 API executor を足すときの考え方」は現行 `src/apsf/` ファイル構造を参照しており、core 禁止事項「CLI エントリポイント前提の実装詳細」に接触している

### "core に見えた部分" の扱い

「role と executor の分離」原則は安定概念だが、この原則の contract はすでに Unit B で `src/apsf/core/` に着地済み:

- `ExecutionType` → `src/apsf/core/domain/models.py`
- `BaseExecutor` (ABC) → `src/apsf/core/executors/base.py`

`execution-model.md` はこれらの契約の説明文であり、契約そのものではない。説明文は `legacy` で十分。core inflation を防ぐため、「重要そう」を理由に core には入れない。

---

## run-018 迷い資産整理との整合

run-018 result.md の迷い資産記録:

> `framework/execution-model.md` — 抽象定義だが現行 CLI モデルの説明も含む可能性がある → 精読後に legacy 移行の可能性を残す

精読の結果、「現行 CLI モデルの説明」は全文に渡っており、legacy への移行が妥当と確認された。迷いは解消。

---

## Unit C への handoff

| 点 | 内容 |
|---|---|
| 判定 | `framework/execution-model.md` → `framework/legacy/` |
| 理由 | v0.1 運用前提。安定契約は core コードに着地済み |
| Unit C への影響 | legacy 受け皿に他の文書と同列で含めてよい。特別扱い不要 |
| 残り迷い資産 | `planning-patterns.md`・`pipeline.py` は今回スコープ外。Unit C 後に判断 |

---

## Success Criteria 照合

| # | 基準 | 結果 |
|---|---|---|
| 1 | placement が core / legacy / hold のいずれかで明示される | ✅ legacy |
| 2 | 判定理由が structural reading に基づいている | ✅ |
| 3 | run-018 の迷い資産整理と矛盾しない | ✅ |
| 4 | Unit C 前に ambiguity を 1 点減らしたと言える | ✅ |
| 5 | 文書移動指示や実装計画に逸脱していない | ✅（移動指示なし・Unit C への handoff のみ） |
