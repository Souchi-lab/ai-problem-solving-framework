# Plan

---

## Goal Readiness Check

- `pipeline.py` の本文を精読した
- Phase 1〜3B の観察結果と参照ドキュメントを確認した
- 判定基準（goal.md の制約）を確認した

Decision: Proceed

---

## pipeline.py 精読結果

### import 構成

```python
from ..core.domain.models import Role, RunContext, StepResult, ExecutionType
from ..core.executors.base import BaseExecutor
from ..core.agents.base import BaseAgent
```

legacy import はゼロ。参照先は全て `..core.*` の抽象契約。

### クラス構成

| 要素 | 内容 |
|---|---|
| `PipelineStep` | dataclass。`role: Role`、`agent: Optional[BaseAgent]` — 全て抽象型 |
| `Pipeline.__init__` | `RunContext` を受け取る。フィールドのみ |
| `Pipeline.add_step` | ビルダーパターン。副作用なし |
| `Pipeline.dry_run` | role/executor マッピングを返す。`print()` なし |
| `Pipeline.run_step` | `step.agent.run(context)` を呼ぶ。抽象インターフェース使用 |
| `Pipeline.run_all` | `print()` + `input()` を含む。CLI 具象依存あり |

### 具象依存の所在

```python
# run_all() 内
print(f"\n[PAUSE]  [{step.name}] Human step — please complete manually.")
print(f"   Workspace: workspaces/{step.role.value}/")
print(f"   Output:    {self._context.run_dir / (step.name + '.md')}")
input("   Press Enter when done...")
```

`input()` は Python stdlib ではあるが、CLI 対話実行を前提とした具象実装である。

### 現在の operational 接続

`cli/main.py` は `ActService` を使っており、`Pipeline` を呼んでいない。
v0.1 スケルトンとして存在するが、現在の実運用フローには接続されていない。

---

## 判定

**legacy**

### 理由

1. **core にしない根拠**：`run_all()` に `print()` + `input()` が存在する。「core 契約しか参照していない」だけで core にしない、という goal.md の制約を適用する。抽象 import だけでは不十分。

2. **hold にしない根拠**：Phase 1〜3B の他の orchestration ファイル（assignment_service / execution_assignment_service / handoff_service / next_instruction_builder / phase_detector / transcript_generator）は全て `legacy/orchestration/` へ移行済みである。`pipeline.py` に特別に保留を続ける理由はなく、同じパッケージに揃えるのが最も honest。

3. **legacy にする根拠**：CLI 具象実装（print/input）を含む、現在は使われていない v0.1 スケルトン、という性質は Phase 1〜3B で `legacy/` に移したファイル群と一致している。v0.1 legacy 実装として `legacy/orchestration/pipeline.py` に着地させるのが自然。

---

## このrunで作成するもの

1. `result.md` — 判定と根拠の要約

### 含めないもの

- 実ファイル移動
- import 修正
- reconstruction 全体 result

---

## Verification Policy

1. 判定が `core / legacy / hold` のいずれかで明示されている
2. 判定理由が structural reading に基づいている
3. Phase 1〜3B の観察と矛盾しない
4. `pipeline.py` の実移動を含んでいない
