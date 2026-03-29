# Result

---

## Status

Completed

---

## Output — Phase 3 Migration Order

### Import Dependency 確認結果

| ファイル | cli/ 依存 |
|---|---|
| `agents/builder.py`, `judge.py`, `junior_builder.py` | **なし** |
| `orchestration/assignment_service.py` | **なし** |
| `orchestration/execution_assignment_service.py` | **なし** |
| `agents/planner.py`, `critic.py` | **あり**（`cli/specialist_registry`） |
| `orchestration/act_service.py` | **あり**（`cli/specialist_registry`） |
| `cli/specialist_registry.py`, `role_rules.py`, `io.py` | なし（stdlib のみ） |
| `cli/main.py` | 全モジュール lazy import、**entry point** |

---

## Phase 3A（最初の実装単位）

**対象**:

| 元パス | 移行先 |
|---|---|
| `agents/builder.py` | `legacy/agents/builder.py` |
| `agents/judge.py` | `legacy/agents/judge.py` |
| `agents/junior_builder.py` | `legacy/agents/junior_builder.py` |
| `orchestration/assignment_service.py` | `legacy/orchestration/assignment_service.py` |
| `orchestration/execution_assignment_service.py` | `legacy/orchestration/execution_assignment_service.py` |

**新設**: `src/apsf/legacy/agents/__init__.py`

**移動後の内部 import 修正**:

| ファイル | 修正内容 |
|---|---|
| `legacy/agents/{builder,judge,junior_builder}.py` | `..core.` → `...core.`、`..legacy.prompts.` → `..prompts.` |
| `legacy/orchestration/assignment_service.py` | `..core.` → `...core.`、`..legacy.config.` → `..config.`、`..legacy.providers.` → `..providers.` |
| `legacy/orchestration/execution_assignment_service.py` | `..core.` → `...core.`、`..legacy.config.` → `..config.`、`..legacy.executors.` → `..executors.` |

**caller 更新**:

| ファイル | 変更内容 |
|---|---|
| `src/apsf/agents/__init__.py` | builder / judge / junior_builder の re-export を legacy 向けに更新 |
| `src/apsf/orchestration/__init__.py` | `.assignment_service` / `.execution_assignment_service` → `..legacy.orchestration.*` |
| `src/apsf/cli/main.py` | lazy imports の assignment_service / execution_assignment_service → legacy |
| `tests/test_assignment_service.py` | `apsf.orchestration.assignment_service` → `apsf.legacy.orchestration.assignment_service` |
| `tests/test_execution_assignment_service.py` | 同上 |

concrete agents を直接 import するテストはゼロ（確認済み）。

---

## Phase 3B（第 2 実装単位）: 連動移行

**対象（同時移行）**:

- `cli/specialist_registry.py` → `legacy/cli/specialist_registry.py`
- `cli/role_rules.py` → `legacy/cli/role_rules.py`
- `cli/io.py` → `legacy/cli/io.py`
- `agents/planner.py` → `legacy/agents/planner.py`
- `agents/critic.py` → `legacy/agents/critic.py`
- `orchestration/act_service.py` → `legacy/orchestration/act_service.py`
- `cli/main.py` → `legacy/cli/main.py`

**specialist_registry を先行させず同時移行とする理由**:
specialist_registry は stdlib のみ（apsf 依存ゼロ）だが、
先行移行しても planner / critic / act_service はすぐ後に移動する。
intermediate state の旨みがなく、import 更新を 1 回で完結させる方が効率的。

**cli/main.py の特殊性**:
entry point として `pyproject.toml` の `[project.scripts]` に登録されている可能性がある。
実装 run で `apsf.cli.main:app` → `apsf.legacy.cli.main:app` の更新要否を確認する。

---

## pipeline.py 観察更新

- `core/` のみ参照（domain/models + executors/base + agents/base）
- CLI / storage / orchestration / config への依存ゼロ
- 具象クラス（`run_all` に `input()` 呼び出し）を含む
- Phase 3A / 3B が完了した後、legacy/orchestration/ の残り全体を見て判断する
- **今回も確定しない**

---

## Success Criteria 照合

| # | 基準 | 結果 |
|---|---|---|
| 1 | `specialist_registry.py` を先行させるか同時かが明示される | ✅ 3B で同時移行、理由つき |
| 2 | `agents/` の landing 単位が定義される | ✅ 3A（3 ファイル）+ 3B（2 ファイル）に分割 |
| 3 | `cli/` 本体の landing 単位が定義される | ✅ 3B で全体を同時移行 |
| 4 | 重め orchestration の移行順序に理由がある | ✅ cli/ 依存有無で 3A / 3B に分割 |
| 5 | `pipeline.py` の観察更新が残る | ✅ Phase 3B 完了後に判断を委ねる |
| 6 | 次の Codex 実装 run の主語が切れる | ✅ Phase 3A が明確な 1 単位として定義済み |

---

## Next Trigger

**Phase 3A 実装 run（Codex）**

```
対象:
  agents/builder.py, judge.py, junior_builder.py → legacy/agents/
  orchestration/assignment_service.py, execution_assignment_service.py → legacy/orchestration/
作業:
  1. src/apsf/legacy/agents/__init__.py を新設
  2. 5 ファイルを legacy/ 側へ移動
  3. 移動後の内部 import 深度修正
  4. caller 更新（agents/__init__, orchestration/__init__, cli/main.py, tests/ 2 ファイル）
  5. pytest -q
```

**Phase 3B 実装 run**（3A 完了後）:
- specialist_registry + planner/critic + act_service + cli/ 全体の連動移行
- pyproject.toml entry point 確認

**pipeline.py 判断**（3B 完了後）
