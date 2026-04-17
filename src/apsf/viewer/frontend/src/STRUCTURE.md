# Frontend Source Structure

`src/` 直下のフォルダ・ファイルと、それぞれに何が書いてあるかの一覧。

---

## App.tsx（499行）

エントリーポイント兼オーケストレーション層。
**ここには「どの hook を使い、何を props として渡すか」だけを書く。ロジックは各 hook / コンポーネントへ。**

- 全 hook の呼び出し
- 全コンポーネントへの props 接続
- `workspaceTab` / `operatorFilter` 等の UI 状態（どの hook にも属さない軽微なもの）
- `openAgentOSWorkspace` 等、複数 hook をまたぐ複合ハンドラ

---

## types/

| ファイル | 内容 |
|---|---|
| `index.ts` | アプリ全体の型定義 396行。`RunDetail` / `AgentOSInfo` / `OperatorAction` 等 |

---

## utils/

| ファイル | 内容 |
|---|---|
| `formatting.ts` | 表示用文字列変換。`formatElapsedMs` / `parseSatisfiabilityReason` / `prettifyActionId` 等 |
| `artifacts.ts` | アーティファクトの表示メタ情報（タイトル・アイコン等）を返す `getArtifactDisplayMeta` |
| `specialist.ts` | Specialist コード・フィルタリング関連のユーティリティ |
| `markdown.ts` | Markdown パース・整形ユーティリティ |

---

## api/

fetch ラッパー群。各ファイルが 1ドメインを担当。

| ファイル | 内容 |
|---|---|
| `runsApi.ts` | runs 一覧 / run 詳細 / history / operator matrix / recent executions の fetch |
| `autoLoopApi.ts` | auto-loop の status 取得・start / stop / cancel |
| `specialistApi.ts` | specialist 候補取得・confirm・create |
| `configApi.ts` | viewer config の取得・更新 |
| `agentOsApi.ts` | AgentOS 情報取得（run_state / gate_results 等） |

---

## hooks/

カスタム React フック群。各フックが 1 ドメインの state + 操作を管理。

| ファイル | 内容 |
|---|---|
| `useModalState.ts` | モーダル open/close フラグ 9個を一括管理 |
| `useRunList.ts` | runs 一覧 state + `fetchRuns` |
| `useRunDetail.ts` | run 詳細 / history / target 詳細 state + fetch 関数群 |
| `useAgentOS.ts` | AgentOS データ state + `loadAgentOS` / `refreshAgentOS` |
| `useAutoLoop.ts` | auto-loop status + start / stop / cancel mutate |
| `useSpecialists.ts` | specialist 選択モーダルの state + `loadSpecialistCandidates` / `handleConfirmSpecialist` / `handleCreatedSpecialist` |
| `useJudgeChat.ts` | JudgeChat messages state + `sendJudgeChatMessage` / `openJudgeChat` |
| `useRallyConversation.ts` | Rally messages state + `openRallyConversation` |
| `useExecution.ts` | action 実行・コマンド実行・AgentOS アクション実行 + `executingRuns` state |
| `useActionContext.tsx` | action のソート・フィルタリング + `renderOperatorAction` の JSX 生成 |
| `usePeriodicRefresh.ts` | 選択 run の詳細自動リフレッシュタイマー |

---

## components/

### badges.tsx

`PhaseBadge` / `PriorityBadge` / `AssignmentModeBadge` / `CopyButton` 等のバッジ・ユーティリティコンポーネント。

### WorkspaceHeader.tsx（246行）

画面上部のヘッダー。taxonomy セレクタ・lineage（parent/child run 選択）・タブ切替ボタン。

### AppModals.tsx（319行）

アプリ全体のモーダルとトーストを 1 ファイルに集約したコンテナ。
`JudgeChatModal` / `ConfirmModal` / `SpecialistSelectionModal` / `AutoLoopLaunchModal` / `RallyConversationModal` / `CreateSpecialistModal` / `ArtifactReferenceModal` / `ExecutionLogModal` / `LoopStopToast` を条件付きレンダリング。

### modals/

各モーダルコンポーネントの実装ファイル。

| ファイル | 内容 |
|---|---|
| `ConfirmModal.tsx` | 汎用確認ダイアログ（タイトル・メッセージ・ボタン） |
| `SpecialistSelectionModal.tsx` | specialist 候補一覧 + 選択 + 新規作成への導線 |
| `AutoLoopLaunchModal.tsx` | auto-loop 起動設定（build script 等） |
| `RallyConversationModal.tsx` | Rally メッセージ表示・auto-loop 状態表示 |
| `CreateSpecialistModal.tsx` | 新規 specialist 作成フォーム |
| `ViewerConfigModal.tsx` | viewer 設定（execution_mode / cli_tool_mode 等）の編集 |
| `ExecutionLogModal.tsx` | 実行ログの詳細表示 |
| `ArtifactReferenceModal.tsx` | アーティファクトファイルの内容プレビュー |

### panels/

ワークスペース本体の 4タブ。

| ファイル | 行数 | 内容 |
|---|---|---|
| `SidebarPanel.tsx` | 252 | 左サイドバー。run 一覧・フィルタ・taxonomy ピン留め。`filteredRuns` / `taxonomySections` を内部計算 |
| `DetailTab.tsx` | 213 | Detail タブ。Current Target / Topology / Operator Actions 一覧 |
| `ManagementTab.tsx` | 202 | Management タブ。Execution Matrix / Rerun Comment 管理 |
| `ActivityTab.tsx` | 214 | Activity タブ。Recent Executions の一覧表示 |
| `AgentOSTab.tsx` | 312 | Agent OS タブのオーケストレーション。下記 `agentOS/` サブコンポーネントを組み合わせる |

### agentOS/

`AgentOSTab` から切り出した 7 つのサブコンポーネント。

| ファイル | 行数 | 内容 |
|---|---|---|
| `PhaseContextCard.tsx` | 417 | 左カラム。Phase / Judge Advisory / Next Action / Auto-Loop を 1 カードに集約 |
| `AssignmentCard.tsx` | 88 | 中カラム。Agent・Provider/Model・Specialist の現在割り当て + Change ボタン |
| `LastActionCard.tsx` | 54 | 右カラム。最後に実行された AgentOS アクションのサマリー |
| `DetailedAssignmentCard.tsx` | 100 | searchTerm `__show_assignment_details__` で表示される詳細 Assignment カード |
| `AgentOSStateSection.tsx` | 158 | RunState + GateResults + ArtifactManifest + ForceAudit の 4 セクション |
| `RecoverySection.tsx` | 233 | Checkpoints / Snapshots / Apply Trace の選択・Inspect UI |
| `OperatorActionsSection.tsx` | 240 | Capture / Apply ボタン群・最新サマリー・履歴の Operator Actions パネル |

### JudgeChatModal.tsx

AI 相談モーダル。Judge Advisory に連動し、suggested action を Judge Chat 経由で実行できる。

---

## 依存関係の方向（上 → 下が依存元 → 依存先）

```
App.tsx
├── hooks/*          ← state & domain logic
├── api/*            ← fetch wrappers (hooks から呼ばれる)
├── components/panels/*
│   └── components/agentOS/*
├── components/AppModals.tsx
│   └── components/modals/*
├── components/WorkspaceHeader.tsx
├── types/index.ts
└── utils/*
```

ルール: `components` → `hooks` への直接 import は禁止（Props 経由で受け取る）。
`hooks` → `api` は OK。`utils` / `types` はどこからでも import 可。
