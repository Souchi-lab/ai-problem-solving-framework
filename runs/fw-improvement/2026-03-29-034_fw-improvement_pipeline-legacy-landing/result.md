# Result

---

## Status

Completed

---

## 実施内容

### 移動したファイル

| 元パス | 移行先 |
|---|---|
| `src/apsf/orchestration/pipeline.py` | `src/apsf/legacy/orchestration/pipeline.py` |

### 移動後の内部 import 修正

```python
# before
from ..core.domain.models import Role, RunContext, StepResult, ExecutionType
from ..core.executors.base import BaseExecutor
from ..core.agents.base import BaseAgent

# after
from ...core.domain.models import Role, RunContext, StepResult, ExecutionType
from ...core.executors.base import BaseExecutor
from ...core.agents.base import BaseAgent
```

### caller 更新

| ファイル | 変更内容 |
|---|---|
| `src/apsf/orchestration/__init__.py` | `from .pipeline import Pipeline` → `from ..legacy.orchestration.pipeline import Pipeline` |

---

## pytest 結果

```
390 passed, 2 failed
```

**2 件は pre-existing failure（変化なし）**。今回の移動による新規失敗はゼロ。

---

## Verification チェック

| # | 基準 | 結果 |
|---|---|---|
| 1 | `legacy/orchestration/pipeline.py` が存在する | ✅ |
| 2 | 元の `orchestration/pipeline.py` が存在しない | ✅ |
| 3 | `orchestration/__init__.py` が legacy 向けに更新されている | ✅ |
| 4 | pytest 結果が記録されている（新規失敗ゼロ） | ✅ |

---

## 残件

reconstruction 後の残件は **1 本** になった。

| 項目 | 状態 |
|---|---|
| `framework/planning-patterns.md` 精読 | 未実施（次 run） |
