# Goal

Run: 2026-03-29-023_fw-improvement_reconstruction-unit-c-legacy-landing-planning
Date: 2026-03-29

---

## Goal Readiness Check

- `run-018` で repo-specific directory mapping と implementation-planning acceptance criteria が定義されている
- `run-019` で Unit C は legacy landing cleanup planning として切り出されている
- `run-020` で `framework/core/` が実体として着地済み
- `run-021` で `src/apsf/core/` が実体として着地済み
- `run-022` で `framework/execution-model.md` は legacy 判定となり、Unit C 前の迷い資産 1 点が解消済み
- 今回は planning-only run であり、実ファイル移動や import 修正は行わない

Decision: Proceed

---

## Objective

APSF 再構築の Unit C として、
`framework/legacy/` と `src/apsf/legacy/` の受け皿設計を行い、
次の legacy 移行 run が安全に始められる状態を作る。

今回の run では、
legacy として扱うべき資産群を受け止めるための
最小 directory structure、
移行単位、
導線方針、
保留資産の扱いを planning-only で定義する。

---

## Scope

この run で扱うのは次だけである。

1. `framework/legacy/` の受け皿方針
2. `src/apsf/legacy/` の受け皿方針
3. legacy 移行を始めるための最小単位の定義
4. core / legacy / experimental / viewer の境界を壊さない導線方針
5. 保留資産の置き場所または保留継続方針の明示

---

## Constraints

### 含めるもの

- legacy landing structure の計画
- legacy 移行単位の順序づけ
- 旧位置スタブや README 誘導の方針整理
- `execution-model.md` legacy 判定の反映

### 含めないもの

- 実ファイル移動
- Python import 修正
- `planning-patterns.md` の精読確定
- `pipeline.py` の精読確定
- viewer の構造変更
- experimental follow-up 群の再配置

### 判断上の制約

- legacy を「全部まとめて置く箱」にしない
- Unit A / B で確定した core 境界を後退させない
- `execution-model.md` は legacy 前提で扱う
- `planning-patterns.md` と `pipeline.py` は、今回無理に確定しない

---

## Success Criteria

1. `framework/legacy/` の最小 structure 方針が定義される
2. `src/apsf/legacy/` の最小 structure 方針が定義される
3. 最初に移せる legacy 単位が 1 つ以上明示される
4. 旧位置導線の扱いが方針として定義される
5. `execution-model.md` の legacy landing が自然に接続される
6. `planning-patterns.md` / `pipeline.py` を無理に決めずに済んでいる
7. 次の Codex 実装 run の入口になる planning result になっている

---

## Verification

- legacy landing の structure と順序が Markdown で読める
- Unit A / B / `run-022` と矛盾していない
- 次の legacy 移行 run の主語が自然に切れる

---

## Non-Goals

- legacy 実装の実移動
- `planning-patterns.md` の core / legacy 判定
- `pipeline.py` の core / legacy 判定
- viewer の再配置
- redesign / follow-up package の再整理

---

## Inputs to Respect

- `runs/fw-improvement/2026-03-28-018_fw-improvement_reconstruction-asset-classification/result.md`
- `runs/fw-improvement/2026-03-29-019_fw-improvement_reconstruction-implementation-planning/result.md`
- `runs/fw-improvement/2026-03-29-020_fw-improvement_reconstruction-unit-a-core-docs/result.md`
- `runs/fw-improvement/2026-03-29-021_fw-improvement_reconstruction-unit-b-core-python/result.md`
- `runs/fw-improvement/2026-03-29-022_fw-improvement_execution-model-placement-read/result.md`

特に次を守ること。

- core はすでに `framework/core/` と `src/apsf/core/` に着地済み
- `execution-model.md` は legacy 判定済み
- `planning-patterns.md` と `pipeline.py` は保留継続でもよい

---

## Desired Landing

この run の着地は、
legacy を受け止めるための
`framework/legacy/` と `src/apsf/legacy/`
の計画上の骨格が定義され、
次の実装 run が
「最初にどの legacy 単位をどこへ移すか」
を迷わず始められる状態である。

今回必要なのは、
legacy 側の受け皿設計を narrow に固めることであり、
保留資産をすべて同時に解決することではない。
