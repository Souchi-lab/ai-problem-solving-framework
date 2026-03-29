# Result

---

## Status

Completed

---

## Run 系列サマリー（018〜032）

| Run | 主語 | 結果 |
|---|---|---|
| 018 | 資産分類 | 47 点を core / legacy / experimental / docs に分類。迷い資産 3 点（execution-model.md / planning-patterns.md / pipeline.py）を明示 |
| 019 | 実装計画 | Unit A → B → C の 3 単位と実施順序を定義 |
| 020 | Unit A（framework/core/ 文書） | `operating-model.md` + `responsibility-matrix.md` を `framework/core/` に着地。旧位置に導線スタブ |
| 021 | Unit B（src/apsf/core/ Python） | `domain/models.py` + 3 × `base.py` を `src/apsf/core/` に着地。import を直接更新 |
| 022 | execution-model.md 精読 | **legacy 判定確定**。v0.1 CLI 運用前提。安定契約は core コードに着地済み |
| 023 | Unit C 着地計画 | C1（framework/legacy/ 文書）/ C2（src/apsf/legacy/ skeleton）/ C3（Python 実装移行計画）に分割 |
| 024 | Unit C2（skeleton） | `src/apsf/legacy/` + cli/orchestration/storage の `__init__.py` + README.md を新設。ファイル移動なし |
| 025 | Unit C1（framework/legacy/ 文書） | `execution-model.md` / `overview.md` / `workflow/` / `agents/` / `templates/` / `skills/` を `framework/legacy/` に着地 |
| 026 | Unit C3 計画 | import 依存グラフから 4 フェーズ構成を定義。agents/cli の cross-module 依存を発見し Phase 3 を 3A/3B に後続分割する布石 |
| 027 | Phase 1（storage + providers） | `legacy/storage/` + `legacy/providers/` 着地。pytest 390 passed |
| 028 | Phase 2（config/prompts/executors/軽量 orchestration） | `legacy/config/` + `legacy/prompts/` + `legacy/executors/` + 軽量 orchestration 4 本着地。pytest 390 passed |
| 029 | Phase 3 計画（3A/3B 分割） | `cli/specialist_registry` 依存を軸に 3A（独立移行）/ 3B（連動移行）に分割確定 |
| 030 | Phase 3A（builder 系 + assignment 系） | `builder/judge/junior_builder` + `assignment_service/execution_assignment_service` 着地。pytest 390 passed |
| 031 | Phase 3B（specialist_registry + planner/critic + act_service + cli/） | 連動 7 本着地。pyproject.toml entry point 更新。pytest 390 passed |
| 032 | pipeline.py 精読 | **legacy 判定確定**。`run_all()` に print/input あり。core import のみでも具象 CLI 実装 |

---

## 着地済み資産

### framework/

| 層 | 実体 |
|---|---|
| `framework/core/` | `operating-model.md`、`responsibility-matrix.md`、`README.md` |
| `framework/legacy/` | `execution-model.md`、`overview.md`、`workflow/v0.1.md`、`workflow/v0.2.md`、`agents/`（planners/critics/ 含む）、`templates/`、`skills/planning-patterns.md`、`README.md` |
| `framework/experimental/` | 現位置維持（変更なし）|
| `framework/improvement-notes/` | docs 層として現位置維持 |
| `framework/planning-patterns.md` | root 直下に残存（判断保留継続）|

### src/apsf/

| 層 | 実体 |
|---|---|
| `src/apsf/core/` | `domain/models.py`、`providers/base.py`、`agents/base.py`、`executors/base.py` |
| `src/apsf/legacy/` | `storage/`、`providers/`（anthropic/openai/gemini）、`config/`、`prompts/`、`executors/`（api/cli/human）、`orchestration/`（phase_detector/transcript_generator/next_instruction_builder/handoff_service/assignment_service/execution_assignment_service/act_service）、`agents/`（builder/judge/junior_builder/planner/critic）、`cli/`（specialist_registry/role_rules/io/main.py） |
| `src/apsf/viewer/` | 独立サポート層として現位置維持 |
| `pyproject.toml` | entry point = `apsf.legacy.cli.main:app` |

### pytest 状態

Phase 1〜3B 全フェーズで **390 passed、2 failed（pre-existing）**。新規失敗ゼロ。

---

## 確定した判断

| 判断 | 根拠 run |
|---|---|
| `framework/execution-model.md` → legacy | run-022：v0.1 CLI 運用前提。安定契約は `src/apsf/core/` に着地済み |
| `src/apsf/orchestration/pipeline.py` → legacy | run-032：`run_all()` に print/input。core import のみでも still-human-operated な具象実装 |
| Python 実装の旧位置に re-export スタブを置かない | run-021/023：import を直接更新する方針 |
| framework 文書は旧位置に導線スタブを残す | run-020/025：急な意味断絶を防ぐ |
| viewer は移行対象外（独立サポート層） | run-018/023 |
| `framework/legacy/` は削除候補ではなく readable な写しとして維持 | run-023 Minor Revision 4 相当 |

---

## 未完了（次に切れる個別 run）

### 1. `pipeline.py` 実移動 run

| 項目 | 内容 |
|---|---|
| 状態 | placement 確定済み（legacy）・実移動未実施 |
| 作業 | `src/apsf/orchestration/pipeline.py` → `src/apsf/legacy/orchestration/pipeline.py`、内部 import 深度修正、caller 確認、pytest |
| 規模 | 小（単ファイル移動）。Phase 1-3B の手順をそのまま適用できる |

### 2. `framework/planning-patterns.md` 精読 run

| 項目 | 内容 |
|---|---|
| 状態 | run-018 以来 root 直下に保留継続 |
| 作業 | 精読して core / legacy / hold を判定。実移動は別 run でもよい |
| 規模 | 小（read-only 判定 run）。run-022 / run-032 と同型 |

---

## 次 trigger

```
1. pipeline.py 実移動 run
2. framework/planning-patterns.md 精読 run
```

どちらも独立・小規模・順序不問。

---

## reconstruction 系列として何が閉じたか

- `src/apsf/core/` と `src/apsf/legacy/` の 3 層分離が Python 実装レベルで着地した
- `framework/core/` と `framework/legacy/` の文書 3 層分離が着地した
- 迷い資産 3 点のうち 2 点（execution-model.md / pipeline.py）の placement が確定した
- CLI entry point が `apsf.legacy.cli.main:app` として整合した
- 全フェーズで pytest 新規失敗ゼロを維持した

## reconstruction 系列として何が閉じていないか

- `pipeline.py` の実移動（判定済みだが未実施）
- `framework/planning-patterns.md` の判定（まだ read していない）
- legacy の最終的な retirement 条件（今回スコープ外・将来論点）
- viewer の将来的な再配置（今回スコープ外）
- APSF 全体の設計完了（reconstruction の次フェーズに委ねる）
