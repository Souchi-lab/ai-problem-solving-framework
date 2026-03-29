# Plan

---

## Goal Readiness Check

- `pipeline.py` は run-032 で legacy 判定確定済み
- `src/apsf/legacy/orchestration/` は Phase 3B で他の orchestration ファイルが着地済み
- caller の全量確認済み（下記）

Decision: Proceed

---

## 事前確認結果

### pipeline.py の内部 import

```python
from ..core.domain.models import Role, RunContext, StepResult, ExecutionType
from ..core.executors.base import BaseExecutor
from ..core.agents.base import BaseAgent
```

`..core.*`（2点）→ 移動後は `...core.*`（3点）に修正。Phase 1〜3B と同じパターン。

### caller（全量）

| ファイル | 内容 |
|---|---|
| `src/apsf/orchestration/__init__.py` | `from .pipeline import Pipeline`（1行） |

`legacy/cli/main.py` 内の "pipeline" はコメント・docstring のみ。import なし。
テストファイルに Pipeline の直接 import なし。

---

## File-Level Plan

### Step 1. pipeline.py を legacy/ へ移す

```
src/apsf/orchestration/pipeline.py → src/apsf/legacy/orchestration/pipeline.py
```

### Step 2. 移動後の内部 import を修正する

```python
# before（src/apsf/orchestration/ にいた時）
from ..core.domain.models import ...
from ..core.executors.base import ...
from ..core.agents.base import ...

# after（src/apsf/legacy/orchestration/ に移ったので 1 段深くなる）
from ...core.domain.models import ...
from ...core.executors.base import ...
from ...core.agents.base import ...
```

### Step 3. caller の import を更新する

**src/apsf/orchestration/__init__.py**:

```python
# before
from .pipeline import Pipeline

# after
from ..legacy.orchestration.pipeline import Pipeline
```

### Step 4. pytest -q を実行して確認する

---

## Scope Policy

### 含めるもの

- Step 1-4

### 含めないもの

- `planning-patterns.md` の判定
- viewer の変更
- 他の orchestration ファイルへの変更

---

## Verification Policy

1. `legacy/orchestration/pipeline.py` が存在する
2. 元の `orchestration/pipeline.py` が存在しない
3. `orchestration/__init__.py` が legacy 向けに更新されている
4. pytest 結果が記録されている（新規失敗ゼロが目標）
