# Plan

---

## Goal Readiness Check

- Phase 1 / Phase 2 で storage / providers / config / prompts / executors / 軽量 orchestration は landing 済みである
- 残りは `agents/`、`cli/` 本体、重め orchestration に絞られている
- 今回は planning-only run であり、実装移行や import 修正は行わない

Decision: Proceed

---

## Problem Structure

Phase 3 の残りは一見「重い塊」に見えるが、
実コードを読むと **cli/ 依存の有無** で 2 つの層に分かれる。

- **cli/ 依存なし**: 独立して先に移せる
- **cli/ 依存あり**: specialist_registry と連動させる必要がある

これを前提に、Phase 3 を **3A / 3B の 2 バッチ** に分ける。

---

## Import Dependency 再確認

### agents/ の cli/ 依存状況

| ファイル | cli/ 依存 | 依存先 |
|---|---|---|
| `agents/builder.py` | **なし** | core/ + legacy.prompts |
| `agents/judge.py` | **なし** | core/ + legacy.prompts |
| `agents/junior_builder.py` | **なし** | core/ + legacy.prompts |
| `agents/planner.py` | **あり** | `cli/specialist_registry` + core/ + legacy.* |
| `agents/critic.py` | **あり** | `cli/specialist_registry` + core/ + legacy.* |

### 重め orchestration の cli/ 依存状況

| ファイル | cli/ 依存 | 依存先 |
|---|---|---|
| `orchestration/assignment_service.py` | **なし** | core/ + legacy.config + legacy.providers |
| `orchestration/execution_assignment_service.py` | **なし** | core/ + legacy.config + legacy.executors |
| `orchestration/act_service.py` | **あり** | `cli/specialist_registry` + core/ + legacy.* |

### cli/ 内部の依存状況

| ファイル | apsf 依存 |
|---|---|
| `cli/specialist_registry.py` | **なし**（stdlib のみ） |
| `cli/role_rules.py` | なし（stdlib のみ） |
| `cli/io.py` | なし（stdlib のみ） |
| `cli/main.py` | 全モジュール（lazy import）、entry point |

---

## Phase 3 の 2 バッチ構成

### Phase 3A（最初の実装単位）: cli/ 依存なし群

**移行対象**:

- `agents/builder.py` → `legacy/agents/builder.py`
- `agents/judge.py` → `legacy/agents/judge.py`
- `agents/junior_builder.py` → `legacy/agents/junior_builder.py`
- `orchestration/assignment_service.py` → `legacy/orchestration/assignment_service.py`
- `orchestration/execution_assignment_service.py` → `legacy/orchestration/execution_assignment_service.py`

**新設**:

- `src/apsf/legacy/agents/__init__.py`

**移行後の内部 import 修正**（legacy/ 内に入ることでパスが変わる）:

| ファイル | 修正内容 |
|---|---|
| `legacy/agents/builder.py` | `..core.` → `...core.`、`..legacy.prompts.` → `..prompts.` |
| `legacy/agents/judge.py` | 同上 |
| `legacy/agents/junior_builder.py` | 同上 |
| `legacy/orchestration/assignment_service.py` | `..core.` → `...core.`、`..legacy.config.` → `..config.`、`..legacy.providers.` → `..providers.` |
| `legacy/orchestration/execution_assignment_service.py` | `..core.` → `...core.`、`..legacy.config.` → `..config.`、`..legacy.executors.` → `..executors.` |

**import 更新が必要な caller**:

| ファイル | 変更内容 |
|---|---|
| `src/apsf/agents/__init__.py` | builder / judge / junior_builder の re-export を legacy 向けに更新（planner / critic はまだ元のまま） |
| `src/apsf/orchestration/__init__.py` | `from .assignment_service` → `from ..legacy.orchestration.assignment_service`、`from .execution_assignment_service` → 同様 |
| `src/apsf/cli/main.py` | lazy `from ..orchestration.assignment_service` → `from ..legacy.orchestration.assignment_service`（および execution_assignment_service） |
| `tests/test_assignment_service.py` | `from apsf.orchestration.assignment_service` → `from apsf.legacy.orchestration.assignment_service` |
| `tests/test_execution_assignment_service.py` | `from apsf.orchestration.execution_assignment_service` → 同様 |

**agents/ の concrete impl を直接 import しているテストはゼロ**（確認済み）。

**理由**:
cli/ 依存がなく、すでに Phase 1/2 で landing 済みの legacy.* を参照するだけ。
この単位は安全に独立して着手できる。

