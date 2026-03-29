# Result

---

## Status

Completed

---

## Initial Migration Unit Proposal

### Unit A: Framework Core Docs

**対象**:

| ファイル | 現パス | 移行後パス |
|---|---|---|
| `operating-model.md` | `framework/operating-model.md` | `framework/core/operating-model.md` |
| `responsibility-matrix.md` | `framework/responsibility-matrix.md` | `framework/core/responsibility-matrix.md` |

**作業内容**:

1. `framework/core/` ディレクトリを新設する
2. 上記 2 ファイルを `framework/core/` に移動する
3. 参照が壊れる箇所があれば最小限のリンク更新を行う（runs/ 内 result.md からの参照など）
4. `framework/core/README.md` を 5〜8 行で新設する（「このディレクトリは安定契約を置く場所」の 1 行説明 + ファイルリスト）

**除外**:

- `framework/execution-model.md` — 迷い資産。精読後に core/legacy を決定する
- `framework/overview.md` — extraction source として保持
- `framework/planning-patterns.md` — 迷い資産
- `framework/templates/`, `framework/agents/` — legacy 群；Unit A では触らない

---

### Unit B: Python Core Contracts

**対象**:

| ファイル | 現パス | 移行後パス |
|---|---|---|
| `domain/models.py` | `src/apsf/domain/models.py` | `src/apsf/core/domain/models.py` |
| `providers/base.py` | `src/apsf/providers/base.py` | `src/apsf/core/providers/base.py` |
| `agents/base.py` | `src/apsf/agents/base.py` | `src/apsf/core/agents/base.py` |
| `executors/base.py` | `src/apsf/executors/base.py` | `src/apsf/core/executors/base.py` |

**作業内容**:

1. `src/apsf/core/` ディレクトリを新設し、`__init__.py` を配置する
2. 上記 4 ファイルを `src/apsf/core/` 以下に移動する（サブディレクトリ構造を維持）
3. 移動後の import パスを列挙し、影響箇所を特定する（変更は Unit B 内で完結させる）
4. `pytest tests/` を通す（または差分を記録する）

**import 影響の確認対象**（Unit B で列挙・修正する範囲）:

- `src/apsf/agents/{planner,builder,critic,judge,junior_builder}.py` → `base.py` を参照している
- `src/apsf/providers/{anthropic,openai,gemini}_provider.py` → `base.py` を参照している
- `src/apsf/executors/{api,cli,human}_executor.py` → `base.py` を参照している
- `src/apsf/orchestration/` 各ファイル → `domain/models.py` を参照している
- `src/apsf/__init__.py` — 再 export があれば確認

**除外**:

- provider 実装本体の移動
- orchestration / storage / CLI / viewer の移動
- `src/apsf/viewer/*` — 現位置維持

---

### Unit C: Legacy Landing Cleanup Planning

**位置づけ**: Unit A / B 完了後に定義する計画単位。今回は「どこを legacy に寄せるか」の設計を行うが、実ファイル移動は Unit C 専用の implementation run に委ねる。

**計画内容**（Unit C の implementation run への引き渡し材料）:

- `framework/legacy/` を新設し、以下を格納する設計
  - `framework/legacy/workflow/`（v0.1.md, v0.2.md）
  - `framework/legacy/agents/`（planners/, critics/ を含む）
  - `framework/legacy/templates/`
  - `framework/legacy/skills/`
  - `framework/legacy/overview.md`（extraction source として）
- `src/apsf/legacy/` を新設し、以下を格納する設計
  - `src/apsf/legacy/providers/`
  - `src/apsf/legacy/agents/`
  - `src/apsf/legacy/orchestration/`
  - `src/apsf/legacy/cli/`
  - `src/apsf/legacy/storage/`
  - `src/apsf/legacy/config/`
  - `src/apsf/legacy/prompts/`
- `legacy` は削除候補でなく「現行の動作形状の読める写し」として扱う（Minor Revision 4）

**除外**:

- 実ファイル移動（Unit C 専用 run の仕事）
- legacy retirement の決定
- 迷い資産の最終決着

---

## Implementation Order

```
Unit A → Unit B → Unit C
```

**理由**:

Unit A は import 影響がなく、repo 上に `core/` が可視化される最小変更であるため先行する。Unit B はコード側の `core/` 骨格を立ち上げるが、import 修正が必要なため Unit A 完了後に着手する方が変更スコープが読みやすい。Unit C は Unit A/B の結果を踏まえて `legacy/` 受け皿を設計するため、両者の完了後でないと設計がぶれやすい。

---

## Deferred Assets

次の資産は初手から外し、状態を以下のとおり記録する。

| 資産 | 理由 | 次の扱い |
|---|---|---|
| `framework/execution-model.md` | 迷い資産。抽象定義と現行 CLI 説明が混在している可能性がある | 精読後に `core` または `legacy` を確定する。Unit A 完了後に単独精読タスクとして扱う |
| `framework/planning-patterns.md` | 再利用可能 guidance と current operational advice が混線 | Unit C 後に抽出可能性を判断する |
| `src/apsf/orchestration/pipeline.py` | legacy 実装だが将来の core 抽出余地がある | Unit B 後に精読し、抽出判断を行う |
| `src/apsf/storage/*` | contract 抽出を伴う可能性があり、初手の安全単位ではない | Unit C 以降に判断する |
| `src/apsf/viewer/*` | 独立サポート層として現位置維持が合意済み | 移行判断は行わない |
| `framework/experimental/redesign/` | 現位置維持。再設計ドラフトとして readable に保つ | 移行対象外 |

---

## Handoff Validation

この result が次の Codex implementation run の `plan.md` に転用できるかを以下で確認する。

| 観点 | 状態 |
|---|---|
| 最初の移行単位が 1〜3 単位に絞られているか | ✅ Unit A / B / C の 3 単位 |
| 各単位に対象ファイル群と非対象範囲があるか | ✅ 各単位に明示 |
| 順序づけに理由が 1 段落で説明されているか | ✅ Implementation Order セクション |
| 迷い資産 3 点を初手から外す理由が明記されているか | ✅ Deferred Assets セクション |
| 検証方法が定義されているか | ✅ Unit B で `pytest` + import 影響列挙を明示 |
| Codex がそのまま implementation run に移れる粒度か | ✅ 各 Unit に作業内容ステップを記載 |
| 出力全体が implementation-planning に留まっているか | ✅ 実ファイル移動は含まない |

---

## Next Trigger

**Unit A 実装 run（Codex）**

- `framework/core/` 新設
- `operating-model.md` + `responsibility-matrix.md` の移動
- `framework/core/README.md` 新設

Unit A 完了後:

- `framework/execution-model.md` 精読タスク（短い確認 run）を挟んでから Unit B へ、または Unit B を先行させて execution-model.md を後回しにする
- どちらを選ぶかは Unit A 実装 run の result.md で Codex が判断する

---

## What This Run Decided

- 最初の移行単位: Unit A（2 文書）→ Unit B（4 Python ファイル）→ Unit C（legacy landing 設計）
- 実装順序と理由
- 各単位のリスク境界と除外範囲
- 迷い資産 3 点の保留と次の扱い
- Unit B の import 影響確認対象の列挙

## What This Run Did Not Decide

- `framework/execution-model.md` の最終分類（core / legacy）
- `framework/planning-patterns.md` の core 昇格可否
- `src/apsf/orchestration/pipeline.py` の core 抽出可否
- Unit C の具体的な実装ステップ（Unit A / B 後に定義）
- legacy retirement 条件
