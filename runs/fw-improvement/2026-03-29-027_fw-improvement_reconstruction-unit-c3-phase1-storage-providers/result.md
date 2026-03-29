# Result

---

## Status

Completed

---

## 実施内容

### 1. ファイル移動

| 元パス | 移行先 |
|---|---|
| `src/apsf/storage/markdown_repository.py` | `src/apsf/legacy/storage/markdown_repository.py` |
| `src/apsf/storage/run_repository.py` | `src/apsf/legacy/storage/run_repository.py` |
| `src/apsf/providers/anthropic_provider.py` | `src/apsf/legacy/providers/anthropic_provider.py` |
| `src/apsf/providers/openai_provider.py` | `src/apsf/legacy/providers/openai_provider.py` |
| `src/apsf/providers/gemini_provider.py` | `src/apsf/legacy/providers/gemini_provider.py` |

### 2. 新設

- `src/apsf/legacy/providers/__init__.py`

### 3. import 更新（plan で見積もった caller + 追加修正）

| ファイル | 変更内容 |
|---|---|
| `src/apsf/cli/main.py` | `..storage.run_repository` → `..legacy.storage.run_repository`（10 箇所） |
| `src/apsf/viewer/api.py` | `apsf.storage.run_repository` → `apsf.legacy.storage.run_repository` |
| `src/apsf/orchestration/assignment_service.py` | `..providers.X` → `..legacy.providers.X`（3 行） |
| `src/apsf/orchestration/act_service.py` | `..providers.X` → `..legacy.providers.X`（3 行、lazy） |
| `src/apsf/executors/api_executor.py` | `..providers.anthropic_provider` → `..legacy.providers.anthropic_provider`（lazy） |
| `src/apsf/providers/__init__.py` | `from .X_provider` → `from ..legacy.providers.X_provider`（3 行、既存 re-export 維持） |
| `src/apsf/legacy/providers/{anthropic,openai,gemini}_provider.py` | `from ..core.` → `from ...core.`（パス深度修正） |
| `tests/test_assignment_service.py` | `apsf.providers.anthropic_provider` → `apsf.legacy.providers.anthropic_provider` |
| `tests/test_run_repository.py` | `apsf.storage.*` → `apsf.legacy.storage.*` |
| `tests/test_markdown_repository.py` | 同上 |
| `tests/test_cli_start_run.py` | 同上 |
| `tests/test_existing_run_optional_files.py` | 同上 |
| `tests/test_optionalization_fresh_run.py` | 同上 |

### plan 想定との差分

- `src/apsf/providers/__init__.py` の既存 re-export を legacy.providers 向けに更新（plan に未記載だった追加修正）
- moved 側 provider ファイルのパス深度修正（`..core.` → `...core.`）が必要だった

---

## pytest 結果

```
390 passed, 2 failed
```

**2 件は pre-existing failure（今回の変更前から failing）**:

- `test_run_repository.py::test_validate_run_name[2026-03-15_sochi-blocks-False]`
- `test_run_repository.py::TestValidateChildRunName::test_validate_child_run_name[016c1_sochi-blocks-False]`

どちらも `validate_child_run_name` / `validate_run_name` のパターン問題で、
今回の Phase 1 移行による新規失敗はゼロである。

---

## Verification チェック

| # | 基準 | 結果 |
|---|---|---|
| 1 | `src/apsf/storage/` が `legacy/storage/` へ landing | ✅ |
| 2 | `src/apsf/providers/` が `legacy/providers/` へ landing | ✅ |
| 3 | `cli/main.py` の storage import 更新 | ✅ |
| 4 | `orchestration/assignment_service.py` の providers import 更新 | ✅ |
| 5 | `pytest -q` 結果が確認された | ✅（390 passed、新規失敗 0） |
| 6 | `agents/` / `cli/` / `act_service.py` を巻き込まずに終わる | ✅ |
| 7 | `pipeline.py` の観察メモが残る | ✅（後述） |

---

## pipeline.py 観察メモ

`src/apsf/orchestration/pipeline.py` の import 依存を確認した。

```python
from ..core.domain.models import Role, RunContext, StepResult, ExecutionType
from ..core.executors.base import BaseExecutor
from ..core.agents.base import BaseAgent
```

**CLI / storage / orchestration への依存がゼロ**。
参照しているのは `core/` だけである。

この特性から、`pipeline.py` は legacy 実装ではなく
**core/ の一部として読む方が自然**である。

- `core/` 側は「ABC + domain model」に留まっており、`Pipeline` は「ABCを組み合わせた実行骨格」
- ただし Pipeline は抽象ではなく具象クラスであり、`input()` 呼び出し（v0.1 実装）も含む

判断: **core/ 昇格候補だが、具象実装が含まれる点で確定しない**。
次フェーズの planning run で `src/apsf/core/` への昇格 vs `legacy/orchestration/` 残留を改めて判断する。

---

## 次の状態

- `src/apsf/legacy/storage/` に実装が landing ✅
- `src/apsf/legacy/providers/` に実装が landing ✅
- `src/apsf/storage/` と `src/apsf/providers/` は `__init__.py` のみ残存（空パッケージ）

Phase 2 の主語: `config/` + `prompts/` + `executors/` + 軽量 orchestration
