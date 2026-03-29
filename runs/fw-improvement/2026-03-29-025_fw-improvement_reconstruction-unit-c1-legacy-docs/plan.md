# Plan

---

## Goal Readiness Check

- `goal.md` は C1 を `framework/legacy/` 文書 landing に限定している
- `run-022` により `framework/execution-model.md` は legacy 判定済みである
- `run-023` により C1 は Unit C の最初の実装単位として定義されている
- `framework/core/` はすでに着地済みであり、core / legacy の文書境界を repo 上で表現できる
- 今回は framework 文書のみを扱い、Python 実装や import 修正は行わない

Decision: Proceed

---

## Problem Structure

今回の C1 は、
`framework/legacy/` を repo 上に実体化し、
legacy と読むべき framework 文書群を
そこへ自然に landing させる run である。

ここで重要なのは、
legacy 文書を移すことと、
保留資産まで無理に確定することを分けることである。

したがって今回は、
legacy 判定済みの文書と、
run-023 で C1 landing 候補に含めた framework 文書群を対象にし、
root 直下の保留資産は外したまま進める。

---

## Selected Approach

### 基本方針

`framework/legacy/` は、
「現在の stable core ではないが、旧運用の理解や参照のために残す framework 文書」
を受ける場所として作る。

今回の landing は次の 2 層で進める。

- `framework/legacy/` 直下
  - overview / execution-model など、旧運用全体の文脈を持つ文書
- `framework/legacy/{workflow,agents,templates,skills}/`
  - 種別ごとに分かれている既存文書群

### `planning-patterns.md` の扱い

今回除外するのは、
**root 直下の** `framework/planning-patterns.md` である。

一方で、
**skills 配下の** `framework/skills/planning-patterns.md` は
C1 landing 対象として含める。

これにより、
保留資産としての root 文書と、
legacy skill 文書として扱う skills 配下文書を混同しない。

### `framework/overview.md` の扱い

今回の C1 では、
`framework/overview.md` を landing 対象に含める。

理由:

- run-023 の C1 定義で `framework/legacy/overview.md` が含まれている
- `overview.md` は core 定義文書というより、旧 framework 全体の案内文書として読む方が自然
- `execution-model.md` と並べて、legacy 側の入口文書として置くと構造が安定する

### 旧位置導線方針

framework 文書については、
Unit A と同様に旧位置に短いスタブまたは誘導文を残す。

今回の C1 では、
「正本は `framework/legacy/` 側」
「旧位置は誘導」
の関係をはっきりさせる。

---

## Legacy Landing Targets

### 直下 landing 対象

- `framework/execution-model.md`
- `framework/overview.md`

### 種別別 landing 対象

- `framework/workflow/`
- `framework/agents/`
- `framework/templates/`
- `framework/skills/`

ただし、
`framework/skills/` 配下で保留にすべきものが見つかった場合は、
その場で広げずに narrow note として残す。

### 今回の除外対象

- `framework/planning-patterns.md` （root 直下、保留継続）
- `framework/core/` 配下の文書
- `framework/experimental/` 配下の文書

---

## File-Level Plan

### 1. `framework/legacy/` を新設する

最小骨格として次を置く。

- `framework/legacy/README.md`
- `framework/legacy/overview.md`
- `framework/legacy/execution-model.md`
- `framework/legacy/workflow/`
- `framework/legacy/agents/`
- `framework/legacy/templates/`
- `framework/legacy/skills/`

### 2. 直下文書を landing させる

次の 2 文書を `framework/legacy/` 直下へ landing させる。

- `framework/execution-model.md`
- `framework/overview.md`

### 3. 種別別文書群を landing させる

workflow / agents / templates / skills の既存文書群を、
対応する `framework/legacy/` 配下へ移す。

### 4. 旧位置に誘導を残す

旧位置の framework 文書には、
新しい legacy 側正本への最小誘導を残す。

---

## Scope Policy

### 含めるもの

- `framework/legacy/` の新設
- `framework/execution-model.md`
- `framework/overview.md`
- workflow / agents / templates / skills の framework 文書群
- 旧位置誘導

### 含めないもの

- `framework/planning-patterns.md` （root 直下）
- `framework/core/` 側の追加変更
- Python 実装移行
- `src/apsf/legacy/` 側の変更

---

## Execution Steps

### Step 1. `framework/legacy/` の骨格を作る

legacy framework 文書を受ける最小ディレクトリ構造を repo 上に着地させる。

### Step 2. 直下文書を landing させる

`execution-model.md` と `overview.md` を
legacy 側の入口文書として先に置く。

### Step 3. 種別別文書群を landing させる

workflow / agents / templates / skills を
対応ディレクトリへ移す。

### Step 4. 旧位置導線を残す

旧位置から正本への誘導を短く残し、
読み手に急断絶を作らない。

### Step 5. root 保留資産はそのまま残す

`framework/planning-patterns.md` は
今回は動かさず、保留継続とする。

---

## Verification Policy

今回の verification は次の 4 点で十分である。

1. `framework/legacy/` が存在する
2. `execution-model.md` と `overview.md` の landing が読める
3. 文書群が legacy 側に整理されている
4. root 直下の `planning-patterns.md` を巻き込んでいない

---

## Deliverables

- `framework/legacy/` の実体
- `framework/legacy/README.md`
- `framework/legacy/overview.md`
- `framework/legacy/execution-model.md`
- workflow / agents / templates / skills の legacy landing
- 旧位置誘導

これらを `result.md` で Unit C1 完了として閉じる。

---

## Review Policy

今回の C1 は、
対象文書群と除外文書が十分に明確であり、
主語も narrow なので `review.md` は必須にしない。

`result.md` で次を回収すれば十分である。

- `framework/legacy/` が catch-all になっていないか
- `execution-model.md` の legacy 判定が自然に反映されたか
- `overview.md` の legacy landing が妥当か
- root 直下 `planning-patterns.md` を巻き込んでいないか

---

## Expected Landing

この run の着地は、
`framework/legacy/` が repo 上に実体として存在し、
legacy と読むべき framework 文書群が
そこへ整理されている状態である。

また、
`execution-model.md` と `overview.md` が
legacy 側の入口文書として先に landing することで、
その後の C3 planning で
「文書 legacy はすでに着地済み」
として扱える状態を作る。
