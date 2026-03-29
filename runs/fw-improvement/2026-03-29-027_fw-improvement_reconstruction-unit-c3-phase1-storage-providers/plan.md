# Plan

---

## Goal Readiness Check

- `run-026` で Phase 1 は `storage/ + providers/` と確定済みである
- `src/apsf/legacy/storage/` と `src/apsf/legacy/cli/` skeleton は run-024 で着地済みである
- `src/apsf/legacy/providers/` は skeleton になく、今回新設する
- import caller の全量を実コードで確認した（後述）

Decision: Proceed

---

## Problem Structure

今回は storage/ と providers/ の実ファイルを legacy/ 側へ移し、
呼び出し元の import を更新して pytest を通す。

run-026 の想定より caller が多かった。
事前確認で追加判明した caller を含めて、今回の更新リストを確定する。

---

## Caller の全量（事前確認済み）

### storage/ の caller

| ファイル | import 種別 | 変更パターン |
|---|---|---|
| `src/apsf/cli/main.py` | lazy（関数内） | `..storage.run_repository` → `..legacy.storage.run_repository` |
| `src/apsf/viewer/api.py` | top-level | `apsf.storage.run_repository` → `apsf.legacy.storage.run_repository` |
| `tests/test_run_repository.py` | top-level | `apsf.storage.run_repository` → `apsf.legacy.storage.run_repository` |
| `tests/test_markdown_repository.py` | top-level | `apsf.storage.markdown_repository` → `apsf.legacy.storage.markdown_repository` |
| `tests/test_cli_start_run.py` | top-level | `apsf.storage.run_repository` → `apsf.legacy.storage.run_repository` |
| `tests/test_existing_run_optional_files.py` | top-level | `apsf.storage.run_repository` → `apsf.legacy.storage.run_repository` |
| `tests/test_optionalization_fresh_run.py` | top-level | `apsf.storage.run_repository` → `apsf.legacy.storage.run_repository` |

### providers/ の caller

| ファイル | import 種別 | 変更パターン |
|---|---|---|
| `src/apsf/orchestration/assignment_service.py` | top-level（L18-20） | `..providers.X` → `..legacy.providers.X` |
| `src/apsf/orchestration/act_service.py` | lazy（関数内） | `..providers.X` → `..legacy.providers.X` |
| `src/apsf/executors/api_executor.py` | lazy（関数内） | `..providers.anthropic_provider` → `..legacy.providers.anthropic_provider` |

---

## Selected Approach

### ファイル移動方針

- `src/apsf/storage/` の実装ファイルを `src/apsf/legacy/storage/` へ移す
- `src/apsf/providers/` の実装ファイルを `src/apsf/legacy/providers/` へ移す
- 元の `src/apsf/storage/` ディレクトリは `__init__.py` だけ残す（空パッケージとして維持）
- 元の `src/apsf/providers/` ディレクトリは `__init__.py` だけ残す（同上）
- Python 側は re-export スタブを使わない（run-023 方針）

### __init__.py の整理

既存の `src/apsf/legacy/storage/__init__.py` は skeleton コメントが入っている。
ファイル移動後、そのコメントを削除して実 import を許容する空 `__init__.py` に置き換える。

`src/apsf/legacy/providers/__init__.py` は今回新設する（空でよい）。

---

## File-Level Plan

### Step 1. `src/apsf/legacy/providers/` を新設する

```
src/apsf/legacy/providers/__init__.py   ← 新規（空）
```

### Step 2. storage/ の実装ファイルを legacy/storage/ へ移す

```
src/apsf/storage/markdown_repository.py  → src/apsf/legacy/storage/markdown_repository.py
src/apsf/storage/run_repository.py       → src/apsf/legacy/storage/run_repository.py
```

移動後:
- `src/apsf/legacy/storage/__init__.py` を skeleton コメントなしの空ファイルに置き換える
- `src/apsf/storage/__init__.py` はそのまま残す（空パッケージとして）

### Step 3. providers/ の実装ファイルを legacy/providers/ へ移す

```
src/apsf/providers/anthropic_provider.py  → src/apsf/legacy/providers/anthropic_provider.py
src/apsf/providers/openai_provider.py     → src/apsf/legacy/providers/openai_provider.py
src/apsf/providers/gemini_provider.py     → src/apsf/legacy/providers/gemini_provider.py
```

移動後:
- `src/apsf/providers/__init__.py` はそのまま残す（空パッケージとして）

