# Goal

Run: 2026-03-29-031_fw-improvement_reconstruction-unit-c3-phase3b-specialist-cli
Date: 2026-03-29

---

## Goal Readiness Check

- `run-029` で Phase 3 は `3A / 3B` に分割済みである
- `run-030` で 3A は完了し、`390 passed` で閉じている
- 残る主要実装群は `specialist_registry` を起点とする `planner / critic / act_service / cli` に絞られている
- `src/apsf/legacy/` はすでに受け皿として存在している
- 今回は Codex 実装 run であり、Phase 3B の連動移行を行う

Decision: Proceed

---

## Objective

APSF 再構築の Unit C3 Phase 3B として、
`cli/specialist_registry.py` を起点に、
`planner.py`、`critic.py`、`act_service.py`、
`cli/role_rules.py`、`cli/io.py`、`cli/main.py`
の連動移行を行う。

今回の run では、
3B を 1 つの依存まとまりとして扱い、
必要最小限の import 更新と
entry point 確認まで含めて閉じる。

---

## Scope

この run で扱うのは次だけである。

1. `cli/specialist_registry.py` の legacy landing
2. `agents/planner.py` の legacy landing
3. `agents/critic.py` の legacy landing
4. `orchestration/act_service.py` の legacy landing
5. `cli/role_rules.py` の legacy landing
6. `cli/io.py` の legacy landing
7. `cli/main.py` の連動更新
8. `pyproject.toml` の entry point 確認
9. `pytest -q` による確認

---

## Constraints

### 含めるもの

- `src/apsf/cli/specialist_registry.py`
- `src/apsf/agents/planner.py`
- `src/apsf/agents/critic.py`
- `src/apsf/orchestration/act_service.py`
- `src/apsf/cli/role_rules.py`
- `src/apsf/cli/io.py`
- `src/apsf/cli/main.py`
- caller / import 更新
- `pyproject.toml` の確認
- `pytest -q`

### 含めないもの

- `pipeline.py` の placement 確定
- viewer の再配置
- 追加の新規分割
- reconstruction 全体完了の宣言

### 判断上の制約

- 3B は `specialist_registry` 依存のまとまりに閉じる
- `cli/main.py` は entry point として慎重に扱う
- `pyproject.toml` は必要なら更新するが、今回の主語を超える再設計はしない
- `pipeline.py` は今回も移行対象ではない

---

## Success Criteria

1. 3B 対象ファイル群が `src/apsf/legacy/` 側へ landing する
2. `specialist_registry` 起点の依存が legacy 側で整合する
3. `cli/main.py` の entry point 整合が保たれる
4. `pyproject.toml` の確認または必要最小限更新が行われる
5. `pytest -q` の結果が確認される
6. `pipeline.py` を巻き込まずに終わる

---

## Verification

- landing 後のディレクトリ構造が存在する
- 主要 import 更新が反映されている
- CLI entry point が壊れていない
- `pytest -q` の結果が記録されている

---

## Non-Goals

- `pipeline.py` の最終判断
- viewer の再配置
- reconstruction 全体完了

---

## Inputs to Respect

- `runs/fw-improvement/2026-03-29-029_fw-improvement_reconstruction-unit-c3-phase3-agents-cli-heavy-orchestration-planning/result.md`
- `runs/fw-improvement/2026-03-29-030_fw-improvement_reconstruction-unit-c3-phase3a-agents-assignment/result.md`
- `src/apsf/core/`
- `src/apsf/legacy/`

特に次を守ること。

- 3B は `specialist_registry + planner/critic + act_service + cli`
  の連動単位である
- 3A 完了を前提に、その残りだけを処理する
- `pipeline.py` は今回判断を閉じない

---

## Desired Landing

この run の着地は、
Phase 3B の残り実装群が `src/apsf/legacy/` 側へ着地し、
CLI entry point と主要 import が整合した状態で
`pytest -q` まで通っていることである。

これにより、
C3 の主要 Python legacy 移行が一通り完了し、
残る論点を `pipeline.py` などの保留資産に狭く戻せる状態を作る。
