# Goal

Run: 2026-03-29-022_fw-improvement_execution-model-placement-read
Date: 2026-03-29

---

## Goal Readiness Check

- `run-018` で `framework/execution-model.md` は迷い資産として明示されている
- `run-019` では Unit A から除外され、初手移行対象に含めない判断が固定されている
- Unit A / Unit B は完了しており、次に Unit C の legacy landing planning を始める前段にある
- 今回は design-only read run であり、ファイル移動やコード変更は行わない

Decision: Proceed

---

## Objective

`framework/execution-model.md` を精読し、
この文書が現在の再構築方針において
`framework/core/` に置くべき資産か、
`framework/legacy/` に置くべき資産か、
あるいは引き続き保留すべき資産かを、
根拠つきで narrow に判定する。

今回の run の役割は、
Unit C の受け皿設計に入る前に
`execution-model.md` の placement ambiguity を 1 点だけ減らすことである。

---

## Scope

この run で扱うのは次だけである。

1. `framework/execution-model.md` の精読
2. core / legacy / hold のいずれが妥当かの判定
3. 判定理由の要約
4. Unit C への影響の短い handoff

---

## Constraints

### 含めるもの

- `framework/execution-model.md` の本文読解
- `run-018` / `run-019` の既存判断との整合確認
- placement 判定のための短い比較

### 含めないもの

- `planning-patterns.md` の精読
- `src/apsf/orchestration/pipeline.py` の精読
- 実ファイル移動
- README 更新
- Unit C 全体の設計

### 判断上の制約

- 「重要そうだから core」にしない
- 現行 CLI / orchestration の説明を含むなら legacy 寄りの可能性を正直に残す
- 無理に即断せず、保留が最も honest なら hold を選んでよい

---

## Success Criteria

1. `framework/execution-model.md` の placement が core / legacy / hold のいずれかで明示される
2. 判定理由が structural reading に基づいている
3. `run-018` の迷い資産整理と矛盾しない
4. Unit C 前に ambiguity を 1 点減らしたと言える
5. 文書移動指示や実装計画に逸脱していない

---

## Verification

- `framework/execution-model.md` の読解結果が要約されている
- 判定が core / legacy / hold のどれかに閉じている
- 判定理由が Unit C の次判断に接続できる

---

## Non-Goals

- `planning-patterns.md` や `pipeline.py` の扱いを同時に決めること
- `framework/legacy/` / `src/apsf/legacy/` の構造設計
- `execution-model.md` の書き換え
- `execution-model.md` の実移動

---

## Inputs to Respect

- `runs/fw-improvement/2026-03-28-018_fw-improvement_reconstruction-asset-classification/result.md`
- `runs/fw-improvement/2026-03-29-019_fw-improvement_reconstruction-implementation-planning/result.md`
- `framework/execution-model.md`

特に次を守ること。

- `execution-model.md` は現時点で迷い資産として扱われている
- Unit A / B の完了を壊さない
- Unit C の前段として narrow に閉じる

---

## Desired Landing

この run の着地は、
`framework/execution-model.md` の placement ambiguity が
1 本分だけ解消され、
次の Unit C planning run が
より明確な境界で始められる状態である。

結果は、
「core か legacy かをどう読むべきか」
を短く固定する handoff で十分であり、
再構築全体の拡張議論に広げない。
