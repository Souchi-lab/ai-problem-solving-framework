# Goal

Run: 2026-03-29-033_fw-improvement_reconstruction-final-handoff
Date: 2026-03-29

---

## Goal Readiness Check

- `run-018` から `run-032` までの reconstruction 系 run が一通り完了している
- `framework/core/` と `framework/legacy/` は repo 上に実体として着地済みである
- `src/apsf/core/` と `src/apsf/legacy/` の主要 Python 移行も完了している
- `execution-model.md` と `pipeline.py` の placement ambiguity は解消済みである
- 主要保留論点はなく、残るのは個別の実移動 run と全体 handoff の整理のみである
- 今回は design-only handoff run であり、新しい移行実装は行わない

Decision: Proceed

---

## Objective

APSF 再構築系列の最終 handoff として、
何がすでに着地したか、
どの判断が確定したか、
残りが何か、
次にどこから実務へ返すかを
Markdown で固定する。

今回の run では、
`run-018` 以降の結果を圧縮して、
再構築系列を result-complete として閉じるための
全体 summary / status / next-trigger を作る。

---

## Scope

この run で扱うのは次だけである。

1. reconstruction 系 run の着地要約
2. 確定した structure / placement の整理
3. 未完了ではなく「次にやる個別実務」の整理
4. 次 trigger の固定

---

## Constraints

### 含めるもの

- `run-018` 〜 `run-032` の result 読み
- core / legacy / experimental / viewer の現状態整理
- reconstruction 後の next-step handoff

### 含めないもの

- 新しい placement 判定
- 新しい移行実装
- GUI 実装
- follow-up template の再議論
- SoChi BLOCKS 側タスク

### 判断上の制約

- 「全部終わった」と誇張しない
- reconstruction 系として何が閉じたかを正確に書く
- 残りを vague な future work ではなく、個別 run に切れる形で書く

---

## Success Criteria

1. reconstruction 系で何が着地したかが一読で分かる
2. `core / legacy / experimental / viewer` の現状態が整理される
3. `execution-model.md` と `pipeline.py` の最終扱いが回収される
4. 「主要保留論点は解消済み」が過不足なく伝わる
5. 次の個別実務 run に自然につながる

---

## Verification

- 既存 run を再要約した handoff になっている
- 新しい実装や判定を足していない
- 次 trigger が 1〜3 本の具体 run に落ちている

---

## Non-Goals

- 新しい移行 run の実施
- GUI 実装
- APSF 全体の最終完成宣言

---

## Inputs to Respect

- `runs/fw-improvement/2026-03-28-018_fw-improvement_reconstruction-asset-classification/result.md`
- `runs/fw-improvement/2026-03-29-019_fw-improvement_reconstruction-implementation-planning/result.md`
- `runs/fw-improvement/2026-03-29-020_fw-improvement_reconstruction-unit-a-core-docs/result.md`
- `runs/fw-improvement/2026-03-29-021_fw-improvement_reconstruction-unit-b-core-python/result.md`
- `runs/fw-improvement/2026-03-29-022_fw-improvement_execution-model-placement-read/result.md`
- `runs/fw-improvement/2026-03-29-023_fw-improvement_reconstruction-unit-c-legacy-landing-planning/result.md`
- `runs/fw-improvement/2026-03-29-024_fw-improvement_reconstruction-unit-c2-legacy-python-skeleton/result.md`
- `runs/fw-improvement/2026-03-29-025_fw-improvement_reconstruction-unit-c1-legacy-docs/result.md`
- `runs/fw-improvement/2026-03-29-026_fw-improvement_reconstruction-unit-c3-legacy-python-migration-planning/result.md`
- `runs/fw-improvement/2026-03-29-027_fw-improvement_reconstruction-unit-c3-phase1-storage-providers/result.md`
- `runs/fw-improvement/2026-03-29-028_fw-improvement_reconstruction-unit-c3-phase2-executors-config-prompts-light-orchestration/result.md`
- `runs/fw-improvement/2026-03-29-029_fw-improvement_reconstruction-unit-c3-phase3-agents-cli-heavy-orchestration-planning/result.md`
- `runs/fw-improvement/2026-03-29-030_fw-improvement_reconstruction-unit-c3-phase3a-agents-assignment/result.md`
- `runs/fw-improvement/2026-03-29-031_fw-improvement_reconstruction-unit-c3-phase3b-specialist-cli/result.md`
- `runs/fw-improvement/2026-03-29-032_fw-improvement_pipeline-placement-read/result.md`

---

## Desired Landing

この run の着地は、
reconstruction 系全体が
「どこまで終わり、何が確定し、次に何を個別 run として進めるか」
まで整理された最終 handoff を持つ状態である。

これにより、
再構築系列は result-complete として閉じつつ、
以後は必要な局所 run のみを切って進められるようにする。
