# Plan

---

## Goal Readiness Check

- `run-024` により `src/apsf/legacy/` skeleton（cli/ orchestration/ storage/）は着地済みである
- `run-025` により `framework/legacy/` 文書 landing は完了している
- `run-021` により `src/apsf/core/` は着地済みであり、core 契約を前提に legacy 移行順序を読める
- 今回は planning-only run であり、実ファイル移動や import 修正は行わない

Decision: Proceed

---

## Problem Structure

今回の C3 は、
`src/apsf/legacy/` skeleton がすでにある前提で、
移行すべき Python 実装群の import 依存を読み、
「最初に何をどの順で動かすと安全か」を定義する run である。

計画の核心は 2 点である。

1. import 影響の狭いものから先に移す（依存の葉から根へ）
2. cross-module 依存のある単位は後回しにし、defer 理由を明示する

---

## Import Dependency Map

src/apsf/ 内の相互 import を読んだ結果を整理する。

### core/ からの import（すでに確定済み）

| 移行先 | 何を参照しているか |
|---|---|
| `providers/` 各 impl | `core/providers/base.py` のみ |
| `agents/` 各 impl | `core/agents/base.py` + `core/domain/models.py` + config/ + prompts/ + **cli/specialist_registry** |
| `executors/` 各 impl | `core/executors/base.py` + `core/domain/models.py` |
| `storage/` 各 impl | stdlib のみ |
| `config/settings.py` | stdlib + dotenv のみ |
| `prompts/loader.py` | stdlib のみ |
| `prompts/renderer.py` | stdlib のみ |
| `orchestration/phase_detector.py` | stdlib のみ |
| `orchestration/transcript_generator.py` | stdlib のみ |
| `orchestration/next_instruction_builder.py` | orchestration/phase_detector のみ |
| `orchestration/handoff_service.py` | `core/domain/models.py` のみ |
| `orchestration/assignment_service.py` | config/ + core/ + providers/ 全実装 |
| `orchestration/execution_assignment_service.py` | config/ + core/ + executors/ 全実装 |
| `orchestration/act_service.py` | config/ + core/ + cli/specialist_registry + orchestration/ 内 + prompts/ |
| `orchestration/pipeline.py` | `core/domain/models.py` + `core/executors/base.py` + `core/agents/base.py` |
| `cli/main.py` | config/ + storage/ + orchestration/ 各種（すべて lazy import） |

### 重要な cross-module 依存

- `agents/planner.py` が `cli/specialist_registry.py` を直接 import している
  - agents/ を単独で legacy へ移すと、cli/ 側の import パスがずれる
  - agents/ の移行は cli/ との同時移行か、先に specialist_registry の依存を解消するか、どちらかが必要

- `orchestration/act_service.py` が `cli/specialist_registry.py` を import している
  - act_service.py の移行も cli/ との連動が必要

- `cli/main.py` はすべての内部 import が関数内 lazy import であり、パッケージ初期化時に依存しない
  - cli/main.py は lazy import のおかげで「最後に移す」戦略が取りやすい

---

## Migration Unit Definition

### 依存の深さで層を分ける

```
Layer 0 (core/ — 完了済み)
  domain/models, agents/base, providers/base, executors/base

Layer 1 (stdlib / dotenv のみ — leaf)
  storage/, config/, prompts/, orchestration/phase_detector, orchestration/transcript_generator

Layer 2 (core/ のみに依存)
  providers/実装, executors/実装, orchestration/handoff_service

Layer 3 (Layer 1-2 + 同一パッケージ内依存)
  orchestration/next_instruction_builder, orchestration/assignment_service,
  orchestration/execution_assignment_service

Layer 4 (cli/ との cross-module 依存あり)
  agents/実装, orchestration/act_service

Layer 5 (全モジュールを lazy import — top-level)
  cli/main.py

[特殊]
  orchestration/pipeline.py → core/ のみ参照（Layer 2 相当だが placement 保留）
```

---

## Migration Order

安全な移行順序として 4 フェーズに分ける。

### Phase 1: storage/ + providers/ （最初の実装単位）

**対象**:

| 現パス | 移行先 |
|---|---|
| `src/apsf/storage/markdown_repository.py` | `src/apsf/legacy/storage/markdown_repository.py` |
| `src/apsf/storage/run_repository.py` | `src/apsf/legacy/storage/run_repository.py` |
| `src/apsf/providers/anthropic_provider.py` | `src/apsf/legacy/providers/anthropic_provider.py` |
| `src/apsf/providers/openai_provider.py` | `src/apsf/legacy/providers/openai_provider.py` |
| `src/apsf/providers/gemini_provider.py` | `src/apsf/legacy/providers/gemini_provider.py` |

**import 更新先（Phase 1 で変更するファイル）**:

| ファイル | 変更内容 |
|---|---|
| `cli/main.py` | `from ..storage.run_repository` → `from ..legacy.storage.run_repository` |
| `orchestration/assignment_service.py` | `from ..providers.X` → `from ..legacy.providers.X`（3 行） |

