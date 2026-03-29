# Goal

Run: 2026-03-29-028_fw-improvement_reconstruction-unit-c3-phase2-executors-config-prompts-light-orchestration
Date: 2026-03-29

---

## Goal Readiness Check

- `run-026` で C3 の移行順序が planning-only で定義されている
- `run-027` で Phase 1 (`storage/ + providers/`) は完了し、`pytest: 390 passed` で閉じている
- `src/apsf/legacy/` skeleton はすでに着地済みであり、追加 landing を受けられる
- `pipeline.py` は core 寄り観察が得られているが、placement はまだ保留である
- 今回は Codex 実装 run であり、Phase 2 を `config/ + prompts/ + executors/ + 軽量 orchestration` に限定する

Decision: Proceed

---

## Objective

APSF 再構築の Unit C3 Phase 2 として、
`config/`、`prompts/`、`executors/`、および軽量 orchestration 実装を
`src/apsf/legacy/` 側へ landing させる。

今回の run では、
Phase 1 に続く次の安全な実装単位として、
比較的依存の読みやすい周辺実装を legacy 側へ移し、
必要最小限の import 更新と `pytest -q` による確認までを行う。

---

## Scope

この run で扱うのは次だけである。

1. `src/apsf/config/` の legacy landing
2. `src/apsf/prompts/` の legacy landing
3. `src/apsf/executors/` の legacy landing
4. 軽量 orchestration 実装の legacy landing
5. 必要最小限の import 更新
6. `pytest -q` による確認

---

## Constraints

### 含めるもの

- `src/apsf/legacy/config/`
- `src/apsf/legacy/prompts/`
- `src/apsf/legacy/executors/`
- 軽量 orchestration 実装
- それに伴う最小限の import 修正
- `pytest -q`

### 含めないもの

- `agents/` の移行
- `cli/` 本体の移行
- 重い orchestration 境界の確定
- `pipeline.py` の placement 確定
- viewer の再配置

### 判断上の制約

- Phase 2 は `config / prompts / executors / 軽量 orchestration` に閉じる
- `agents / cli` との連動移行を今回持ち込まない
- `pipeline.py` は観察対象であって、今回の移行対象にしない
- import 更新は Phase 2 の caller に必要な最小限に留める

---

## Success Criteria

1. `config/` が `src/apsf/legacy/config/` へ landing する
2. `prompts/` が `src/apsf/legacy/prompts/` へ landing する
3. `executors/` が `src/apsf/legacy/executors/` へ landing する
4. 対象の軽量 orchestration 実装が legacy 側へ landing する
5. 必要最小限の import 更新で整合が取れる
6. `pytest -q` の結果が確認される
7. `agents / cli / pipeline.py` を巻き込まずに終わる

---

## Verification

- landing 後のディレクトリ構造が存在する
- import 更新が反映されている
- `pytest -q` の結果が記録されている
- 今回の変更が Phase 2 の主語に留まっている

---

## Non-Goals

- `agents/` の移行
- `cli/` 本体の移行
- `pipeline.py` の最終 placement 判定
- viewer の再配置
- C3 全体の完了

---

## Inputs to Respect

- `runs/fw-improvement/2026-03-29-026_fw-improvement_reconstruction-unit-c3-legacy-python-migration-planning/result.md`
- `runs/fw-improvement/2026-03-29-027_fw-improvement_reconstruction-unit-c3-phase1-storage-providers/result.md`
- `src/apsf/core/`
- `src/apsf/legacy/`

特に次を守ること。

- Phase 2 は `storage + providers` の次段である
- `agents / cli` はまだ別単位として扱う
- `pipeline.py` は今回判断を閉じない

---

## Desired Landing

この run の着地は、
`config/`、`prompts/`、`executors/`、軽量 orchestration が
`src/apsf/legacy/` 側へ着地し、
必要な import 更新とテスト確認まで終わっている状態である。

同時に、
まだ重い `agents / cli / pipeline.py` の論点を持ち込まず、
次段の移行判断をさらに narrow に進められる状態を作る。
