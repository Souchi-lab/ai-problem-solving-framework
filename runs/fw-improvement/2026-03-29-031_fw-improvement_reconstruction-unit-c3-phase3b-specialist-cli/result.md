# Result

---

## Status

Completed

---

## 実施内容

### 移動したファイル

| 元パス | 移行先 |
|---|---|
| `src/apsf/cli/specialist_registry.py` | `src/apsf/legacy/cli/specialist_registry.py` |
| `src/apsf/cli/role_rules.py` | `src/apsf/legacy/cli/role_rules.py` |
| `src/apsf/cli/io.py` | `src/apsf/legacy/cli/io.py` |
| `src/apsf/cli/main.py` | `src/apsf/legacy/cli/main.py` |
| `src/apsf/agents/planner.py` | `src/apsf/legacy/agents/planner.py` |
| `src/apsf/agents/critic.py` | `src/apsf/legacy/agents/critic.py` |
| `src/apsf/orchestration/act_service.py` | `src/apsf/legacy/orchestration/act_service.py` |

### 移動後の内部 import 修正

| ファイル | 修正内容 |
|---|---|
| `legacy/agents/planner.py` | `..legacy.config.settings` → `..config.settings`、`...cli.specialist_registry` → `..cli.specialist_registry`、`..core.*` → `...core.*`、`..legacy.prompts.renderer` → `..prompts.renderer` |
| `legacy/agents/critic.py` | 同上（同じパターン） |
| `legacy/orchestration/act_service.py` | `..legacy.config.settings` → `..config.settings`、`...cli.specialist_registry` → `..cli.specialist_registry`（3点→2点修正）、`..core.*` → `...core.*`、`..legacy.orchestration.*` → `..orchestration.*`、`..legacy.prompts.renderer` → `..prompts.renderer`、`..legacy.providers.*` → `..providers.*`、`..orchestration.assignment_service` → `..assignment_service` |
| `legacy/cli/main.py` | `..legacy.*` → `..*`（36箇所）、`..core.*` → `...core.*`、`..viewer.api` → `...viewer.api`、`.io/.role_rules/.specialist_registry` は変更なし |

### caller 更新

| ファイル | 変更内容 |
|---|---|
| `src/apsf/agents/__init__.py` | `from .planner import PlannerAgent` → `from ..legacy.agents.planner import PlannerAgent`、`from .critic import CriticAgent` → `from ..legacy.agents.critic import CriticAgent` |
| `src/apsf/cli/__init__.py` | `__getattr__` 内 `from .main import app` → `from ..legacy.cli.main import app` |
| `pyproject.toml` | `apsf = "apsf.cli.main:app"` → `apsf = "apsf.legacy.cli.main:app"` |
| `tests/test_cli_act.py` | `from apsf.cli.main import app` → `from apsf.legacy.cli.main import app`、patch パスを `apsf.orchestration.act_service.ActService` → `apsf.legacy.orchestration.act_service.ActService`（8箇所） |
| `tests/test_cli_start_run.py` | `from apsf.cli.main import app` → `from apsf.legacy.cli.main import app` |
| `tests/test_cli_write_phase.py` | 同上 |
| `tests/test_existing_run_optional_files.py` | 同上 |
| `tests/test_optionalization_fresh_run.py` | 同上 |
| `tests/test_specialist_registry.py` | `from apsf.cli.specialist_registry import` → `from apsf.legacy.cli.specialist_registry import` |
| `tests/test_specialist_selection.py` | 同上 |
| `tests/test_role_rules.py` | `from apsf.cli.role_rules import` → `from apsf.legacy.cli.role_rules import` |
| `tests/test_cli_io.py` | `from apsf.cli.io import` → `from apsf.legacy.cli.io import` |

### import 修正の補足（plan 差分）

計画時に未検出だった caller が 4 ファイル追加された：

- `tests/test_specialist_registry.py` — `apsf.cli.specialist_registry` 直接 import
- `tests/test_specialist_selection.py` — 同上
- `tests/test_role_rules.py` — `apsf.cli.role_rules` 直接 import
- `tests/test_cli_io.py` — `apsf.cli.io` 直接 import（遅延 import 形式）

また `legacy/agents/planner.py`・`critic.py`・`orchestration/act_service.py` の `...cli.specialist_registry`（3点）を `..cli.specialist_registry`（2点）に修正した。
プランでは「`...cli.specialist_registry`」と記載されていたが、`legacy/` 内からは 2点が正しいパスである。

---

## pytest 結果

```
390 passed, 2 failed
```

**2 件は pre-existing failure（Phase 3A 時点から変化なし）**。今回の Phase 3B 移行による新規失敗はゼロ。

---

## Verification チェック

| # | 基準 | 結果 |
|---|---|---|
| 1 | `legacy/cli/` に specialist_registry / role_rules / io / main が存在する | ✅ |
| 2 | `legacy/agents/` に planner / critic が存在する | ✅ |
| 3 | `legacy/orchestration/` に act_service が存在する | ✅ |
| 4 | `pyproject.toml` entry point が `apsf.legacy.cli.main:app` になっている | ✅ |
| 5 | pytest 結果が記録されている（新規失敗ゼロ） | ✅ |
| 6 | `pipeline.py` を巻き込んでいない | ✅ |

---

## 現在の残り

Phase 3B 完了により、C3 の主要 Python legacy 移行が一通り完了した。

残る論点：

| ファイル | 状態 |
|---|---|
| `orchestration/pipeline.py` | placement 保留継続（今回も移行対象外） |
