# Goal

Run: 2026-03-29-025_fw-improvement_reconstruction-unit-c1-legacy-docs
Date: 2026-03-29

---

## Goal Readiness Check

- `run-023` で C1 は `framework/legacy/` 文書 landing として独立単位に定義されている
- `run-022` で `framework/execution-model.md` は legacy 判定済みである
- `run-020` により `framework/core/` は実体として着地済みであり、core / legacy の文書境界を repo 上で表現できる状態にある
- 今回は framework 文書のみを扱う実装 run であり、Python 実装や import 修正は含まない

Decision: Proceed

---

## Objective

APSF 再構築の Unit C1 として、
`framework/legacy/` を repo 上に実体化し、
legacy 文書群の最初の landing を行う。

今回の run では、
`framework/execution-model.md` を含む legacy 文書群を
`framework/legacy/` 配下へ移し、
旧位置から新位置への導線も最小限で残す。

---

## Scope

この run で扱うのは次だけである。

1. `framework/legacy/` の新設
2. `framework/legacy/README.md` または最小 overview の追加
3. `framework/execution-model.md` の legacy landing
4. workflow / agent / template / skill 系の framework 文書群の landing
5. 旧位置からの最小誘導

---

## Constraints

### 含めるもの

- `framework/legacy/`
- `framework/execution-model.md`
- workflow / agent / template / skill 系の framework 文書
- 最小 README / overview
- 旧位置スタブまたは短い誘導文

### 含めないもの

- `framework/planning-patterns.md` の判定
- `framework/core/` 側の追加変更
- `src/apsf/legacy/` 側の変更
- Python 実装移行
- viewer / docs / experimental の再配置

### 判断上の制約

- `legacy` を雑多な箱にしない
- `execution-model.md` は legacy 判定済みとして扱う
- `planning-patterns.md` は今回 landing 対象に含めない
- core 側の文書と役割が重ならないようにする

---

## Success Criteria

1. `framework/legacy/` が repo 上に実体として着地する
2. `framework/execution-model.md` が legacy 側に正しく landing する
3. 対象 framework 文書群が legacy 配下へ整理される
4. 旧位置からの導線が残る
5. `planning-patterns.md` を無理に含めていない
6. `framework/core/` の読みやすさを後退させていない
7. 次の C3 planning run が legacy 文書側を既成事実として扱える状態になる

---

## Verification

- `framework/legacy/` の構造が存在する
- `execution-model.md` の新旧位置関係が読める
- 対象文書群が landing 範囲に収まっている
- 今回の変更が framework 文書に閉じている

---

## Non-Goals

- `planning-patterns.md` の placement 判定
- Python legacy 実装の移行
- `src/apsf/legacy/` の拡張
- viewer / docs / experimental の整理

---

## Inputs to Respect

- `runs/fw-improvement/2026-03-28-018_fw-improvement_reconstruction-asset-classification/result.md`
- `runs/fw-improvement/2026-03-29-022_fw-improvement_execution-model-placement-read/result.md`
- `runs/fw-improvement/2026-03-29-023_fw-improvement_reconstruction-unit-c-legacy-landing-planning/result.md`

特に次を守ること。

- `execution-model.md` は legacy 判定で固定済み
- `planning-patterns.md` は保留資産のまま残す
- C1 は文書 legacy landing に限定する

---

## Desired Landing

この run の着地は、
`framework/legacy/` が repo 上に実体として存在し、
`execution-model.md` を含む legacy 文書群が
そこへ自然に着地している状態である。

また、旧位置からの導線が残っていることで、
legacy への再配置が読み手にとって急断絶にならない状態を作る。

今回は文書 legacy の landing を終えることが目的であり、
保留資産や Python legacy 実装まで同時に処理することは目的ではない。
