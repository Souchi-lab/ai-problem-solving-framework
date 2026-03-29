# Plan

---

## Goal Readiness Check

- `run-027` により Phase 1（storage/ + providers/）は完了、pytest 390 passed で閉じている
- `src/apsf/legacy/orchestration/` skeleton は run-024 で着地済みである
- config/, prompts/, executors/ の `__init__.py` には既存 re-export があり、bridge 更新が可能である
- 今回は Codex 実装 run であり、Phase 2 の対象に閉じる

Decision: Proceed

---

## Problem Structure

今回は config/, prompts/, executors/, 軽量 orchestration の 4 単位を
legacy/ 側へ移す run である。

Phase 1 と異なる点が 2 つある。

1. **agents/ が今回の移動対象ではないが、config/ と prompts/ の主な caller である**
   - agents/ は Phase 3 で移動する
   - 今回は agents/ の import パスを `..legacy.config.*` / `..legacy.prompts.*` へ更新する
   - Phase 3 で agents/ が legacy/agents/ に移ったとき、`..config.*` / `..prompts.*` へ改めて更新する（legacy/ 内の相対パス）

2. **軽量 orchestration は `from apsf.orchestration.*` の直接 module import が多い**
   - `orchestration/__init__.py` の bridge だけでは賄えない
   - tests, cli, viewer/api.py の直接 import を全量更新する

---

## 対象ファイル一覧

### 移動対象

| 元パス | 移行先 | 内部 import 修正 |
|---|---|---|
| `src/apsf/config/settings.py` | `src/apsf/legacy/config/settings.py` | なし（stdlib + dotenv のみ） |
| `src/apsf/prompts/loader.py` | `src/apsf/legacy/prompts/loader.py` | なし（stdlib のみ） |
| `src/apsf/prompts/renderer.py` | `src/apsf/legacy/prompts/renderer.py` | なし（stdlib のみ） |
| `src/apsf/executors/api_executor.py` | `src/apsf/legacy/executors/api_executor.py` | `..core.` → `...core.`、`..legacy.providers.` → `..providers.` |
| `src/apsf/executors/cli_executor.py` | `src/apsf/legacy/executors/cli_executor.py` | `..core.` → `...core.` |
| `src/apsf/executors/human_executor.py` | `src/apsf/legacy/executors/human_executor.py` | `..core.` → `...core.` |
| `src/apsf/orchestration/phase_detector.py` | `src/apsf/legacy/orchestration/phase_detector.py` | TYPE_CHECKING 内 `apsf.orchestration.` → `apsf.legacy.orchestration.` |
| `src/apsf/orchestration/transcript_generator.py` | `src/apsf/legacy/orchestration/transcript_generator.py` | TYPE_CHECKING 内 同上 |
| `src/apsf/orchestration/next_instruction_builder.py` | `src/apsf/legacy/orchestration/next_instruction_builder.py` | `.phase_detector` は維持、TYPE_CHECKING 内 同上 |
| `src/apsf/orchestration/handoff_service.py` | `src/apsf/legacy/orchestration/handoff_service.py` | `..core.` → `...core.` |

### 新設する `__init__.py`

- `src/apsf/legacy/config/__init__.py`
- `src/apsf/legacy/prompts/__init__.py`
- `src/apsf/legacy/executors/__init__.py`

---

## Caller の全量と更新パターン

### config/settings → legacy/config/settings

| ファイル | 変更パターン |
|---|---|
| `src/apsf/config/__init__.py` | `from .settings import` → `from ..legacy.config.settings import` |
| `src/apsf/agents/critic.py` | `from ..config.settings import` → `from ..legacy.config.settings import` |
| `src/apsf/agents/planner.py` | 同上 |
| `src/apsf/cli/main.py` | lazy `from ..config.settings import` → `from ..legacy.config.settings import`（14 箇所） |
| `src/apsf/orchestration/act_service.py` | `from ..config.settings import` → `from ..legacy.config.settings import` |
| `src/apsf/orchestration/assignment_service.py` | 同上 |
| `src/apsf/orchestration/execution_assignment_service.py` | 同上 |
| `tests/test_assignment_service.py` | `from apsf.config.settings import` → `from apsf.legacy.config.settings import` |
| `tests/test_execution_assignment_service.py` | 同上 |

### prompts/renderer → legacy/prompts/renderer

| ファイル | 変更パターン |
|---|---|
| `src/apsf/prompts/__init__.py` | `from .loader import`、`from .renderer import` → `from ..legacy.prompts.*` |
| `src/apsf/agents/builder.py` | `from ..prompts.renderer import` → `from ..legacy.prompts.renderer import` |
| `src/apsf/agents/critic.py` | 同上 |
| `src/apsf/agents/judge.py` | 同上 |
| `src/apsf/agents/junior_builder.py` | 同上 |
| `src/apsf/agents/planner.py` | 同上 |
| `src/apsf/cli/main.py` | lazy `from ..prompts.renderer import` → `from ..legacy.prompts.renderer import`（1 箇所） |
| `src/apsf/orchestration/act_service.py` | `from ..prompts.renderer import` → `from ..legacy.prompts.renderer import` |
| `tests/test_renderer.py` | `from apsf.prompts.renderer import` → `from apsf.legacy.prompts.renderer import` |

