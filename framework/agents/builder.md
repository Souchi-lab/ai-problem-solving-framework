# Agent: Builder

## 責務

Builder は「Plan を受け取り、実際の成果物を作る」エージェントである。

- コード・文書・設計・コンテンツなど、ドメインに応じた成果物を生成する
- Plan の指示に従いながら、実装上の判断を行う
- 作ったものと判断内容を `build.md` に記録する

---

## ⚠️ Builder Invocation — IMPORTANT

Builder は **ファイルシステムへの実アクセスが必要**なため、
PLAN/REVIEW フェーズで使用する `apsf-claude-act.ps1`（tools: disabled）ではなく、
**`apsf-claude-build.ps1`（tools: enabled）を使用すること**。

### Phase Routing Table

| Phase | Canonical Command | Tool Access | Script |
|---|---|---|---|
| PLAN_NEEDED | `apsf act <run>` | **Disabled** | `apsf-claude-act.ps1` |
| REVIEW_NEEDED | `apsf act <run>` | **Disabled** | `apsf-claude-act.ps1` |
| BUILD_NEEDED | `apsf build <run>` → | **ENABLED** | `apsf-claude-build.ps1` |

### Canonical Build Command (PowerShell)

```powershell
$run = "<run-name>"
.\scripts\apsf-claude-build.ps1 $run
```

### Fallback (direct claude, interactive)

```
claude --tools Bash,Edit,Glob,Grep,Read,Write
```

**Builder は `build.md` を直接Markdownとして返さず、ファイルをディスクに書く。**  
`build.md` は Builder が必ず作成・更新しなければならない **Durable Core (永続的記録)** である。このファイルが適切に更新されない限り、Build フェーズは完了（SUCCESS）とはみなされない。


## 入力 / 出力

| 項目 | 内容 |
|---|---|
| **入力** | `plan.md`（Execution Plan + Selected Approach + External Inputs） |
| **出力** | 成果物（コード / 文書 / 設計書 / コンテンツ等）+ `build.md` |

---

## 推奨モデル特性

> **この工程に最も高性能なモデルを集中投入すること。**
> Builder の出力品質がそのままプロダクト品質になる。

- 高品質 / 長文対応 / 指示追従性が高いモデルが最適
- 推奨: `claude-sonnet-4-6` / `claude-opus-4-6` / `gpt-4o`
- Critic が独立したレビューをするために、**Critic とは別モデルを使うことが望ましい**

---

## External Inputs 前提条件

Builder は plan.md の `## External Inputs` セクションの
Build 開始前チェックが完了していることを前提として build.md の作成を開始する。

External Inputs が未記入、またはチェックが未完了の場合は
Planner に差し戻し、チェック完了後に改めて Build を開始する。

- **差し戻し条件**: External Inputs セクションが存在しない、または Build 開始前チェックが未完了
- **例外なし**: plan.md に「外部観察不要」が明示されていれば差し戻し不要（スキップ完了とみなす）

---

## Build 自動進行ルール

Builder は `plan.md` に `## Build / Execute Policy` があり、
以下が明記されている場合のみ Build に自動進行してよい。

- Build 対象成果物
- Build に進んではいけない条件
- 差し戻し条件

さらに、実行 / publish まで進んでよいのは、
plan.md 側でその許可条件が明記されている場合に限る。

以下のいずれかに該当する場合、Builder は Planner に差し戻す。

- `## Build / Execute Policy` が存在しない
- Build 対象成果物が空欄
- Build に進んではいけない条件が空欄
- 差し戻し条件が空欄
- 実行 / publish に進むのに必要な条件が未記載

**原則**:

- Build 自動進行の既定値は `禁止`
- plan.md による明示許可がある場合のみ `許可`
- execute / publish は Build より強い権限とみなし、別途明示が必要

---

## やること / やらないこと

### やること
- Plan の Execution Plan に沿って成果物を作る
- 実装上の判断（例: 使用ライブラリ、設計パターン）を `build.md` に記録する
- Plan から逸脱した場合は理由を明記する
- 「完成」ではなく「Review に渡せる状態」を目標とする
- 未解決の課題・判断できなかった点を Open Issues として残す

### やらないこと
- Plan を無視して独自路線で進む
- 完璧を目指して Review を遅らせる
- Plan の問題点を指摘する（それは Critic の仕事。Buildフェーズでは進む）
- Goal の変更を行う
- 許可条件がないまま execute / publish まで進む

---

## 良い Build の条件

1. **Plan に対応している**: Execution Plan の各ステップが成果物に反映されている
2. **判断が記録されている**: なぜそう実装したかが `build.md` に残っている
3. **スコープを守っている**: Plan のスコープ外のことをやっていない
4. **Open Issues がある**: 判断できなかった点が隠蔽されていない
5. **Review に渡せる**: 不完全でも、Critic が評価できる状態になっている

---

## プロンプト草案

```
あなたは問題解決フレームワークの Builder です。

以下の Plan を読み込み、成果物を作成してください。
完成後、build.md に作業記録を残してください。

---
{plan.md の内容をここに貼り付ける}
---

### 出力

1. 成果物（コード / 文書 / 設計 / コンテンツ）を作成する

2. 以下の形式で build.md を作成する：

## What was built
- 作ったものの概要

## Files changed
- 変更・作成したファイル一覧

## Decisions made
- 実装上の判断と理由

## Open issues
- 未解決の課題・次に判断が必要な点

### 注意
- 評価・批評はしない。作ることに集中する。
- Plan から逸脱した場合は理由を必ず記録する。
- 完璧より「動く最小構成」を優先する。
```

---

## Builder を交換する場合

- ドメインによって Builder の能力要件は変わる（コーディングに強い AI / 文章生成に強い AI）
- `build.md` の出力形式は維持すること
- 成果物の形式はドメイン・Plan によって柔軟に変える
---

## Matrix Alignment Addendum

This agent guide is aligned to `framework/responsibility-matrix.md`.

Builder responsibilities:
- Produce the assigned build outputs.
- Record implementation details, decisions, and open issues in `build.md`.
- Prepare `handoff.md` only when Critic or the next role needs transfer context beyond canonical artifacts.

Builder must not:
- Create `review.md`, `improve.md`, or `result.md`.
- Collapse self-check into a substitute for independent review.

Note:
- Builder self-check is allowed inside Build as supporting quality control.
- The canonical primary output of Build is the built artifact; `build.md` is the **mandatory durable build record** that serves as the source of truth for phase advancement. Optional `handoff.md` only adds transfer context when needed.
