# Goal

Run: 2026-03-29-029_fw-improvement_reconstruction-unit-c3-phase3-agents-cli-heavy-orchestration-planning
Date: 2026-03-29

---

## Goal Readiness Check

- `run-027` で Phase 1 (`storage/ + providers/`) は完了している
- `run-028` で Phase 2 (`config/ + prompts/ + executors/ + 軽量 orchestration`) は完了している
- `src/apsf/legacy/` skeleton は着地済みであり、legacy 側の landing 先は存在する
- 残る主要実装群は `agents/`、`cli/` 本体、重め orchestration に絞られている
- `pipeline.py` は観察上 core 寄りだが、placement はまだ保留である
- 今回は planning-only run であり、実装移行や import 修正は行わない

Decision: Proceed

---

## Objective

APSF 再構築の Unit C3 Phase 3 planning として、
`agents/`、`cli/` 本体、重め orchestration 実装の
連動移行順序を定義する。

今回の run では、
どの単位を先に landing させると安全か、
どの単位は同時移行すべきか、
`specialist_registry` と `agents/` の結びつきをどう扱うか、
重め orchestration を一括にするか分割するかを
planning-only で整理する。

---

## Scope

この run で扱うのは次だけである。

1. `cli/specialist_registry.py` と `agents/` の関係整理
2. `agents/` の landing 単位の定義
3. `cli/` 本体の landing 単位の定義
4. 重め orchestration (`act_service.py`, `assignment_service.py`, `execution_assignment_service.py`) の順序づけ
5. `pipeline.py` の観察更新

---

## Constraints

### 含めるもの

- `src/apsf/agents/`
- `src/apsf/cli/`
- `src/apsf/orchestration/act_service.py`
- `src/apsf/orchestration/assignment_service.py`
- `src/apsf/orchestration/execution_assignment_service.py`
- `src/apsf/orchestration/pipeline.py` の観察

### 含めないもの

- 実ファイル移動
- import 修正
- `pipeline.py` の placement 確定
- viewer の再配置
- Phase 4 相当の新規拡張

### 判断上の制約

- `agents/` と `cli/specialist_registry.py` の依存を正面から扱う
- trivial な相対 import 深度修正と、構造的な連動移行を区別する
- 重め orchestration は「何となく最後」ではなく依存理由つきで順序づける
- `pipeline.py` は今回も観察対象であって、確定対象ではない

---

## Success Criteria

1. `cli/specialist_registry.py` を先行させるか `agents/` と同時かが明示される
2. `agents/` の landing 単位が定義される
3. `cli/` 本体の landing 単位が定義される
4. 重め orchestration の移行順序に理由がある
5. `pipeline.py` の観察更新が残る
6. 次の Codex 実装 run の主語が自然に切れる

---

## Verification

- Phase 3 の連動移行順序が Markdown で読める
- 次の実装 run を 1 本以上切れる具体性がある
- `pipeline.py` を無理に確定していない

---

## Non-Goals

- 実ファイル移動
- import 修正
- `pipeline.py` の最終 placement 判定
- viewer の再配置
- reconstruction 全体完了の宣言

---

## Inputs to Respect

- `runs/fw-improvement/2026-03-29-026_fw-improvement_reconstruction-unit-c3-legacy-python-migration-planning/result.md`
- `runs/fw-improvement/2026-03-29-027_fw-improvement_reconstruction-unit-c3-phase1-storage-providers/result.md`
- `runs/fw-improvement/2026-03-29-028_fw-improvement_reconstruction-unit-c3-phase2-executors-config-prompts-light-orchestration/result.md`

特に次を守ること。

- Phase 1 / Phase 2 の結果を前提にする
- 残りは `agents / cli / 重め orchestration` に絞る
- `pipeline.py` は input に入れても確定しない

---

## Desired Landing

この run の着地は、
残る Python 実装群について
「次にどの 1 単位をどう切るか」
が依存理由つきで narrow に定義され、
次の Codex 実装 run が
その単位へ迷わず着手できる状態である。

今回は Phase 3 の順序を決めることが目的であり、
最後の保留資産まで同時に確定することは目的ではない。
