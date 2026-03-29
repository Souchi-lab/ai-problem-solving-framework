# Result

---

## Status

Completed

---

## 実施内容

### 移動したファイル

| 元パス | 移行先 |
|---|---|
| `src/apsf/agents/builder.py` | `src/apsf/legacy/agents/builder.py` |
| `src/apsf/agents/judge.py` | `src/apsf/legacy/agents/judge.py` |
| `src/apsf/agents/junior_builder.py` | `src/apsf/legacy/agents/junior_builder.py` |
| `src/apsf/orchestration/assignment_service.py` | `src/apsf/legacy/orchestration/assignment_service.py` |
| `src/apsf/orchestration/execution_assignment_service.py` | `src/apsf/legacy/orchestration/execution_assignment_service.py` |

### 新設

- `src/apsf/legacy/agents/__init__.py`

### 移動後の内部 import 修正

| ファイル | 修正内容 |
|---|---|
| `legacy/agents/{builder,judge,junior_builder}.py` | `..core.` → `...core.`、`..legacy.prompts.` → `..prompts.` |
| `legacy/orchestration/assignment_service.py` | `..core.` → `...core.`、`..legacy.config.` → `..config.`、`..legacy.providers.` → `..providers.` |
| `legacy/orchestration/execution_assignment_service.py` | `..core.` → `...core.`、`..legacy.config.` → `..config.`、`..legacy.executors.` → `..executors.` |

### caller 更新

| ファイル | 変更内容 |
|---|---|
| `src/apsf/agents/__init__.py` | builder / judge / junior_builder の re-export を legacy 向けに更新（planner / critic はそのまま） |
| `src/apsf/orchestration/__init__.py` | assignment_service / execution_assignment_service を legacy 向けに更新 |
| `src/apsf/cli/main.py` | lazy `execution_assignment_service` import 2 箇所を legacy 向けに更新 |
| `tests/test_assignment_service.py` | `apsf.orchestration.assignment_service` → `apsf.legacy.orchestration.assignment_service` |
| `tests/test_execution_assignment_service.py` | `apsf.orchestration.execution_assignment_service` → 同様 |

---

## pytest 結果

```
390 passed, 2 failed
```

**2 件は pre-existing failure（変化なし）**。今回の Phase 3A 移行による新規失敗はゼロ。

---

## Verification チェック

| # | 基準 | 結果 |
|---|---|---|
| 1 | `legacy/agents/` に builder / judge / junior_builder が存在する | ✅ |
| 2 | `legacy/orchestration/` に assignment_service / execution_assignment_service が存在する | ✅ |
| 3 | 元の 5 ファイルが存在しない | ✅ |
| 4 | pytest 確認（新規失敗ゼロ） | ✅ |
| 5 | planner / critic / specialist_registry / cli / act_service を巻き込まなかった | ✅ |

---

## 現在の残り（Phase 3B）

Phase 3A 完了により、残る移行対象が以下に絞られた。

| ファイル | 理由 |
|---|---|
| `agents/planner.py` | `cli/specialist_registry` 依存あり |
| `agents/critic.py` | 同上 |
| `orchestration/act_service.py` | 同上 |
| `cli/specialist_registry.py` | 連動の起点（apsf 依存ゼロ） |
| `cli/role_rules.py` | cli/ 本体 |
| `cli/io.py` | cli/ 本体 |
| `cli/main.py` | entry point、pyproject.toml 確認要 |
| `orchestration/pipeline.py` | placement 保留継続 |
