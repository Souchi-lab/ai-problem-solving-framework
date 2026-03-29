# Goal

Run: 2026-03-29-030_fw-improvement_reconstruction-unit-c3-phase3a-agents-assignment
Date: 2026-03-29

---

## Goal Readiness Check

- `run-029` で Phase 3 は `3A / 3B` に分割済みである
- `3A` は `cli` 非依存の独立移行単位として定義されている
- 対象は `builder / judge / junior_builder` と `assignment_service / execution_assignment_service` に限定されている
- `src/apsf/legacy/` はすでに skeleton と周辺実装受け皿を持っている
- 今回は Codex 実装 run であり、Phase 3A の実移行を行う

Decision: Proceed

---

## Objective

APSF 再構築の Unit C3 Phase 3A として、
`builder`、`judge`、`junior_builder`、
`assignment_service`、`execution_assignment_service`
を `src/apsf/legacy/` 側へ landing させる。

今回の run では、
`cli` 非依存で独立して移行できる最初の agent / orchestration 単位として、
必要最小限の import 更新と `pytest -q` による確認までを行う。

---

## Scope

この run で扱うのは次だけである。

1. `builder / judge / junior_builder` の legacy landing
2. `assignment_service / execution_assignment_service` の legacy landing
3. それに伴う最小限の import 更新
4. `pytest -q` による確認

---

## Constraints

### 含めるもの

- `src/apsf/agents/builder.py`
- `src/apsf/agents/judge.py`
- `src/apsf/agents/junior_builder.py`
- `src/apsf/orchestration/assignment_service.py`
- `src/apsf/orchestration/execution_assignment_service.py`
- それらの caller / import 更新
- `pytest -q`

### 含めないもの

- `planner / critic` の移行
- `specialist_registry.py` の移行
- `cli/` 本体の移行
- `act_service.py` の移行
- `pipeline.py` の placement 確定

### 判断上の制約

- 3A は `cli` 非依存単位に閉じる
- import 更新は 3A caller に必要な最小限に留める
- 3B に属する `planner / critic / specialist_registry / cli / act_service` を持ち込まない

---

## Success Criteria

1. 対象 5 ファイルが `src/apsf/legacy/` 側へ landing する
2. 3A caller の import 更新で整合が取れる
3. `planner / critic / specialist_registry / cli / act_service` を巻き込んでいない
4. `pytest -q` の結果が確認される
5. Phase 3B に必要な境界がむしろ明確になる

---

## Verification

- landing 後のディレクトリ構造が存在する
- import 更新が反映されている
- `pytest -q` の結果が記録されている
- 今回の変更が Phase 3A の主語に留まっている

---

## Non-Goals

- 3B 実装
- `pipeline.py` の最終判断
- viewer の再配置
- reconstruction 全体完了

---

## Inputs to Respect

- `runs/fw-improvement/2026-03-29-029_fw-improvement_reconstruction-unit-c3-phase3-agents-cli-heavy-orchestration-planning/result.md`
- `src/apsf/core/`
- `src/apsf/legacy/`

特に次を守ること。

- 3A は `cli` 非依存単位である
- `builder / judge / junior_builder + assignment_service / execution_assignment_service` に閉じる
- 3B 側の連動移行を先取りしない

---

## Desired Landing

この run の着地は、
3A 対象 5 ファイルが `src/apsf/legacy/` 側へ着地し、
最小 import 更新とテスト確認まで終わっている状態である。

同時に、
残る 3B が
`specialist_registry + planner/critic + cli + act_service`
の連動単位としてさらに明確になる状態を作る。
