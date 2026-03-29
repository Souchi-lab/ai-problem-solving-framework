# Result

---

## Status

Completed

---

## 実施内容

### 移動したファイル

| 元パス | 移行先 |
|---|---|
| `src/apsf/config/settings.py` | `src/apsf/legacy/config/settings.py` |
| `src/apsf/prompts/loader.py` | `src/apsf/legacy/prompts/loader.py` |
| `src/apsf/prompts/renderer.py` | `src/apsf/legacy/prompts/renderer.py` |
| `src/apsf/executors/api_executor.py` | `src/apsf/legacy/executors/api_executor.py` |
| `src/apsf/executors/cli_executor.py` | `src/apsf/legacy/executors/cli_executor.py` |
| `src/apsf/executors/human_executor.py` | `src/apsf/legacy/executors/human_executor.py` |
| `src/apsf/orchestration/phase_detector.py` | `src/apsf/legacy/orchestration/phase_detector.py` |
| `src/apsf/orchestration/transcript_generator.py` | `src/apsf/legacy/orchestration/transcript_generator.py` |
| `src/apsf/orchestration/next_instruction_builder.py` | `src/apsf/legacy/orchestration/next_instruction_builder.py` |
| `src/apsf/orchestration/handoff_service.py` | `src/apsf/legacy/orchestration/handoff_service.py` |

### 新設した __init__.py

- `src/apsf/legacy/config/__init__.py`
- `src/apsf/legacy/prompts/__init__.py`
- `src/apsf/legacy/executors/__init__.py`

### 移動後の内部 import 修正

| ファイル | 修正内容 |
|---|---|
| `legacy/executors/api_executor.py` | `..core.` → `...core.`、`..legacy.providers.` → `..providers.` |
| `legacy/executors/cli_executor.py` | `..core.` → `...core.` |
| `legacy/executors/human_executor.py` | `..core.` → `...core.` |
| `legacy/orchestration/handoff_service.py` | `..core.` → `...core.` |
| `legacy/orchestration/phase_detector.py` | TYPE_CHECKING 内 `apsf.orchestration.` → `apsf.legacy.orchestration.` |
| `legacy/orchestration/transcript_generator.py` | 同上 |
| `legacy/orchestration/next_instruction_builder.py` | 同上（`.phase_detector` 相対 import は維持） |

### import 更新したファイル（plan 想定 + 追加発見）

| ファイル | 更新内容 |
|---|---|
| `src/apsf/config/__init__.py` | bridge → `legacy.config.settings` |
| `src/apsf/prompts/__init__.py` | bridge → `legacy.prompts.*` |
| `src/apsf/executors/__init__.py` | bridge → `legacy.executors.*` |
| `src/apsf/orchestration/__init__.py` | handoff_service / next_instruction_builder / transcript_generator → `legacy.orchestration.*` |
| `src/apsf/agents/critic.py` | config + prompts → legacy |
| `src/apsf/agents/planner.py` | config + prompts → legacy |
| `src/apsf/agents/builder.py` | prompts → legacy |
| `src/apsf/agents/judge.py` | prompts → legacy |
| `src/apsf/agents/junior_builder.py` | prompts → legacy |
| `src/apsf/cli/main.py` | config(14) + prompts(1) + phase_detector(5) + transcript_generator(1) + next_instruction_builder(2) → legacy |
| `src/apsf/orchestration/act_service.py` | config + prompts + phase_detector + next_instruction_builder → legacy |
| `src/apsf/orchestration/assignment_service.py` | config → legacy |
| `src/apsf/orchestration/execution_assignment_service.py` | config + executors → legacy |
| `src/apsf/viewer/api.py` | phase_detector → legacy |
| `tests/test_assignment_service.py` | config → legacy |
| `tests/test_execution_assignment_service.py` | config + executors → legacy |
| `tests/test_renderer.py` | prompts → legacy |
| `tests/test_phase_detector.py` | phase_detector → legacy |
| `tests/test_next_instruction_builder.py` | phase_detector + next_instruction_builder → legacy |
| `tests/test_transcript_generator.py` | transcript_generator → legacy |
| `tests/test_cli_write_phase.py` | transcript_generator + config（import as） → legacy |
| `tests/test_existing_run_optional_files.py` | phase_detector + config（import as）→ legacy |
| `tests/test_ondemand_creation_guidance.py` | phase_detector + next_instruction_builder → legacy |
| `tests/test_cli_act.py` | config（import as）→ legacy（**plan 未記載・追加発見**） |
| `tests/test_cli_start_run.py` | config（import as）→ legacy（**plan 未記載・追加発見**） |
| `tests/test_optionalization_fresh_run.py` | config（import as）→ legacy（**plan 未記載・追加発見**） |

### plan 想定との差分

`import apsf.config.settings as settings_module` パターン（`import as` 形式）が
plan で拾えていなかった 3 test ファイルに存在した。
`from apsf.config.settings import` パターンの grep で検出できなかったもの。
影響は軽微で同一パターン（`apsf.config.settings` → `apsf.legacy.config.settings`）で解消。

---

## pytest 結果

```
390 passed, 2 failed
```

**2 件は Phase 1 から変わらない pre-existing failure**:

- `test_run_repository.py::test_validate_run_name[2026-03-15_sochi-blocks-False]`
- `test_run_repository.py::TestValidateChildRunName::test_validate_child_run_name[016c1_sochi-blocks-False]`

今回の Phase 2 移行による新規失敗はゼロ。

---

## Verification チェック

| # | 基準 | 結果 |
|---|---|---|
| 1 | `legacy/config/` に実装が landing | ✅ |
| 2 | `legacy/prompts/` に実装が landing | ✅ |
| 3 | `legacy/executors/` に実装が landing | ✅ |
| 4 | 軽量 orchestration 4 ファイルが `legacy/orchestration/` に landing | ✅ |
| 5 | pytest 確認（新規失敗ゼロ） | ✅ |
| 6 | `agents/` / `cli/` 実装を移動していない | ✅ |
| 7 | `pipeline.py` を確定していない | ✅ |

---

## 次の状態

**legacy/ に landing 済み:**
- storage/ ✅ (Phase 1)
- providers/ ✅ (Phase 1)
- config/ ✅ (Phase 2)
- prompts/ ✅ (Phase 2)
- executors/ ✅ (Phase 2)
- orchestration/ 軽量 4 ファイル ✅ (Phase 2)

**未 landing（Phase 3 へ）:**
- `agents/` 実装（cli/ との連動前提）
- `cli/` 本体
- `orchestration/act_service.py, assignment_service.py, execution_assignment_service.py`
- `orchestration/pipeline.py`（placement 保留継続）
