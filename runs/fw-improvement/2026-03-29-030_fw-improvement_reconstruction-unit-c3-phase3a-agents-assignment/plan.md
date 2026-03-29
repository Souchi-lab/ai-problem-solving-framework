# Plan

---

## Goal Readiness Check

- `run-029` で Phase 3A は `builder/judge/junior_builder + assignment_service/execution_assignment_service` として定義済みである
- 対象 5 ファイルはいずれも `cli/specialist_registry` 依存がない（確認済み）
- `src/apsf/legacy/` に skeleton と Phase 1/2 の landing が存在する
- 今回は Codex 実装 run である

Decision: Proceed

---

## Caller の全量（事前確認済み）

### agents/builder / judge / junior_builder の caller

concrete agents を直接 import するテストはゼロ（Phase 3 planning で確認済み）。

`src/apsf/agents/__init__.py` が re-export している：

```python
from .junior_builder import JuniorBuilderAgent   # → 更新
from .builder import BuilderAgent                 # → 更新
from .judge import JudgeAgent                     # → 更新
from .planner import PlannerAgent                 # → そのまま（3B）
from .critic import CriticAgent                   # → そのまま（3B）
```

### orchestration/assignment_service / execution_assignment_service の caller

| ファイル | 変更パターン |
|---|---|
| `src/apsf/orchestration/__init__.py` | `from .assignment_service` → `from ..legacy.orchestration.assignment_service`、`from .execution_assignment_service` → 同様 |
| `src/apsf/cli/main.py` | lazy `from ..orchestration.execution_assignment_service import ExecutionAssignmentService`（2 箇所）→ `from ..legacy.orchestration.execution_assignment_service import` |
| `tests/test_assignment_service.py` | `from apsf.orchestration.assignment_service import` → `from apsf.legacy.orchestration.assignment_service import` |
| `tests/test_execution_assignment_service.py` | `from apsf.orchestration.execution_assignment_service import` → `from apsf.legacy.orchestration.execution_assignment_service import` |

`assignment_service` を直接 lazy import している箇所は `cli/main.py` にない（`act_service.py` 経由のみ）。

---

## File-Level Plan

### Step 1. `src/apsf/legacy/agents/__init__.py` を新設する

```python
# src/apsf/legacy/agents
```

### Step 2. 5 ファイルを legacy/ へ移す

```
agents/builder.py       → legacy/agents/builder.py
agents/judge.py         → legacy/agents/judge.py
agents/junior_builder.py → legacy/agents/junior_builder.py
orchestration/assignment_service.py         → legacy/orchestration/assignment_service.py
orchestration/execution_assignment_service.py → legacy/orchestration/execution_assignment_service.py
```

### Step 3. 移動後ファイルの内部 import を修正する

**legacy/agents/{builder,judge,junior_builder}.py**:

```python
# before（src/apsf/agents/ にいた時）
from ..core.domain.models import ...
from ..core.executors.base import ...
from ..core.agents.base import ...
from ..legacy.prompts.renderer import ...
# after（src/apsf/legacy/agents/ に移ったので 1 段深くなる）
from ...core.domain.models import ...
from ...core.executors.base import ...
from ...core.agents.base import ...
from ..prompts.renderer import ...          # ..legacy.prompts → legacy/ 内相対
```

**legacy/orchestration/assignment_service.py**:

```python
# before
from ..legacy.config.settings import Settings
from ..core.domain.models import ...
from ..core.providers.base import BaseProvider
from ..legacy.providers.anthropic_provider import AnthropicProvider
from ..legacy.providers.gemini_provider import GeminiProvider
from ..legacy.providers.openai_provider import OpenAIProvider
# after（legacy/orchestration/ に移ったので）
from ..config.settings import Settings          # ..legacy.config → ..config
from ...core.domain.models import ...           # ..core → ...core
from ...core.providers.base import BaseProvider # 同上
from ..providers.anthropic_provider import AnthropicProvider  # ..legacy.providers → ..providers
from ..providers.gemini_provider import GeminiProvider
from ..providers.openai_provider import OpenAIProvider
```

**legacy/orchestration/execution_assignment_service.py**:

```python
# before
from ..legacy.config.settings import Settings
from ..core.domain.models import ...
from ..core.executors.base import BaseExecutor
from ..legacy.executors.cli_executor import CLIExecutor
from ..legacy.executors.human_executor import HumanExecutor
from ..legacy.executors.api_executor import APIExecutor
# after
from ..config.settings import Settings          # ..legacy.config → ..config
from ...core.domain.models import ...           # ..core → ...core
from ...core.executors.base import BaseExecutor # 同上
from ..executors.cli_executor import CLIExecutor  # ..legacy.executors → ..executors
from ..executors.human_executor import HumanExecutor
from ..executors.api_executor import APIExecutor
```

### Step 4. caller の import を更新する

**src/apsf/agents/__init__.py**（3 行更新、planner / critic はそのまま）:

```python
from ..legacy.agents.junior_builder import JuniorBuilderAgent
from ..legacy.agents.builder import BuilderAgent
from ..legacy.agents.judge import JudgeAgent
```

**src/apsf/orchestration/__init__.py**（2 行更新）:

```python
from ..legacy.orchestration.assignment_service import AssignmentService
from ..legacy.orchestration.execution_assignment_service import ExecutionAssignmentService
```

**src/apsf/cli/main.py**（2 箇所 lazy import 更新）:

```python
from ..legacy.orchestration.execution_assignment_service import ExecutionAssignmentService
```

**tests/test_assignment_service.py**, **tests/test_execution_assignment_service.py**:

```python
from apsf.legacy.orchestration.assignment_service import ...
from apsf.legacy.orchestration.execution_assignment_service import ...
```

### Step 5. pytest -q を実行して確認する

---

## Scope Policy

### 含めるもの

- Step 1-5

### 含めないもの

- `agents/planner.py`, `agents/critic.py`
- `cli/specialist_registry.py`, `cli/` 本体
- `orchestration/act_service.py`
- `pipeline.py`

---

## Verification Policy

1. `legacy/agents/` に builder / judge / junior_builder が存在する
2. `legacy/orchestration/` に assignment_service / execution_assignment_service が存在する
3. 元の `agents/` と `orchestration/` に移動した 5 ファイルが存在しない
4. pytest 結果が記録されている（新規失敗ゼロが目標）
5. planner / critic / specialist_registry / cli / act_service を巻き込んでいない
