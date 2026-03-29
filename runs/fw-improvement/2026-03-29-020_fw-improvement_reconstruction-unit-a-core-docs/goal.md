# Goal

Run: 2026-03-29-020_fw-improvement_reconstruction-unit-a-core-docs
Date: 2026-03-29

---

## Goal Readiness Check

- `run-018` で資産分類と directory mapping が確定済み
- `run-019` で Unit A / B / C の移行順序が確定済み
- Unit A は `framework/core/` の文書 2 点に限定されている
- `execution-model.md` は保留資産として初手から外れている
- 今回は design-only ではなく、小規模実装 run である

Decision: Proceed

---

## Objective

APSF 再構築の最初の実装単位として、
`framework/core/` を新設し、
次の 2 文書を安全に移行する。

- `framework/operating-model.md`
- `framework/responsibility-matrix.md`

あわせて、
この新しい `core` 入口が repo 上で読めるように、
必要最小限の README / 案内接続を加える。

今回の run の目的は、
`core` の思想全体を完成させることではなく、
最小の `core` 文書単位を repo に着地させることにある。

---

## Scope

この run で実施してよいこと:

1. `framework/core/` ディレクトリの新設
2. 以下 2 文書の移動または移設相当の整理
   - `framework/operating-model.md`
   - `framework/responsibility-matrix.md`
3. `framework/` または `framework/core/` の README / 案内接続の最小更新
4. 必要なら旧位置から新位置への参照誘導

---

## Constraints

### 今回含めるもの

- 文書 2 点のみ
- `framework/core/` の最小受け皿
- README / index の最小接続

### 今回含めないもの

- `framework/execution-model.md`
- `framework/overview.md`
- `framework/planning-patterns.md`
- `framework/templates/`
- `framework/agents/`
- `src/apsf/` 配下のコード変更
- compare material の追加更新
- `legacy` 全体の整理

### 実装原則

- 変更は Unit A に閉じる
- `legacy` の readable 性を壊さない
- 旧位置の意味が急に失われないようにする
- README 接続は最小限に留める

---

## Success Criteria

1. `framework/core/` が新設されている
2. `operating-model.md` と `responsibility-matrix.md` が `framework/core/` に収まっている
3. `framework/` 側から新しい `core` 位置が辿れる
4. `legacy` 文書群の読みやすさが悪化していない
5. 保留資産が巻き込まれていない
6. 変更が Unit A の範囲に閉じている
7. 次の Unit B 実装 run に自然につなげられる

---

## Verification

- ファイル配置の確認
- README / 案内接続の確認
- 旧位置に依存する文書導線が極端に壊れていないことの確認
- 変更差分が Unit A の 2 文書 + 最小案内接続に留まっていることの確認

---

## Non-Goals

- `core` 文書群の全面確定
- `execution-model.md` の処遇決定
- `legacy` 整理の開始
- `src/apsf/core/` のコード移行
- import / path / pytest を伴うコード変更

---

## Inputs to Respect

- `runs/fw-improvement/2026-03-28-018_fw-improvement_reconstruction-asset-classification/result.md`
- `runs/fw-improvement/2026-03-29-019_fw-improvement_reconstruction-implementation-planning/result.md`
- `framework/experimental/redesign/plan.md`
- `framework/experimental/redesign/result.md`

特に次を守ること。

- Unit A は明確 `core` 文書 2 点に限定
- `execution-model.md` は保留
- `legacy` は readable に保つ

---

## Desired Landing

この run の着地は、
repo 上に
`framework/core/`
が初めて実体として現れ、
最小の `core` 文書 2 点がそこに着地した状態である。

理想形は、
次の Unit B run が
`src/apsf/core/`
を作るときに、
文書側の `core` がすでに先行着地していることである。
