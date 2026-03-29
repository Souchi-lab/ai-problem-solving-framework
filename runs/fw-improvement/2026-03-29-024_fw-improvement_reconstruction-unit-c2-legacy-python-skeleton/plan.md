# Plan

---

## Goal Readiness Check

- `goal.md` は C2 を `src/apsf/legacy/` skeleton 新設だけに限定している
- `run-023` で C2 は C1 と並行可能な軽量実装単位として定義されている
- `src/apsf/core/` はすでに着地済みであり、legacy 側の受け皿だけを先に置く前提が成立している
- 今回は実装本体移行や import 修正を行わない

Decision: Proceed

---

## Problem Structure

今回の C2 は、
Python legacy 実装群を今後受け止めるための
最小受け皿を先に作る run である。

ここで重要なのは、
legacy 側の受け皿を作ることと、
legacy 実装群そのものを移すことを分けることである。

したがって今回は、
後続の C3 が迷わず始められるだけの最小 skeleton を置き、
まだ広い階層展開や実装移行には踏み込まない。

---

## Selected Approach

### 基本方針

`src/apsf/legacy/` の skeleton は、
今回の時点では次の 3 本だけを作る。

- `src/apsf/legacy/cli/`
- `src/apsf/legacy/orchestration/`
- `src/apsf/legacy/storage/`

この 3 本は、
run-023 で「最初に移しやすい Python legacy 単位」として読める範囲に対応している。

### 今回まだ作らないもの

次は今回の C2 では作らない。

- `src/apsf/legacy/providers/`
- `src/apsf/legacy/agents/`
- `src/apsf/legacy/config/`
- `src/apsf/legacy/prompts/`

これらは、
C3 で実装群の移行順序を計画するときに、
必要なら追加する。

この判断により、
C2 は「受け皿の最小化」に留まり、
過剰な skeleton 拡張を避けられる。

---

## File-Level Plan

### 1. `src/apsf/legacy/` を新設する

`legacy` Python 実装の landing root として、
`src/apsf/legacy/` を作る。

### 2. 最小 3 ディレクトリを作る

今回作るのは次の 3 つだけである。

- `src/apsf/legacy/cli/`
- `src/apsf/legacy/orchestration/`
- `src/apsf/legacy/storage/`

### 3. package として読める最小構成を入れる

必要最小限の `__init__.py` を置く。

### 4. skeleton の役割を短く残す

`src/apsf/legacy/README.md` または package-level の短い説明で、
この skeleton が C3 以降の受け皿であることを明示する。

---

## Scope Policy

### 含めるもの

- `src/apsf/legacy/`
- `src/apsf/legacy/cli/`
- `src/apsf/legacy/orchestration/`
- `src/apsf/legacy/storage/`
- 最小 `__init__.py`
- skeleton 用の短い説明

### 含めないもの

- Python 実装本体の移行
- import 修正
- `providers` / `agents` / `config` / `prompts` の追加
- `framework/legacy/` 側の文書移行

---

## Execution Steps

### Step 1. `src/apsf/legacy/` を作る

legacy Python landing root を repo 上に着地させる。

### Step 2. 最小 3 ディレクトリを置く

`cli` / `orchestration` / `storage` だけを skeleton として追加する。

### Step 3. 最小 package 構成を入れる

必要な `__init__.py` を置いて、
Python package として自然な形にする。

### Step 4. 役割説明を残す

この skeleton が C3 以降の受け皿であり、
まだ実装本体を含まないことを短く明示する。

---

## Verification Policy

今回の verification は次の 3 点で十分である。

1. `src/apsf/legacy/` が存在する
2. `cli` / `orchestration` / `storage` の 3 本だけが作られている
3. 変更が skeleton 作成以上に広がっていない

---

## Deliverables

- `src/apsf/legacy/`
- `src/apsf/legacy/cli/`
- `src/apsf/legacy/orchestration/`
- `src/apsf/legacy/storage/`
- 最小 `__init__.py`
- skeleton 説明

これらを `result.md` で短く閉じる。

---

## Review Policy

今回の run は小さく、実装内容も定型的であるため、
`review.md` は必須にしない。

`result.md` で次だけ回収すれば十分である。

- skeleton が最小に保たれたか
- 3 本以外へ広がっていないか
- C3 の足場として十分か

---

## Expected Landing

この run の着地は、
`src/apsf/legacy/` が
`cli / orchestration / storage`
の 3 本だけを持つ最小 skeleton として repo 上に着地し、
次の C3 で
「どの Python legacy 実装をどの順で landing させるか」
を迷わず計画できる状態である。

今回は足場だけを作る。
その先の移行判断はまだ持ち込まない。
