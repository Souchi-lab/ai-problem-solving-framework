# Goal

Run: 2026-03-29-034_fw-improvement_pipeline-legacy-landing
Date: 2026-03-29

---

## Goal Readiness Check

- `run-032` で `src/apsf/orchestration/pipeline.py` は legacy 判定で確定している
- `run-033` で reconstruction 系列は result-complete として閉じている
- `src/apsf/legacy/` はすでに skeleton と主要実装群の landing を持っている
- 今回は残件 2 本のうちの 1 本として、`pipeline.py` の実移動だけを扱う
- placement 判定は終わっているため、今回は implementation run に集中できる

Decision: Proceed

---

## Objective

`src/apsf/orchestration/pipeline.py` を
`src/apsf/legacy/orchestration/` 側へ landing させ、
必要最小限の import 更新と確認を行う。

今回の run は、
再構築後に残っていた `pipeline.py` の実移動を単独で完了させることを目的とする。

---

## Scope

この run で扱うのは次だけである。

1. `pipeline.py` の legacy landing
2. それに伴う最小限の import 更新
3. 必要なら package-level `__init__` の追従
4. `pytest -q` または最小確認

---

## Constraints

### 含めるもの

- `src/apsf/orchestration/pipeline.py`
- `src/apsf/legacy/orchestration/pipeline.py`
- その caller / import 更新
- 最小テスト確認

### 含めないもの

- `planning-patterns.md` の判定
- viewer の再配置
- 新しい構造変更
- reconstruction 全体の再整理

### 判断上の制約

- `pipeline.py` 単独 run に留める
- 新しい placement 議論を再開しない
- import 更新はこの移動に必要な最小限に留める

---

## Success Criteria

1. `pipeline.py` が `src/apsf/legacy/orchestration/` へ landing する
2. caller 側 import が整合する
3. 新規 failure を出さずに確認が取れる
4. `planning-patterns.md` など他の残件を巻き込んでいない
5. reconstruction 後の残件 1 本を減らしたと言える

---

## Verification

- landing 後のファイル位置が確認できる
- import 更新が反映されている
- `pytest -q` または最小 smoke で破綻がない

---

## Non-Goals

- `planning-patterns.md` の判断
- viewer の再配置
- 新しい redesign 文書の追加

---

## Inputs to Respect

- `runs/fw-improvement/2026-03-29-032_fw-improvement_pipeline-placement-read/result.md`
- `runs/fw-improvement/2026-03-29-033_fw-improvement_reconstruction-final-handoff/result.md`
- `src/apsf/core/`
- `src/apsf/legacy/`

特に次を守ること。

- `pipeline.py` は legacy 判定済み
- 今回は実移動だけを行う
- reconstruction 系列を再び広げない

---

## Desired Landing

この run の着地は、
`pipeline.py` が `src/apsf/legacy/orchestration/` 側へ着地し、
再構築後の残件が
`planning-patterns.md` 精読 1 本だけになる状態である。