### Step 4. import を更新する

**src/apsf/cli/main.py**（lazy import、関数内に複数箇所）:

```python
# before
from ..storage.run_repository import RunRepository
# after
from ..legacy.storage.run_repository import RunRepository
```

**src/apsf/viewer/api.py**（top-level import）:

```python
# before
from apsf.storage.run_repository import RunRepository
# after
from apsf.legacy.storage.run_repository import RunRepository
```

**src/apsf/orchestration/assignment_service.py**（top-level import、L18-20）:

```python
# before
from ..providers.anthropic_provider import AnthropicProvider
from ..providers.gemini_provider import GeminiProvider
from ..providers.openai_provider import OpenAIProvider
# after
from ..legacy.providers.anthropic_provider import AnthropicProvider
from ..legacy.providers.gemini_provider import GeminiProvider
from ..legacy.providers.openai_provider import OpenAIProvider
```

**src/apsf/orchestration/act_service.py**（lazy import、関数内）:

```python
# before
from ..providers.anthropic_provider import AnthropicProvider
from ..providers.gemini_provider import GeminiProvider
from ..providers.openai_provider import OpenAIProvider
# after
from ..legacy.providers.anthropic_provider import AnthropicProvider
from ..legacy.providers.gemini_provider import GeminiProvider
from ..legacy.providers.openai_provider import OpenAIProvider
```

**src/apsf/executors/api_executor.py**（lazy import、関数内）:

```python
# before
from ..providers.anthropic_provider import AnthropicProvider
# after
from ..legacy.providers.anthropic_provider import AnthropicProvider
```

**tests/ 5 ファイル**（top-level import）:

```python
# before
from apsf.storage.run_repository import RunRepository
from apsf.storage.run_repository import RunRepository, STANDARD_FILES
from apsf.storage.markdown_repository import MarkdownRepository
# after（それぞれ）
from apsf.legacy.storage.run_repository import RunRepository
from apsf.legacy.storage.run_repository import RunRepository, STANDARD_FILES
from apsf.legacy.storage.markdown_repository import MarkdownRepository
```

対象ファイル:
- `tests/test_run_repository.py`
- `tests/test_markdown_repository.py`
- `tests/test_cli_start_run.py`
- `tests/test_existing_run_optional_files.py`
- `tests/test_optionalization_fresh_run.py`

### Step 5. pytest -q を実行して確認する

```bash
pytest -q tests/
```

結果を result.md に記録する。

---

## Scope Policy

### 含めるもの

- `src/apsf/storage/` の実装 2 ファイルの移動
- `src/apsf/providers/` の実装 3 ファイルの移動
- `src/apsf/legacy/providers/__init__.py` の新設
- 上記 Caller の全量 import 更新
- `src/apsf/legacy/storage/__init__.py` の skeleton コメント除去

### 含めないもの

- `agents/` / `cli/` / `act_service.py` の移動
- `pipeline.py` の移動
- `config/` / `prompts/` / `executors/` の移動
- viewer の変更（ただし viewer/api.py の import 更新は含む）

---

## Verification Policy

1. `src/apsf/legacy/storage/` に 2 ファイルが存在する
2. `src/apsf/legacy/providers/` に 3 ファイルが存在する
3. `src/apsf/storage/` と `src/apsf/providers/` に実装ファイルがなく `__init__.py` だけ残る
4. `pytest -q` の結果が確認される（pass / 残存エラーの両方を記録する）
5. `agents/` / `cli/` を巻き込んでいない

---

## pipeline.py 観察メモ方針

`result.md` に次を記録する。

- `pipeline.py` が参照しているのは `core/` のみであること（`core/domain/models`, `core/executors/base`, `core/agents/base`）
- CLI / orchestration / storage への依存がゼロであること
- この特性から core/ 昇格 vs legacy 残留のどちらが自然かを 1 段落で記録する
- 今回は placement を確定しない

---

## Deliverables

- `src/apsf/legacy/storage/markdown_repository.py`
- `src/apsf/legacy/storage/run_repository.py`
- `src/apsf/legacy/providers/__init__.py`
- `src/apsf/legacy/providers/anthropic_provider.py`
- `src/apsf/legacy/providers/openai_provider.py`
- `src/apsf/legacy/providers/gemini_provider.py`
- 上記 Caller の import 更新（7 ファイル）
- `pytest -q` 結果の記録
- `pipeline.py` 観察メモ
- `result.md`
