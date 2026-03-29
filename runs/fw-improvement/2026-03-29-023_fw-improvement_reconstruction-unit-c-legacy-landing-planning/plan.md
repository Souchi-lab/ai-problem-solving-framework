# Plan

---

## Goal Readiness Check

- `goal.md` は Unit C を `framework/legacy/` / `src/apsf/legacy/` の受け皿設計に限定している
- `run-020` により `framework/core/` は repo 上の実体として着地済み
- `run-021` により `src/apsf/core/` は repo 上の実体として着地済み
- `run-022` により `framework/execution-model.md` は legacy 判定で確定済み
- `planning-patterns.md` と `pipeline.py` は保留継続が許容されている
- 今回は planning-only run であり、ファイル移動や import 修正は行わない

Decision: Proceed

---

## Problem Structure

Unit A / B によって `core` 側の最小骨格は着地した。
その次に必要なのは、
`core` に入らなかった資産を安全に受け止める `legacy` 側の受け皿設計である。

ただし今回の Unit C は、
legacy 資産を一気に全部移す run ではない。

必要なのは次の 3 点である。

1. `framework/legacy/` と `src/apsf/legacy/` に何を受け止めるか
2. 最初にどの単位から移行できるか
3. 旧位置導線をどう保つか

この run では、
`legacy` を catch-all にせず、
core / legacy / experimental / viewer の境界を壊さない形で、
最小の landing structure を定義する。

---

## Selected Approach

### 基本方針

今回の Unit C では、
legacy 側を次の 2 層に分けて考える。

- `framework/legacy/`
  - 旧運用前提の framework 文書群を受ける
- `src/apsf/legacy/`
  - 旧運用前提の Python 実装群を受ける

この分割により、
文書 legacy とコード legacy を別の責務として扱う。

### legacy の置き方

legacy には「今は core ではないが、履歴や旧運用として残す価値があるもの」を置く。
したがって、単純に未整理資産の箱にはしない。

判断基準は次で固定する。

- 安定契約として残したいものは `core`
- 現行 repo でまだ必要だが、旧運用説明や旧構造に強く依存するものは `legacy`
- 判断保留が妥当なものは無理に landing させない

### 旧位置導線方針

Unit A と同様に、legacy 移行でも旧位置導線を残せるようにする。
ただし Python 側では Unit B と同じく、原則として re-export スタブは使わない。

今回 planning として先に固定するのは次である。

- framework 文書群:
  旧位置スタブまたは短い誘導文を許容
- Python 実装群:
  旧 import 温存ではなく、専用移行 run で import 更新前提

---

## Legacy Landing Structure

### `framework/legacy/`

最小構造は次を基準とする。

- `framework/legacy/README.md`
- `framework/legacy/workflow/`
- `framework/legacy/templates/`
- `framework/legacy/agents/`
- `framework/legacy/skills/`
- `framework/legacy/overview.md`

現時点で確定している最初の legacy 文書候補:

- `framework/execution-model.md`

追加候補:

- workflow / agent / template / skill 系文書群

`planning-patterns.md` は今回は landing 対象に含めない。

### `src/apsf/legacy/`

最小構造は次を基準とする。

- `src/apsf/legacy/__init__.py`
- `src/apsf/legacy/cli/`
- `src/apsf/legacy/orchestration/`
- `src/apsf/legacy/storage/`

初手でいきなり全移行はしない。
まずは「landing を受け止められる構造」だけを定義し、
実移行は専用 run に分ける。

`viewer` は現位置維持であり、`legacy` 受け皿には含めない。

---

## Migration Units

今回の planning では、legacy 側の最小移行単位を次の 3 つに分ける。

### Unit C1. Legacy framework docs landing

対象:

- `framework/execution-model.md`
- workflow/agent/template 系の framework 文書群

役割:

- `framework/legacy/` の実体化
- 文書 legacy の最初の landing

### Unit C2. Legacy Python landing skeleton

対象:

- `src/apsf/legacy/` のディレクトリ構造
- `README` または package-level 説明

役割:

- Python legacy 実装群を今後受け止める足場づくり

### Unit C3. Legacy implementation migration planning

対象:

- CLI / orchestration / storage のうち、最初に移しやすい単位

役割:

- 実移行 run の切り方を確定する

今回の Unit C planning run 自体は、
この 3 単位のうち実行順序と切り分けまでを定義すれば十分である。

---

## Deferred Assets Policy

今回も次は保留継続でよい。

- `framework/planning-patterns.md`
- `src/apsf/orchestration/pipeline.py`

理由:

- `planning-patterns.md` は概念と運用が混在しており、legacy landing planning と同時に決めると論点が増える
- `pipeline.py` はコード読解と orchestration 境界判断を伴い、Unit C の受け皿設計からは一段重い

したがって、今回は「legacy 側の骨格を固める」ことを優先し、
この 2 点は次段で別判断とする。

---

## Execution Steps

### Step 1. `framework/legacy/` の最小 landing structure を定義する

文書 legacy を受けるための最小ディレクトリ構造と、
最初に landing させる候補を定義する。

### Step 2. `src/apsf/legacy/` の最小 landing structure を定義する

Python legacy 実装を受けるための最小ディレクトリ構造だけを定義する。

### Step 3. 最初の legacy 移行単位を切る

`framework/execution-model.md` を含む文書 legacy 単位と、
Python legacy 側の skeleton 単位を分けて扱う。

### Step 4. 旧位置導線方針を固定する

framework 文書では旧位置誘導を許容し、
Python では import 温存を避ける方針を再確認する。

### Step 5. Deferred assets を明示したまま handoff で閉じる

`planning-patterns.md` と `pipeline.py` を無理に決めず、
次の run に渡す open item として残す。

---

## Verification Policy

今回の verification は planning の妥当性確認で十分である。

確認点は次の 4 つに絞る。

1. `framework/legacy/` の骨格が読める
2. `src/apsf/legacy/` の骨格が読める
3. 最初の legacy 移行 run の主語が切れている
4. 保留 2 点を無理に解決していない

---

## Deliverables

- `framework/legacy/` landing structure proposal
- `src/apsf/legacy/` landing structure proposal
- legacy migration units (`C1 / C2 / C3`)
- old-location guidance policy
- deferred assets note

これらを `result.md` で handoff 可能な形にまとめる。

---

## Review Policy

今回の Unit C は planning-only であり、
主語も narrow に保てているため、
`review.md` は必須にしない。

代わりに `result.md` で次を回収する。

- legacy が catch-all になっていないか
- `execution-model.md` legacy 判定が自然に反映されているか
- `planning-patterns.md` / `pipeline.py` の保留が保たれているか
- 次の実装 run の入口として十分か

---

## Expected Landing

この run の着地は、
`framework/legacy/` と `src/apsf/legacy/` の受け皿構造が planning 上で固まり、
次の run が
「まず `framework/legacy/` を実体化して文書 legacy を着地させる」
または
「まず `src/apsf/legacy/` の skeleton を作る」
のどちらから始めるかを迷わず切れる状態である。

今回必要なのは、
legacy 側を narrow に整理して受け皿を作ることであり、
保留資産のすべてを同時に処理することではない。
