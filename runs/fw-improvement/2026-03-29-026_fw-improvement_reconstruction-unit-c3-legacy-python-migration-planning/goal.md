# Goal

Run: 2026-03-29-026_fw-improvement_reconstruction-unit-c3-legacy-python-migration-planning
Date: 2026-03-29

---

## Goal Readiness Check

- `run-019` で Unit C3 は Python 実装移行 planning として切り出されている
- `run-024` により `src/apsf/legacy/` skeleton は着地済みである
- `run-025` により `framework/legacy/` 文書 landing は完了している
- `src/apsf/core/` はすでに着地済みであり、core / legacy の Python 境界を前提に移行順序を考えられる
- 今回は planning-only run であり、実装移行や import 修正は行わない

Decision: Proceed

---

## Objective

APSF 再構築の Unit C3 として、
`src/apsf/legacy/` へ移すべき Python 実装群の
最初の安全な移行順序を定義する。

今回の run では、
legacy 側へ移す実装群を適切な単位に分け、
どこから着手すると安全か、
どの単位は後回しにすべきか、
import 影響をどう読むべきかを planning-only で整理する。

---

## Scope

この run で扱うのは次だけである。

1. legacy Python 実装群の候補整理
2. 最初の移行単位の切り分け
3. 移行順序の定義
4. import 影響の読み方
5. defer すべき重い単位の明示

---

## Constraints

### 含めるもの

- `src/apsf/cli/`
- `src/apsf/orchestration/`
- `src/apsf/storage/`
- 必要に応じて `providers` / `agents` への波及影響の読み

### 含めないもの

- 実ファイル移動
- import 修正
- `pipeline.py` の placement 判定確定
- viewer の再配置
- `framework/` 側文書の追加変更

### 判断上の制約

- `src/apsf/legacy/` を catch-all にしない
- Unit B で着地した `core` 契約を後退させない
- `pipeline.py` は必要なら影響源として読むが、今回無理に placement 確定しない
- 最初の移行単位は「動かしやすさ」だけでなく import 影響の狭さも優先する

---

## Success Criteria

1. 最初の legacy Python 移行単位が 1 つ以上明示される
2. 移行順序に理由がある
3. import 影響の見方が明示される
4. defer すべき重い単位が区別される
5. 次の Codex 実装 run の主語が自然に切れる
6. `pipeline.py` を無理に確定していない

---

## Verification

- 移行候補群と順序が Markdown で読める
- 次の実装 run を 1 本切れるだけの具体性がある
- 保留資産や viewer を巻き込んでいない

---

## Non-Goals

- Python 実装の実移行
- import 修正
- `pipeline.py` の最終判定
- providers / agents の全面再配置
- viewer の再配置

---

## Inputs to Respect

- `runs/fw-improvement/2026-03-29-019_fw-improvement_reconstruction-implementation-planning/result.md`
- `runs/fw-improvement/2026-03-29-023_fw-improvement_reconstruction-unit-c-legacy-landing-planning/result.md`
- `runs/fw-improvement/2026-03-29-024_fw-improvement_reconstruction-unit-c2-legacy-python-skeleton/result.md`
- `runs/fw-improvement/2026-03-29-025_fw-improvement_reconstruction-unit-c1-legacy-docs/result.md`

特に次を守ること。

- `src/apsf/legacy/` は skeleton 済み
- C3 は移行順序の planning に限定する
- 文書 legacy 側はすでに着地済みとみなす

---

## Desired Landing

この run の着地は、
Python legacy 実装群について
「最初にどの単位をどの順で移すか」
が narrow に定義され、
次の Codex 実装 run が
その 1 単位に対してすぐ着手できる状態である。

今回は順序を定義することが目的であり、
重い境界問題をすべて同時に解決することは目的ではない。