**理由**:
- storage/ は stdlib のみ依存で、inbound caller が cli/main.py（lazy）のみ
- providers/ は core/ のみ依存で、inbound caller が orchestration/assignment_service.py のみ
- 合計 import 更新行数が少なく、pytest がそのまま通るはず
- `src/apsf/legacy/providers/` は skeleton にないため、このフェーズで新設する

---

### Phase 2: config/ + prompts/ + executors/ + 軽量 orchestration （第 2 単位）

**対象**:

- `config/settings.py` → `legacy/config/settings.py`
- `prompts/loader.py` → `legacy/prompts/loader.py`
- `prompts/renderer.py` → `legacy/prompts/renderer.py`
- `executors/api_executor.py` → `legacy/executors/api_executor.py`
- `executors/cli_executor.py` → `legacy/executors/cli_executor.py`
- `executors/human_executor.py` → `legacy/executors/human_executor.py`
- `orchestration/phase_detector.py` → `legacy/orchestration/phase_detector.py`
- `orchestration/transcript_generator.py` → `legacy/orchestration/transcript_generator.py`
- `orchestration/next_instruction_builder.py` → `legacy/orchestration/next_instruction_builder.py`
- `orchestration/handoff_service.py` → `legacy/orchestration/handoff_service.py`

**import 更新先**: Phase 1 から残った全 orchestration / agents / cli の import パス

**理由**: Phase 1 完了後、callers が legacy/ 側に更新済みのため、同じパターンで拡張できる

---

### Phase 3: agents/ + orchestration/重量級 （第 3 単位）

**対象**:

- `agents/planner.py, builder.py, critic.py, judge.py, junior_builder.py`
- `orchestration/assignment_service.py`
- `orchestration/execution_assignment_service.py`
- `orchestration/act_service.py`

**前提条件**:
- Phase 2 完了後、`cli/specialist_registry.py` が legacy/cli/ に移動済みであること
- agents/ と act_service.py の cli/ 依存を解消してから着手する

**理由**: agents/ は cli/specialist_registry に依存しているため、cli/ の一部を先行移行するか、同時移行が必要

---

### Phase 4: cli/ （最終単位）

**対象**:

- `cli/main.py, cli/io.py, cli/role_rules.py, cli/specialist_registry.py`

**理由**: cli/main.py は全モジュールを lazy import しているため、他が全部 legacy/ に移り終わってから最後に移す

---

## pipeline.py の扱い

`orchestration/pipeline.py` は `core/` のみを参照しており、
Layer 2 相当の依存の浅さを持つ。

この特性から 2 通りの読み方がある。

- **core/ 昇格候補**: core/ だけに依存しているなら、core/ の一部として読める
- **legacy 扱い**: CLI 前提の実行制御ロジックであれば legacy 側が適切

今回は判断を確定しない。
次の実装 run（Phase 1）の result.md で、
pipeline.py の dependency を改めて確認してから判断する。

---

## Defer 対象の明示

| 単位 | defer 理由 |
|---|---|
| `agents/` | `cli/specialist_registry` への依存。cli/ との連動が必要 |
| `orchestration/act_service.py` | `cli/specialist_registry` への依存。同上 |
| `cli/` | top-level。他がすべて landing した後 |
| `orchestration/pipeline.py` | core vs legacy 判定を次 run に委ねる |
| `config/` | callers が多い（5+）。Phase 2 で一括処理が安全 |
| `viewer/` | 独立層。移行対象外 |

---

## 次の実装 run の主語

**Phase 1 実装 run（Codex）**

```
対象: src/apsf/storage/ + src/apsf/providers/
作業:
  1. src/apsf/legacy/providers/ を新設（__init__.py）
  2. storage/markdown_repository.py → legacy/storage/markdown_repository.py
  3. storage/run_repository.py → legacy/storage/run_repository.py
  4. providers/anthropic_provider.py → legacy/providers/anthropic_provider.py
  5. providers/openai_provider.py → legacy/providers/openai_provider.py
  6. providers/gemini_provider.py → legacy/providers/gemini_provider.py
  7. cli/main.py の storage import を legacy.storage へ更新
  8. orchestration/assignment_service.py の providers import を legacy.providers へ更新（3 行）
  9. pytest -q を通す
```

---

## Scope Policy

### 今回の planning run で確定したもの

- legacy Python 移行の 4 フェーズ構成
- Phase 1 の対象ファイルと import 更新先
- agents/ / cli/ の defer 理由
- pipeline.py の判断を次実装 run へ委ねる方針

### 今回確定していないもの

- Phase 2 以降の詳細 import 更新リスト（Phase 1 完了後に改めて確認）
- pipeline.py の core vs legacy 最終判定
- config/ を legacy/ に移した後の dotenv パス問題の有無
- viewer/ の扱い（対象外のまま）

---

## Verification Policy

この planning run の完了条件は次の 4 点である。

1. 最初の実装単位（Phase 1）が明示されている ✓
2. 移行順序に import 依存の根拠がある ✓
3. defer 理由が明示されている ✓
4. pipeline.py を無理に確定していない ✓
