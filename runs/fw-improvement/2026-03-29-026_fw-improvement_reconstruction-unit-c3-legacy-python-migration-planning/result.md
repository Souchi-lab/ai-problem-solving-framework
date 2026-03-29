# Result

---

## Status

Completed

---

## Output — Python Legacy Migration Order

### Import 依存グラフ（確認結果）

| Layer | 単位 | 依存先 |
|---|---|---|
| 0 | `core/` | 完了済み |
| 1 | `storage/`, `config/`, `prompts/`, `orchestration/phase_detector`, `orchestration/transcript_generator` | stdlib のみ |
| 2 | `providers/実装`, `executors/実装`, `orchestration/handoff_service` | core/ のみ |
| 3 | `orchestration/next_instruction_builder`, `orchestration/assignment_service`, `orchestration/execution_assignment_service` | Layer 1-2 |
| 4 | `agents/実装`, `orchestration/act_service` | Layer 1-3 + **cli/specialist_registry**（cross-module 依存） |
| 5 | `cli/main.py` | 全モジュール（lazy import） |
| 特殊 | `orchestration/pipeline.py` | core/ のみ（Layer 2 相当、placement 保留） |

### 重要発見: agents/ → cli/ cross-module 依存

`agents/planner.py` と `orchestration/act_service.py` が
`cli/specialist_registry.py` を直接 import している。

→ agents/ と act_service.py は cli/ との連動移行か、
　specialist_registry の依存解消なしには単独で移せない。

---

## Migration Order

### Phase 1（最初の実装単位）: storage/ + providers/

**対象ファイル**:

| 現パス | 移行先 |
|---|---|
| `src/apsf/storage/markdown_repository.py` | `src/apsf/legacy/storage/markdown_repository.py` |
| `src/apsf/storage/run_repository.py` | `src/apsf/legacy/storage/run_repository.py` |
| `src/apsf/providers/anthropic_provider.py` | `src/apsf/legacy/providers/anthropic_provider.py` |
| `src/apsf/providers/openai_provider.py` | `src/apsf/legacy/providers/openai_provider.py` |
| `src/apsf/providers/gemini_provider.py` | `src/apsf/legacy/providers/gemini_provider.py` |

**import 更新先**:

| ファイル | 変更内容 |
|---|---|
| `cli/main.py` | `from ..storage.*` → `from ..legacy.storage.*` |
| `orchestration/assignment_service.py` | `from ..providers.X` → `from ..legacy.providers.X`（3 行） |

**初手に選んだ理由**:
- storage/ は stdlib のみ依存、inbound caller は cli/main.py（lazy import）のみ
- providers/ は core/ のみ依存、inbound caller は orchestration/assignment_service.py のみ（3 行）
- 合計 import 更新が最小で最も影響が狭い

---

### Phase 2: config/ + prompts/ + executors/ + 軽量 orchestration

- `config/settings.py`
- `prompts/loader.py`, `prompts/renderer.py`
- `executors/api_executor.py, cli_executor.py, human_executor.py`
- `orchestration/phase_detector.py, transcript_generator.py, next_instruction_builder.py, handoff_service.py`

---

### Phase 3: agents/ + orchestration/重量級

- `agents/` 全実装（cli/specialist_registry との連動前提）
- `orchestration/assignment_service.py, execution_assignment_service.py, act_service.py`
- **前提**: `cli/specialist_registry.py` が先行して legacy/cli/ に移動済みであること

---

### Phase 4: cli/（最終）

- `cli/main.py, io.py, role_rules.py, specialist_registry.py`
- 他が全部 legacy/ に移り終わってから最後に移す

---

## Defer 対象

| 単位 | defer 理由 |
|---|---|
| `agents/` | `cli/specialist_registry` への cross-module 依存 |
| `orchestration/act_service.py` | 同上 |
| `cli/` | top-level（lazy import）。他が全部 landing した後 |
| `orchestration/pipeline.py` | core/ のみ参照という特性から core vs legacy 判定が必要。次実装 run で確認 |
| `viewer/` | 独立層、移行対象外 |

---

## Success Criteria 照合

| # | 基準 | 結果 |
|---|---|---|
| 1 | 最初の legacy Python 移行単位が 1 つ以上明示される | ✅ Phase 1（storage/ + providers/） |
| 2 | 移行順序に理由がある | ✅ import 依存グラフの layer 順 |
| 3 | import 影響の見方が明示される | ✅ 依存グラフ + 更新ファイル列挙 |
| 4 | defer すべき重い単位が区別される | ✅ agents/ cli/ act_service の defer 理由を明示 |
| 5 | 次の Codex 実装 run の主語が自然に切れる | ✅ Phase 1 で対象・作業・検証が切れている |
| 6 | `pipeline.py` を無理に確定していない | ✅ 判断を次実装 run に委ねる構えで閉じた |

---

## Next Trigger

**Phase 1 実装 run（Codex）**

```
対象: src/apsf/storage/ + src/apsf/providers/
作業:
  1. src/apsf/legacy/providers/ を新設（__init__.py）
  2. storage/ 2 ファイルを legacy/storage/ へ移動
  3. providers/ 3 ファイルを legacy/providers/ へ移動
  4. cli/main.py の storage import を legacy.storage へ更新
  5. orchestration/assignment_service.py の providers import を legacy.providers へ更新（3 行）
  6. pytest -q を通す
```

**pipeline.py 判定**（Phase 1 result.md 内で）

- core/ のみ参照という特性を確認し、core vs legacy の判断を記録する

---

## What This Run Decided

- Python legacy 移行の 4 フェーズ構成と Layer 定義
- Phase 1 の対象ファイル・import 更新先・選定理由
- agents/ / act_service.py の defer 理由（cli/specialist_registry cross-module 依存）
- pipeline.py の判断を Phase 1 result.md に委ねる方針

## What This Run Did Not Decide

- Phase 2 以降の詳細 import 更新リスト
- pipeline.py の core vs legacy 最終判定
- viewer/ の将来的な扱い
