# Result

---

## Status

Completed

---

## 読解結果

### import 構成

`pipeline.py` の import は全て `..core.*` のみ。legacy 依存はゼロ。

```python
from ..core.domain.models import Role, RunContext, StepResult, ExecutionType
from ..core.executors.base import BaseExecutor
from ..core.agents.base import BaseAgent
```

### 具象実装の所在

`run_all()` に `print()` + `input()` が存在する。

```python
print(f"\n[PAUSE]  [{step.name}] Human step — please complete manually.")
input("   Press Enter when done...")
```

これは CLI 対話実行を前提とした still-human-operated な具象実装であり、
抽象契約の記述とは異なる層に属する。

### operational 接続状況

現在の `cli/main.py` は `ActService` を使っており、`Pipeline` を呼んでいない。
v0.1 スケルトンとして存在するが、実運用フローには接続されていない。

---

## 判定

**`legacy/orchestration/pipeline.py`**

---

## 判定理由

| 論点 | 内容 |
|---|---|
| core にしない | `run_all()` に `print()` / `input()` がある。import が `core.*` のみでも、具象 CLI 依存がある時点で core 不適格 |
| hold にしない | Phase 1〜3B で他の orchestration ファイル全てを `legacy/orchestration/` へ移行済みであり、今回の読解で「未判断」状態が解消された。hold は「まだ判断できない」の名前であって、判断できた今は使わない |
| legacy にする | print/input を含む v0.1 スケルトン、という性質は Phase 3B で移行した orchestration 群（assignment_service / execution_assignment_service / act_service 等）と同じカテゴリ。揃えるのが最も honest |

---

## Verification チェック

| # | 基準 | 結果 |
|---|---|---|
| 1 | 判定が `core / legacy / hold` のいずれかで明示されている | ✅ legacy |
| 2 | 判定理由が structural reading に基づいている | ✅ |
| 3 | Phase 1〜3B の観察と矛盾しない | ✅ |
| 4 | 実ファイル移動を含んでいない | ✅ |

---

## reconstruction 最終 handoff

この判定により、C3 再構築の主要保留論点が全て解消された。

残る作業：

| 項目 | 内容 |
|---|---|
| `pipeline.py` 実移動 | `legacy/orchestration/pipeline.py` への移動（別 run） |
| reconstruction 全体 result | C3 完了宣言 + 最終状態の記録（別 run） |

どちらも今回の主語の外であり、この run は判定で閉じる。
