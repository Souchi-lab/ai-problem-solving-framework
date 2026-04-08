# APSF Agent Architecture Notes

---

## Summary

APSF が次に採るべきものは、単一 repo の模倣ではなく、機能ごとの最良断面の採用である。

優先度の中心は以下の 5 本:

1. planner artifact / executor artifact の分離
2. session の正本を typed append-only event log にする
3. 実行 checkpoint とファイル snapshot を別レイヤで持つ
4. MCP 前提の tool registry を採用する
5. permission を `操作種別 × 対象範囲 × 承認方式` で管理する

ただし実装順は、GUI や自動化の土台として効く順に並べる。

**推奨順**:

1. event-sourced session core
2. permission matrix engine
3. tool registry + MCP adapter
4. planner-executor artifact spec
5. dual checkpoint prototype

---

## Adopt

### v1.5 で採るもの

- **typed append-only event log を session の正本にする**
  - transcript ではなく typed events を system of record に寄せる
  - permission decision、tool call、tool result、checkpoint を同じ履歴軸で扱う

- **permission matrix を導入する**
  - `read / write / command / network / mcp` の操作種別
  - `workspace / local / global` の対象範囲
  - `allow / ask / deny` の承認方式

- **tool registry + MCP adapter を統一抽象で持つ**
  - 内部ツールと外部 MCP ツールを同じ registry で扱う
  - permission gate は registry の外でなく、実行直前の統一ゲートに置く

### v2 候補

- **planner artifact / executor artifact の厳密分離**
  - `PlanDraft / ApprovedPlan / ExecutionIntent / ExecutionResult` の型設計
  - 既存 APSF は artifact 駆動があるため、session 正本の後でよい

- **dual checkpoint**
  - 実行 checkpoint とファイル snapshot を分離
  - 再開性と巻き戻しを同じ機構で扱わない

- **task/tool lifecycle hooks の公式化**
  - permission、監査、ポリシー注入を hook point に寄せる
  - ただし event / permission / registry の基盤後に導入する

---

## Defer

- orchestrator + subagents の全面導入
- 長期記憶の自動学習化
- remote sandbox / cloud execution
- extension の自動推薦 / 自動有効化
- full-autonomy / YOLO 系モード

これらは有効だが、APSF の現状では境界が広がりすぎる。
まずは session / permission / registry の基盤を先に固める。

---

## Reject

- transcript 中心の状態管理
- モデルの自己判断だけに依存する安全設計
- planner と executor の境界なし設計
- snapshot だけで再開可能性を担保しようとする設計
- provenance 不明 fork / mirror / dump を比較対象に入れること
- 「Claude Code の答え合わせ」を目的にした比較整理

---

## Reference Mapping

| 機能断面 | 主参照 | APSF で採る要点 |
|---|---|---|
| planner / executor 分離 | Aider | architect/editor 的な二段分離を artifact で固定する |
| permission / sandbox | Codex / Cline / Goose | 権限を操作クラスと対象範囲で分ける |
| event log / state | OpenHands | immutable append-only event を正本にする |
| checkpoint | LangGraph | 実行状態の durable checkpoint |
| file snapshot | Cline | ファイル状態の復元・巻き戻し |
| tool registry | Goose | MCP を第一級に扱う registry |
| memory | OpenHands / Goose | short-term と persistent を分離する |

---

## Existing APSF Mapping

| 現在の APSF 資産 | 強み | 次に足すべきもの |
|---|---|---|
| `run_state.json` | phase truth の正本がある | session 全体の typed event log |
| `artifact_manifest.json` | artifact 状態が正本化済み | tool / permission / checkpoint の履歴統合 |
| `force_audit.json` | override 監査がある | permission decision 全般の event 化 |
| `GateService` | gate 評価の単一入口がある | permission matrix と hook の接続 |
| role / phase artifact 境界 | durable artifact の分離が進んでいる | planner / executor artifact spec の厳密化 |

---

## Next Runs

1. **event-sourced session core**
   - `UserMessage / ToolCall / ToolResult / PermissionDecision / CheckpointCreated / MemoryCondensed` を append-only で定義する

2. **permission matrix engine**
   - `操作種別 × 対象範囲 × 承認方式` の evaluator を試作する

3. **tool registry + MCP adapter**
   - 内部ツールと MCP ツールを同一 registry で扱う最小実装

4. **planner-executor artifact spec**
   - `PlanDraft / ApprovedPlan / ExecutionIntent / ExecutionResult` の型を切る

5. **dual checkpoint prototype**
   - 実行 checkpoint とファイル snapshot を分離実装して比較する

---

## Design Notes

- permission と sandbox は別軸で評価する
- session DB / event log / memory store には秘密情報が残る前提で、保持期間・redaction・export 制御を先に決める
- IDE 拡張系と CLI 専用実装は UX が異なるため、権限 UI と isolation 強度を混同しない
