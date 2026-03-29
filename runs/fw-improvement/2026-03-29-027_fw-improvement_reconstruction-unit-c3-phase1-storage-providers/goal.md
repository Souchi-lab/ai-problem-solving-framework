# Goal

Run: 2026-03-29-027_fw-improvement_reconstruction-unit-c3-phase1-storage-providers
Date: 2026-03-29

---

## Goal Readiness Check

- `run-026` で C3 の最初の実装単位は `storage/ + providers/` が妥当と整理済みである
- `src/apsf/legacy/` skeleton は `run-024` で着地済みである
- `framework/legacy/` 文書 landing は `run-025` で完了済みである
- `src/apsf/core/` はすでに着地しており、core 契約を参照する前提が整っている
- 今回は Codex 実装 run であり、Phase 1 の移行対象を `storage/ + providers/` に限定する

Decision: Proceed

---

## Objective

APSF 再構築の Unit C3 Phase 1 として、
`src/apsf/storage/` と `src/apsf/providers/` を
`src/apsf/legacy/` 側へ landing させる。

今回の run では、
最小限の import 更新だけを伴って
legacy Python 実装の最初の実移行を行い、
`pytest -q` による確認までを含めて閉じる。

また、`pipeline.py` については
今回 placement を確定しないまま、
Phase 1 実装結果を見て
core / legacy のどちらに寄るかを `result.md` に記録する。

---

## Scope

この run で扱うのは次だけである。

1. `src/apsf/legacy/providers/` の新設
2. `src/apsf/storage/` の legacy landing
3. `src/apsf/providers/` の legacy landing
4. 必要最小限の import 更新
5. `pytest -q` による確認
6. `pipeline.py` の観察メモを `result.md` に残す

---

## Constraints

### 含めるもの

- `src/apsf/legacy/storage/`
- `src/apsf/legacy/providers/`
- `cli/main.py` の storage import 更新
- `orchestration/assignment_service.py` の providers import 更新
- それに付随する最小限の import 修正
- `pytest -q`

### 含めないもの

- `agents/` の移行
- `cli/` 本体の移行
- `orchestration/act_service.py` の移行
- `pipeline.py` の placement 確定
- viewer の再配置

### 判断上の制約

- Phase 1 は `storage + providers` に閉じる
- import 更新は最小限に留める
- `agents/` と `cli/` の連動移行は今回持ち込まない
- `pipeline.py` は観察対象であって、今回の移行対象ではない

---

## Success Criteria

1. `src/apsf/storage/` が `src/apsf/legacy/storage/` へ landing する
2. `src/apsf/providers/` が `src/apsf/legacy/providers/` へ landing する
3. `cli/main.py` の storage import が更新される
4. `orchestration/assignment_service.py` の providers import が更新される
5. `pytest -q` の結果が確認される
6. `agents/` / `cli/` / `act_service.py` を巻き込まずに終わる
7. `pipeline.py` の core vs legacy 読みが `result.md` に観察メモとして残る

---

## Verification

- landing 後のディレクトリ構造が存在する
- 主要 import 更新が反映されている
- `pytest -q` の結果が記録されている
- 今回の変更が Phase 1 の主語に留まっている

---

## Non-Goals

- `agents/` の移行
- `cli/` 本体の移行
- `orchestration/act_service.py` の移行
- `pipeline.py` の最終 placement 判定
- C3 全体の完了

---

## Inputs to Respect

- `runs/fw-improvement/2026-03-29-026_fw-improvement_reconstruction-unit-c3-legacy-python-migration-planning/result.md`
- `runs/fw-improvement/2026-03-29-024_fw-improvement_reconstruction-unit-c2-legacy-python-skeleton/result.md`
- `src/apsf/core/`

特に次を守ること。

- Phase 1 の初手は `storage/ + providers/`
- `cli/main.py` と `orchestration/assignment_service.py` だけを主要更新点として扱う
- `pipeline.py` は今回判断を閉じない

---

## Desired Landing

この run の着地は、
`storage/` と `providers/` が
`src/apsf/legacy/` 側へ最初の Python legacy 実装として着地し、
最小限の import 更新とテスト確認まで終わっている状態である。

同時に、
`pipeline.py` については
Phase 1 の結果から見えた依存上の読みを `result.md` に残し、
次段の判断材料にする。
