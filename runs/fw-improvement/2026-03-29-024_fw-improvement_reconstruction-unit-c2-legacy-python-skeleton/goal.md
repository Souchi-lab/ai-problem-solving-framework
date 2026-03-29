# Goal

Run: 2026-03-29-024_fw-improvement_reconstruction-unit-c2-legacy-python-skeleton
Date: 2026-03-29

---

## Goal Readiness Check

- `run-019` で Unit C は legacy landing cleanup planning として切り出されている
- `run-023` で C2 は `src/apsf/legacy/` skeleton 新設として独立単位に定義されている
- `src/apsf/core/` は `run-021` で着地済みであり、legacy 側の受け皿を別系統で作る前提が整っている
- 今回は skeleton 新設のみの小実装 run であり、Python 実装本体の移行や import 修正は行わない

Decision: Proceed

---

## Objective

APSF 再構築の Unit C2 として、
`src/apsf/legacy/` の最小 skeleton を repo 上に着地させる。

今回の run では、
legacy Python 実装群を今後受け止めるための
ディレクトリ構造と最小案内だけを作り、
まだ実装本体は移さない。

---

## Scope

この run で扱うのは次だけである。

1. `src/apsf/legacy/` の新設
2. 最小 package 構造の追加
3. 必要なら package-level README または短い案内の追加
4. C3 以降の実移行を始められる足場づくり

---

## Constraints

### 含めるもの

- `src/apsf/legacy/`
- `src/apsf/legacy/cli/`
- `src/apsf/legacy/orchestration/`
- `src/apsf/legacy/storage/`
- 必要最小限の `__init__.py`
- skeleton 用の短い説明

### 含めないもの

- CLI 実装の移行
- orchestration 実装の移行
- storage 実装の移行
- import 修正
- `providers` / `agents` の legacy landing
- `framework/legacy/` 側の文書移行

### 判断上の制約

- `legacy` を catch-all にしない
- 中身のない過剰階層を増やしすぎない
- C3 のための足場づくり以上のことをしない

---

## Success Criteria

1. `src/apsf/legacy/` が repo 上に実体として着地する
2. `cli` / `orchestration` / `storage` の skeleton が作られる
3. skeleton の役割が短く読める
4. 実装本体や import 修正に踏み込んでいない
5. 次の C3 run がこの skeleton を前提に始められる

---

## Verification

- ディレクトリ構造が存在する
- package として読める最小構成になっている
- 今回の変更が skeleton 作成だけに留まっている

---

## Non-Goals

- Python 実装群の実移行
- import 更新
- `framework/legacy/` 文書 landing
- `planning-patterns.md` / `pipeline.py` の判断

---

## Inputs to Respect

- `runs/fw-improvement/2026-03-29-019_fw-improvement_reconstruction-implementation-planning/result.md`
- `runs/fw-improvement/2026-03-29-023_fw-improvement_reconstruction-unit-c-legacy-landing-planning/result.md`

特に次を守ること。

- C2 は skeleton 新設だけの軽い実装単位である
- C1 と並行可能な粒度に留める
- 実装本体の移行は C3 以降に送る

---

## Desired Landing

この run の着地は、
`src/apsf/legacy/` が repo 上に最小 skeleton として存在し、
次の Python legacy 移行 run が
「どこへ landing させるか」をもう迷わずに始められる状態である。

今回は受け皿を作ることが目的であり、
legacy 実装を動かすことはまだ目的ではない。
