# Plan

---

## Goal Readiness Check

- `run-030` で Phase 3A は完了、pytest 390 passed で閉じている
- 残りは `specialist_registry` 依存の連動単位（planner / critic / act_service / cli 全体）に絞られている
- `pyproject.toml` の entry point は `apsf = "apsf.cli.main:app"` で確認済みである

Decision: Proceed

---

## 事前確認結果

### cli/main.py を import しているテスト（5 本）

```python
from apsf.cli.main import app  # test_cli_act, start_run, write_phase, existing_run, optionalization_fresh_run
```

移行後は `from apsf.legacy.cli.main import app` へ更新する。

### cli/__init__.py の __getattr__

```python
def __getattr__(name: str) -> Any:
    if name == "app":
        from .main import app  # ← .main がなくなるので更新が必要
        return app
```

→ `from ..legacy.cli.main import app` へ更新する。

### cli/main.py 内の非-legacy import（移動後に深度修正が必要）

- `from ..core.domain.models import ...`（line 567）
- `from ..core.providers.base import ...`（line 1264）
- `from ..viewer.api import app`（line 1598）
- `from ..orchestration.act_service import ActError, ActService`（lines 1261, 1393）

→ 移動後は `...core.*`、`...viewer.api` に深度修正。
→ `..orchestration.act_service` は act_service も同時に `legacy/orchestration/` へ移るので、移動後の `legacy/cli/main.py` から `..orchestration.act_service` は自然に `apsf.legacy.orchestration.act_service` を指す ✓

### act_service.py の既存壊れた lazy import

```python
from ..orchestration.assignment_service import AssignmentService  # Phase 3A で legacy へ移動済み
```

→ 移動後 `legacy/orchestration/act_service.py` からは `..assignment_service` で解決する（同一パッケージ内）。

---

## File-Level Plan

### Step 1. 7 ファイルを legacy/ へ移す

```
cli/specialist_registry.py   → legacy/cli/specialist_registry.py
cli/role_rules.py             → legacy/cli/role_rules.py
cli/io.py                     → legacy/cli/io.py
cli/main.py                   → legacy/cli/main.py
agents/planner.py             → legacy/agents/planner.py
agents/critic.py              → legacy/agents/critic.py
orchestration/act_service.py  → legacy/orchestration/act_service.py
```

### Step 2. 移動後ファイルの内部 import を修正する

**legacy/agents/planner.py**, **legacy/agents/critic.py**:

```python
# ..legacy.config.settings  → ..config.settings
# ..cli.specialist_registry  → ...cli.specialist_registry
# ..core.*                   → ...core.*
# ..legacy.prompts.renderer  → ..prompts.renderer
```

**legacy/orchestration/act_service.py**:

```python
# ..legacy.config.settings        → ..config.settings
# ..core.*                         → ...core.*
# ..cli.specialist_registry        → ...cli.specialist_registry
# ..legacy.orchestration.*         → ..orchestration.*
# ..legacy.prompts.renderer        → ..prompts.renderer
# ..legacy.providers.*             → ..providers.*
# ..orchestration.assignment_service → ..assignment_service  (同一 legacy/orchestration/ 内)
```

**legacy/cli/main.py**:

```python
# ..legacy.*  → ..*  (36 箇所、一括 sed)
# ..core.*    → ...core.*
# ..viewer.api → ...viewer.api
# .io / .role_rules / .specialist_registry → 変更なし（同一 legacy/cli/ 内）
# ..orchestration.act_service → 変更なし（移動後は legacy/ 内で自然に解決）
```

### Step 3. caller の import を更新する

| ファイル | 変更内容 |
|---|---|
| `src/apsf/agents/__init__.py` | `from .planner import PlannerAgent` → `from ..legacy.agents.planner import PlannerAgent`、`from .critic import CriticAgent` → `from ..legacy.agents.critic import CriticAgent` |
| `src/apsf/cli/__init__.py` | `__getattr__` 内の `from .main import app` → `from ..legacy.cli.main import app` |
| `tests/test_cli_act.py` | `from apsf.cli.main import app` → `from apsf.legacy.cli.main import app` |
| `tests/test_cli_start_run.py` | 同上 |
| `tests/test_cli_write_phase.py` | 同上 |
| `tests/test_existing_run_optional_files.py` | 同上 |
| `tests/test_optionalization_fresh_run.py` | 同上 |

### Step 4. pyproject.toml を更新する

```toml
[project.scripts]
apsf = "apsf.legacy.cli.main:app"
```

### Step 5. pytest -q を実行して確認する

---

## Scope Policy

### 含めるもの

- Step 1-5

### 含めないもの

- `pipeline.py` の移行・判断
- viewer の変更
- `src/apsf/orchestration/__init__.py` の act_service re-export（現状 export していない）

---

## Verification Policy

1. `legacy/cli/` に specialist_registry / role_rules / io / main が存在する
2. `legacy/agents/` に planner / critic が存在する
3. `legacy/orchestration/` に act_service が存在する
4. `pyproject.toml` entry point が `apsf.legacy.cli.main:app` になっている
5. pytest 結果が記録されている（新規失敗ゼロが目標）
6. `pipeline.py` を巻き込んでいない