---

### Phase 3B（第 2 実装単位）: cli/ 依存あり群の連動移行

**移行対象**:

- `cli/specialist_registry.py` → `legacy/cli/specialist_registry.py`
- `cli/role_rules.py` → `legacy/cli/role_rules.py`
- `cli/io.py` → `legacy/cli/io.py`
- `agents/planner.py` → `legacy/agents/planner.py`
- `agents/critic.py` → `legacy/agents/critic.py`
- `orchestration/act_service.py` → `legacy/orchestration/act_service.py`
- `cli/main.py` → `legacy/cli/main.py`

**移行後の内部 import 修正**:

| ファイル | 修正内容 |
|---|---|
| `legacy/agents/planner.py` | `..core.` → `...core.`、`..cli.specialist_registry` → `..cli.specialist_registry`（同一 legacy/ 内なので depth 維持）、`..legacy.config.` → `..config.`、`..legacy.prompts.` → `..prompts.` |
| `legacy/agents/critic.py` | 同上 |
| `legacy/orchestration/act_service.py` | `..core.` → `...core.`、`..cli.specialist_registry` → `...cli.specialist_registry`、`..legacy.*` → `...*`（legacy 内相対） |
| `legacy/cli/main.py` | 全 lazy import を legacy 内相対に更新 |

**cli/main.py の特殊性**:

`cli/main.py` は pyproject.toml に entry point として登録されている可能性がある。
移行後は `pyproject.toml` の `[project.scripts]` を確認し、
`apsf.cli.main:app` → `apsf.legacy.cli.main:app` へ更新が必要な場合がある。

**import 更新が必要な caller（3B 完了時）**:

- `src/apsf/agents/__init__.py`: planner / critic の re-export を legacy 向けに更新
- `src/apsf/orchestration/__init__.py`: act_service（Pipeline 以外の残り）
- `cli/main.py` 自体が移動するため、移動後は legacy 内で自完結する

---

## specialist_registry を先行させるか同時か

**判断: 3B で同時移行**

理由:
- `specialist_registry.py` は stdlib のみ（apsf 依存ゼロ）
- 先行させても callers（planner / critic / act_service）はすぐ後に移動する
- 先行移行してもその間に intermediate state の旨みがない
- 同時移行する方が import 更新の往復が 1 回で済む

---

## pipeline.py 観察更新

**Phase 1 からの観察累積**:

- `pipeline.py` は `core/` のみ参照（domain/models + executors/base + agents/base）
- CLI / storage / orchestration / config への依存がゼロ
- 具象クラス（`run_all` に `input()` 呼び出し）を含む

**Phase 3 を経ての読み**:

Phase 3A / 3B が完了すると、`legacy/orchestration/` に act_service / assignment_service などが着地する。
`pipeline.py` はそれらを参照せず、core/ だけで完結している。

→ `legacy/orchestration/pipeline.py` として残す選択肢と、`core/pipeline.py` として昇格させる選択肢が並存する。
→ Phase 3B 完了後に単独で判断する。今回は確定しない。

---

## Migration Order Summary

```
Phase 3A: builder / judge / junior_builder + assignment_service + execution_assignment_service
Phase 3B: specialist_registry + planner / critic + act_service + cli/ 全体（同時）
[別途] pipeline.py: core vs legacy 判断（Phase 3B 完了後）
```

---

## 次の実装 run の主語

**Phase 3A 実装 run（Codex）**

```
対象:
  agents/builder.py, judge.py, junior_builder.py → legacy/agents/
  orchestration/assignment_service.py, execution_assignment_service.py → legacy/orchestration/
作業:
  1. src/apsf/legacy/agents/__init__.py を新設
  2. 5 ファイルを legacy/ 側へ移動
  3. 移動後の内部 import 深度修正（..core. → ...core. 等）
  4. caller 更新（agents/__init__, orchestration/__init__, cli/main.py, tests/ 2 ファイル）
  5. pytest -q
```

---

## Scope Policy

### 今回の planning run で確定したもの

- Phase 3A / 3B の 2 バッチ構成と理由
- 3A の対象ファイル・caller・import 修正方針
- specialist_registry を同時移行とする判断
- cli/main.py の entry point 特殊性を注意点として明示
- pipeline.py の判断を Phase 3B 完了後に委ねる方針

### 今回確定していないもの

- Phase 3B の詳細 caller リスト（3A 完了後に改めて確認）
- pipeline.py の core vs legacy 最終判定
- pyproject.toml の entry point 更新要否の確認
