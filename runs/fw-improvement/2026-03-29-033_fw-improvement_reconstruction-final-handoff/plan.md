# Plan

---

## Goal Readiness Check

- run-018〜032 の全 result.md を精読した
- 着地済み / 確定済み / 残り / 次 trigger が整理できる状態にある
- 新しい移行・判定は含めない

Decision: Proceed

---

## result.md の構成方針

### 1. Run 系列サマリー表

run-018〜032 を 1 行ずつ圧縮した対照表。

### 2. 着地済み資産の整理

#### framework/

| 層 | 状態 |
|---|---|
| `framework/core/` | operating-model + responsibility-matrix ✓ |
| `framework/legacy/` | execution-model / overview / workflow / agents / templates / skills ✓ |
| `framework/experimental/` | 現位置維持（変更なし） |
| `framework/improvement-notes/` | docs 層として現位置維持 |
| `framework/planning-patterns.md` | root 直下に残存（判断保留継続） |

#### src/apsf/

| 層 | 状態 |
|---|---|
| `src/apsf/core/` | domain/models + providers/base + agents/base + executors/base ✓ |
| `src/apsf/legacy/` | Phase 1-3B 全完了（storage/providers/config/prompts/executors/orchestration(軽量)/agents/cli + act_service） ✓ |
| `src/apsf/viewer/` | 独立層として現位置維持（変更なし） |
| `pyproject.toml` | entry point = `apsf.legacy.cli.main:app` ✓ |

### 3. 確定した判断の記録

| 判断 | run | 内容 |
|---|---|---|
| `framework/execution-model.md` → legacy | run-022 | v0.1 CLI 運用前提。安定契約は core コードに既着地 |
| `src/apsf/orchestration/pipeline.py` → legacy | run-032 | `run_all()` に print/input。core import のみでも具象 CLI 実装 |
| Python re-export スタブを使わない | run-021/023 | import を直接更新する方針 |
| framework 文書は旧位置導線スタブを残す | run-020/025 | 急な意味断絶を防ぐ |
| viewer は移行対象外 | run-018/023 | 独立サポート層 |

### 4. 未完了（次に切れる個別 run）

| 項目 | 状態 | 次 run 主語 |
|---|---|---|
| `pipeline.py` の実移動 | placement 確定済み・実移動未実施 | legacy/orchestration/ への move + import 修正 + pytest |
| `framework/planning-patterns.md` の扱い | root 直下に保留継続 | 精読 run で legacy 判定（short read run） |

### 5. 次 trigger の固定

2 本に絞る。どちらも小規模・独立。

1. `pipeline.py` 実移動 run
2. `planning-patterns.md` 精読 run（placement 判定のみ、実移動は別 run でもよい）

---

## このrunで作成するもの

- `result.md` のみ

### 含めないもの

- 実ファイル移動
- 新判定
- APSF 全体完了宣言
- GUI / SoChi BLOCKS タスク
