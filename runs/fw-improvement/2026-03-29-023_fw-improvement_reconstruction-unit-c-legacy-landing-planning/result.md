# Result

---

## Status

Completed

---

## Output 1 — `framework/legacy/` Landing Structure Proposal

### 最小 directory structure

```
framework/legacy/
  README.md
  workflow/
    v0.1.md
    v0.2.md
  agents/
    planner.md
    builder.md
    critic.md
    judge.md
    junior-builder.md
    planners/
    critics/
  templates/
    (全 template ファイル群)
  skills/
    planning-patterns.md
  execution-model.md
  overview.md
```

### README の役割

`framework/legacy/README.md` は次の内容を 5〜8 行で記述する。

- このディレクトリは「現行 APSF が動作するために必要な現行運用形状」を保持する
- `core/` に入らなかった、CLI フロー・テンプレート・agent role 文書など
- 削除候補ではなく、readable な現行運用の写しとして維持する
- `framework/core/` との関係（`core` が契約、`legacy` が実装形状）

### 旧位置導線方針（framework 文書）

Unit A と同様に、旧位置に短い誘導スタブを残す。

例:
```
> この文書は framework/legacy/ に移動しました。
> 正本: [framework/legacy/execution-model.md](legacy/execution-model.md)
```

---

## Output 2 — `src/apsf/legacy/` Landing Structure Proposal

### 最小 directory structure（skeleton）

```
src/apsf/legacy/
  __init__.py
  README.md
  cli/
  orchestration/
  storage/
  providers/
  agents/
  config/
  prompts/
```

Unit C2 では上記の **骨格（空ディレクトリ + `__init__.py`）だけを作る**。実ファイルの移動は Unit C3 以降の専用 run に委ねる。

### README の役割

`src/apsf/legacy/README.md` は次の内容を記述する。

- このパッケージは「現行 APSF の実装形状」を保持する
- `src/apsf/core/` が安定契約（ABC / domain model）、`src/apsf/legacy/` が現行実装
- 削除候補ではなく、現行 CLI / orchestration / storage が動く状態を保つ
- viewer は `src/apsf/viewer/` のまま維持（このパッケージには含まない）

### 旧位置導線方針（Python 実装）

Unit B と同じく、Python 側では re-export スタブを使わない。実移行 run でファイルを移動するときに import を直接更新する。

---

## Output 3 — Legacy Migration Units (C1 / C2 / C3)

### Unit C1: Framework legacy docs landing

**役割**: `framework/legacy/` を実体化し、文書 legacy の最初の着地を完成させる

**対象**:

| ファイル | 移行先 |
|---|---|
| `framework/execution-model.md` | `framework/legacy/execution-model.md` |
| `framework/overview.md` | `framework/legacy/overview.md` |
| `framework/workflow/v0.1.md` | `framework/legacy/workflow/v0.1.md` |
| `framework/workflow/v0.2.md` | `framework/legacy/workflow/v0.2.md` |
| `framework/agents/` 全体 | `framework/legacy/agents/`（サブ構造維持） |
| `framework/templates/` 全体 | `framework/legacy/templates/`（ファイル構造維持） |
| `framework/skills/planning-patterns.md` | `framework/legacy/skills/planning-patterns.md` |

**除外**（Unit C1 では触らない）:

- `framework/planning-patterns.md` — 保留継続
- `framework/core/` — 変更なし
- `framework/experimental/` — 変更なし
- `framework/improvement-notes/` — docs 層として現位置維持

**旧位置処理**: 移動後、旧位置に導線スタブを残す（Unit A と同方式）

---

### Unit C2: Python legacy skeleton

**役割**: `src/apsf/legacy/` の骨格を作り、Python legacy 実装を将来受け止める足場にする

**作業**:

- `src/apsf/legacy/` ディレクトリを新設
- 各サブディレクトリに `__init__.py` を配置（空でよい）
- `src/apsf/legacy/README.md` を新設
- 実ファイルの移動は **行わない**

---

### Unit C3: Python legacy implementation migration planning

**役割**: Python 実装群の実移行単位と順序を定義する専用計画 run

**対象の検討範囲**:

- `src/apsf/cli/` → `src/apsf/legacy/cli/`
- `src/apsf/orchestration/` → `src/apsf/legacy/orchestration/`
- `src/apsf/storage/` → `src/apsf/legacy/storage/`
- `src/apsf/providers/{anthropic,openai,gemini}_provider.py` → `src/apsf/legacy/providers/`
- `src/apsf/agents/{planner,builder,critic,judge,junior_builder}.py` → `src/apsf/legacy/agents/`
- `src/apsf/config/` → `src/apsf/legacy/config/`
- `src/apsf/prompts/` → `src/apsf/legacy/prompts/`

**Unit C3 では実移行は行わない**。import 影響の全列挙と移行順序を確定する。

---

## Deferred Assets Policy（保留継続）

| 資産 | 理由 | 次の扱い |
|---|---|---|
| `framework/planning-patterns.md` | 概念と運用が混在。legacy landing と同時に決めると論点が増える | Unit C1 完了後に単独精読 run |
| `src/apsf/orchestration/pipeline.py` | コード読解と orchestration 境界判断を伴う。Unit C3 の planning 前後に判断 | Unit C3 planning run の中で扱う |

---

## Old-location Guidance Policy

| 資産種別 | 方針 |
|---|---|
| framework 文書（Unit C1） | 旧位置に導線スタブを残す。急な意味断絶を避ける |
| Python 実装（Unit C2/C3） | re-export スタブは使わない。実移行 run で import を直接更新 |

---

## Success Criteria 照合

| # | 基準 | 結果 |
|---|---|---|
| 1 | `framework/legacy/` の最小 structure 方針が定義される | ✅ |
| 2 | `src/apsf/legacy/` の最小 structure 方針が定義される | ✅ |
| 3 | 最初に移せる legacy 単位が 1 つ以上明示される | ✅ Unit C1（framework docs） |
| 4 | 旧位置導線の扱いが方針として定義される | ✅ 文書=スタブあり、Python=直接更新 |
| 5 | `execution-model.md` の legacy landing が自然に接続される | ✅ Unit C1 の先頭候補 |
| 6 | `planning-patterns.md` / `pipeline.py` を無理に決めずに済んでいる | ✅ 保留継続 |
| 7 | 次の Codex 実装 run の入口になる | ✅ C1/C2/C3 の主語が切れている |

---

## Next Triggers

**Unit C1 実装 run（Codex）**

- `framework/legacy/` + `README.md` を新設
- 確定 7 種の文書を legacy へ移設
- 旧位置に導線スタブを追加

**Unit C2 実装 run（Codex）**（C1 と並行可能）

- `src/apsf/legacy/` + 各 `__init__.py` を新設
- `src/apsf/legacy/README.md` を新設
- ファイル移動なし

**Unit C3 計画 run**（C1/C2 完了後）

- Python 実装群の移行順序・import 影響を定義

**保留単独処理**（任意タイミング）

- `framework/planning-patterns.md` 精読 run
