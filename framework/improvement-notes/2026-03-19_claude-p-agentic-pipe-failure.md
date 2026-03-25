# FW Improvement Note

Date: 2026-03-19
Theme: `claude -p` がアジェンティックモードで起動し APSF パイプが不成立になるケース
Scope: CLI pipe 設計 / `claude -p` 互換性 / wrapper

---

## 観察した事象

run-022 の BUILD_NEEDED フェーズで `apsf-claude-act.ps1` を実行したところ、`claude -p` が stdout にテキストを出力せず、代わりにファイル書き込み許可を対話的に要求した。

```
Write access isn't allowed yet. Could you grant write access to these files...
- framework/agents/planner.md
- framework/templates/plan.md
- runs/_template/plan.md
- (build.md — new file in the current run folder)
```

`apsf write-phase --stdin` はこの出力を「空 or テンプレートのみ」と判定し、保存せずに exit=1 で終了した。

---

## 既知記録との差分

`framework/cli-orchestrator.md` の `claude -p` 評価（2026-03-17）では以下を確認済み：

- **Claude Code セッション内からは不可**（nested session ブロック）
- 通常 PowerShell（pwsh）では 3 phase 完走確認済み

今回は **通常の PowerShell（Claude Code セッション外）** での実行にもかかわらずアジェンティック動作が発生した。plan.md の生成（-UntilPlan）は同じ環境で成功していたため、フェーズや prompt の内容によって挙動が変わる可能性がある。

---

## 仮説

- BUILD_NEEDED フェーズの prompt が「成果物を作れ」という指示を含むため、`claude -p` がツール使用を起動する確率が上がる
- PLAN_NEEDED フェーズの prompt（plan.md を書く）より BUILD_NEEDED フェーズの prompt（ファイルを変更する）の方がアジェンティック判定されやすい
- `claude -p` の `-p` フラグが non-interactive を保証するものではなく、プロンプト内容によってアジェンティック動作にフォールバックする

---

## 影響

- `apsf-claude-act.ps1` の BUILD_NEEDED フェーズが不安定
- `llm` CLI または Claude Code（直接実行）へのフォールバックが必要

---

## 改善候補

1. **wrapper でフォールバック検出を追加**: `claude -p` の出力が空 or 許可要求パターンを含む場合、`[Warn] claude -p behaved agentically. Fallback to llm?` を表示して停止する
2. **BUILD フェーズは `llm` を推奨に格上げ**: `cli-orchestrator.md` の互換表で BUILD フェーズの `claude -p` を △ → ❌ に変更し、`llm` を標準とする
3. **prompt の agentic トリガー抑制**: `apsf act` が BUILD フェーズの prompt 末尾に「ファイルを直接書かず stdout にテキストのみ出力せよ」という制約文を自動付与する

---

## 関連ファイル

- `framework/cli-orchestrator.md`（`claude -p` 評価セクション）
- `scripts/apsf-claude-act.ps1`
- `src/apsf/prompts/renderer.py`（prompt 生成）