### executors/ → legacy/executors/

| ファイル | 変更パターン |
|---|---|
| `src/apsf/executors/__init__.py` | `.cli_executor`、`.human_executor`、`.api_executor` → `..legacy.executors.*` |
| `src/apsf/orchestration/execution_assignment_service.py` | `from ..executors.X import` → `from ..legacy.executors.X import`（3 行） |
| `tests/test_execution_assignment_service.py` | `from apsf.executors.X import` → `from apsf.legacy.executors.X import`（2 行） |

### 軽量 orchestration → legacy/orchestration/

| ファイル | 変更パターン |
|---|---|
| `src/apsf/orchestration/__init__.py` | `.handoff_service`、`.next_instruction_builder`、`.transcript_generator` → `.legacy.orchestration.*`（ただし `pipeline`、`AssignmentService` 等は変更しない） |
| `src/apsf/orchestration/act_service.py` | `from ..orchestration.phase_detector import` → `from ..legacy.orchestration.phase_detector import`、`from ..orchestration.next_instruction_builder import` → `from ..legacy.orchestration.next_instruction_builder import` |
| `src/apsf/cli/main.py` | lazy `from ..orchestration.phase_detector import` → `from ..legacy.orchestration.phase_detector import`（5 箇所）、`from ..orchestration.transcript_generator import` → `from ..legacy.orchestration.transcript_generator import`（1 箇所）、`from ..orchestration.next_instruction_builder import` → `from ..legacy.orchestration.next_instruction_builder import`（2 箇所） |
| `src/apsf/viewer/api.py` | `from apsf.orchestration.phase_detector import` → `from apsf.legacy.orchestration.phase_detector import` |
| `tests/test_phase_detector.py` | `from apsf.orchestration.phase_detector import` → `from apsf.legacy.orchestration.phase_detector import` |
| `tests/test_next_instruction_builder.py` | phase_detector + next_instruction_builder の 2 行更新 |
| `tests/test_transcript_generator.py` | `from apsf.orchestration.transcript_generator import` → `from apsf.legacy.orchestration.transcript_generator import` |
| `tests/test_cli_write_phase.py` | 同上 |
| `tests/test_existing_run_optional_files.py` | `from apsf.orchestration.phase_detector import` → `from apsf.legacy.orchestration.phase_detector import` |
| `tests/test_ondemand_creation_guidance.py` | phase_detector + next_instruction_builder の 2 行更新 |

---

## Execution Steps

### Step 1. legacy/ 新規ディレクトリを作る

```bash
mkdir -p src/apsf/legacy/config src/apsf/legacy/prompts src/apsf/legacy/executors
```

各ディレクトリに空の `__init__.py` を配置する。

### Step 2. config/ を移す

- `config/settings.py` を `legacy/config/settings.py` へコピー
- 元ファイルを削除
- `config/__init__.py` の import を legacy 向けに更新

### Step 3. prompts/ を移す

- `prompts/loader.py`, `prompts/renderer.py` を `legacy/prompts/` へコピー
- 元ファイルを削除
- `prompts/__init__.py` の import を legacy 向けに更新

### Step 4. executors/ を移す

- 3 ファイルを `legacy/executors/` へコピー
- 元ファイルを削除
- 移動後のファイル内 `..core.` → `...core.`、`..legacy.providers.` → `..providers.` を修正
- `executors/__init__.py` の import を legacy 向けに更新

### Step 5. 軽量 orchestration を移す

- 4 ファイルを `legacy/orchestration/` へコピー
- 元ファイルを削除
- 移動後ファイル内の深度修正（`..core.` → `...core.`）、TYPE_CHECKING ブロックの更新
- `orchestration/__init__.py` の該当 import を legacy 向けに更新

### Step 6. 全 caller の import を更新する

上記 Caller 全量テーブルに従い、sed または手動で更新する。

### Step 7. pytest -q を実行して確認する

```bash
pytest -q tests/
```

結果を result.md に記録する。

---

## Scope Policy

### 含めるもの

- Step 1-7 の全作業
- agents/ の config/prompts import 更新（移動なし、import パス更新のみ）

### 含めないもの

- agents/ 実装ファイルの移動
- cli/ 本体の移動
- act_service.py / assignment_service.py / execution_assignment_service.py の移動
- pipeline.py の移動
- viewer/ の変更（ただし viewer/api.py の import 更新は含む）

---

## Verification Policy

1. `legacy/config/`, `legacy/prompts/`, `legacy/executors/` に実装ファイルが存在する
2. `legacy/orchestration/` に軽量 4 ファイルが存在する
3. 元の config/, prompts/, executors/ の実装ファイルが存在しない
4. pytest の結果が記録されている（pass / 残存エラー両方）
5. agents/ / cli/ 実装を移動していない
