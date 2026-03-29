# Plan

---

## Goal Readiness Check

- `goal.md` は Unit A を `framework/core/` + 文書 2 点 + 最小案内接続に固定している
- `run-018` と `run-019` の handoff が揃っている
- 保留資産 `execution-model.md` は明示的に scope 外になっている
- 今回の変更は文書資産に閉じており、コード変更を伴わない

Decision: Proceed

---

## Problem Structure

今回の Unit A は、
`core` の最小実体を repo 上に着地させる最初の実装 run である。

問題は大きく 3 つに分かれる。

1. `framework/core/` をどう立ち上げるか
2. 2 文書をどう移設するか
3. 旧位置からの導線をどう壊さずにつなぐか

この run では、
`legacy` の整理や `core` 文書群の全面確定には進まない。

---

## Selected Approach

### 基本方針

`framework/core/` を新設し、
`operating-model.md` と `responsibility-matrix.md` を
そこで読むのが自然な配置にする。

同時に、
旧位置から新位置への導線が唐突に切れないように、
最小限の案内を残す。

### 実装方式

今回の実装は
`移動または移設相当の整理`
として扱う。

plan 段階では、
`git mv` か内容整理付き再配置かを固定しすぎず、
次を優先する。

- 新しい `core` 入口が自然であること
- 旧位置導線が壊れないこと
- 変更差分が Unit A に閉じること

---

## File-Level Plan

### 1. `framework/core/` を新設する

最低限、次を置ける構造を作る。

- `framework/core/operating-model.md`
- `framework/core/responsibility-matrix.md`

必要なら、
`framework/core/README.md`
または
`framework/README.md` からの導線で
`core` の役割を短く案内する。

### 2. 2 文書を `framework/core/` に着地させる

対象:

- `framework/operating-model.md`
- `framework/responsibility-matrix.md`

今回の観点:

- 文書本文を大きく書き換えない
- まず位置づけを repo 構造として明確化する

### 3. 旧位置の導線を最小限残す

今回の plan では、
旧位置に何も残さない完全断絶は避ける。

したがって、
旧位置から新位置へ短い参照誘導を残す前提で進める。

この判断により、
Success Criteria 4
`legacy 文書群の読みやすさが悪化していない`
を、導線観点で実質的に確認する。

---

## Scope Policy

### 含めるもの

- `framework/core/` の新設
- 文書 2 点の移設
- `core` への最小 README / 案内接続
- 旧位置からの最小参照誘導

### 含めないもの

- `framework/execution-model.md`
- `framework/overview.md`
- `framework/planning-patterns.md`
- `framework/templates/`
- `framework/agents/`
- `framework/legacy/` の新設
- compare material の更新
- `src/apsf/` 配下の変更

---

## Execution Steps

### Step 1. `framework/core/` を作る

`core` 文書の最小着地点として
`framework/core/` を新設する。

### Step 2. 文書 2 点を移設する

対象 2 文書を
`framework/core/` 側へ着地させる。

### Step 3. 旧位置導線を残す

旧位置から新位置へ、
短い参照誘導または案内を残す。

### Step 4. README / 案内接続を最小更新する

`framework/` または `framework/core/` から、
新しい `core` の役割と文書位置が辿れるようにする。

### Step 5. 範囲確認を行う

変更差分が Unit A の範囲に閉じていることを確認する。

---

## Verification Policy

確認観点は次の 4 点で十分とする。

1. ファイル配置
   - `framework/core/` に 2 文書が存在する
2. README / 案内接続
   - `core` の入口が辿れる
3. 旧位置導線
   - 旧位置から見たときに急に意味が切れない
4. 変更範囲
   - Unit A の対象以外を巻き込んでいない

---

## Deliverables

- `framework/core/` の新設
- `operating-model.md` の着地
- `responsibility-matrix.md` の着地
- 最小 README / 案内接続
- 旧位置参照誘導

結果は `result.md` で回収する。

---

## Review Policy

今回は変更範囲が狭く、
確認観点も明確なので、
独立した `review.md` は必須としない。

代わりに `result.md` で次を回収する。

- `core` の最小着地として妥当か
- 旧位置導線が残っているか
- Unit A の範囲に閉じているか
- Unit B へ自然につながるか

---

## Expected Landing

この run の着地は、
repo 上に
`framework/core/`
が実体として現れ、
`operating-model.md`
と
`responsibility-matrix.md`
がそこに着地し、
なおかつ旧位置からの意味が急に切れない状態である。

その結果、
次の Unit B run が
`src/apsf/core/`
を立ち上げるときに、
文書側 `core` がすでに先行している状態を作る。
