# Goal

Run: 2026-03-29-032_fw-improvement_pipeline-placement-read
Date: 2026-03-29

---

## Goal Readiness Check

- `run-018` で `src/apsf/orchestration/pipeline.py` は迷い資産として明示されている
- Phase 1〜3 の実装を通じて、`pipeline.py` は core 契約側だけを参照しているという観察が蓄積されている
- ただし具象実装（`input()` 等）を含むため、core / legacy の最終判定はまだ保留である
- `framework/core/` / `framework/legacy/` / `src/apsf/core/` / `src/apsf/legacy/` の骨格はすでに着地済みである
- 今回は design-only read run であり、ファイル移動やコード変更は行わない

Decision: Proceed

---

## Objective

`src/apsf/orchestration/pipeline.py` を精読し、
この実装が現在の再構築方針において
`core` に置くべきか、
`legacy` に置くべきか、
あるいは引き続き `hold` とするべきかを、
根拠つきで narrow に判定する。

今回の run の役割は、
再構築の最後の主要保留資産について
placement ambiguity を 1 点だけ解消することである。

---

## Scope

この run で扱うのは次だけである。

1. `src/apsf/orchestration/pipeline.py` の精読
2. `core / legacy / hold` のいずれが妥当かの判定
3. 判定理由の要約
4. reconstruction 最終 handoff への短い接続

---

## Constraints

### 含めるもの

- `src/apsf/orchestration/pipeline.py` の本文読解
- Phase 1〜3 の観察結果との整合確認
- placement 判定のための短い比較

### 含めないもの

- 実ファイル移動
- import 修正
- viewer の再配置
- 新しい分割設計
- reconstruction 全体 result の執筆

### 判断上の制約

- 「core 契約しか参照していない」だけで自動的に core にしない
- 具象実装や運用前提が強ければ legacy / hold を正直に残す
- 無理に即断せず、hold が最も honest なら hold を選んでよい

---

## Success Criteria

1. `pipeline.py` の placement が `core / legacy / hold` のいずれかで明示される
2. 判定理由が structural reading に基づいている
3. Phase 1〜3 の観察と矛盾しない
4. reconstruction の保留論点を 1 点減らしたと言える
5. 実装計画や追加移行 run に逸脱していない

---

## Verification

- `pipeline.py` の読解結果が要約されている
- 判定が `core / legacy / hold` のどれかに閉じている
- 判定理由が reconstruction 最終 handoff に接続できる

---

## Non-Goals

- `pipeline.py` の実移動
- `pipeline.py` の書き換え
- viewer の再配置
- reconstruction 最終 result の作成

---

## Inputs to Respect

- `runs/fw-improvement/2026-03-28-018_fw-improvement_reconstruction-asset-classification/result.md`
- `runs/fw-improvement/2026-03-29-026_fw-improvement_reconstruction-unit-c3-legacy-python-migration-planning/result.md`
- `runs/fw-improvement/2026-03-29-027_fw-improvement_reconstruction-unit-c3-phase1-storage-providers/result.md`
- `runs/fw-improvement/2026-03-29-028_fw-improvement_reconstruction-unit-c3-phase2-executors-config-prompts-light-orchestration/result.md`
- `runs/fw-improvement/2026-03-29-029_fw-improvement_reconstruction-unit-c3-phase3-agents-cli-heavy-orchestration-planning/result.md`
- `runs/fw-improvement/2026-03-29-031_fw-improvement_reconstruction-unit-c3-phase3b-specialist-cli/result.md`
- `src/apsf/orchestration/pipeline.py`

特に次を守ること。

- `pipeline.py` は最後の主要保留資産である
- Phase 1〜3 の観察を尊重する
- 今回は判定だけで閉じる

---

## Desired Landing

この run の着地は、
`src/apsf/orchestration/pipeline.py` の placement ambiguity が
1 本分だけ解消され、
reconstruction 系全体を
最終 handoff に向けて閉じられる状態である。

結果は、
「pipeline.py をどう読むべきか」
を短く固定する handoff で十分であり、
新しい大きな設計論へ広げない。
