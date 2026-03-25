# APSF Viewer Implementation Walkthrough
APSF の運用を強力にサポートする、軽量・高機能な Viewer を実装しました！🎉

## 🌟 実装された主要機能

### 1. 進捗状況の可視化 (Workflow Diagram)
- **Goal → Plan → Build → Review → Result** の 5 ステップで進捗を表示。
- **RE-WORK バッジ**: 差し戻しが発生したステップをひと目で識別可能。

### 2. ラン一覧のディレクトリ表示 (Directory View)
- **グループ化**: 膨大な run を「タクソノミ（work等）」と「日付（YYYY-MM-DD）」で階層的に整理。
- **クイックアクセス**: 最新の実行が常に上に来るようソートされます。

### 3. フェーズ判定の改善 (Legacy Support)
- **判定ロジック強化**: `execution-assignment.md` がない旧バージョン run でも、既存の成果物からフェーズを推定可能。

### 4. 信頼性・操作性の向上 (RX/UX)
- **Custom ConfirmModal**: ブラウザ標準のダイアログを廃止し、Viewer 専用のモーダルを導入。
- **履歴の永続化**: `viewer.db` による実行履歴と差し戻しコメントの管理を統合。
- **Priority System**: `priority-index.yaml` による「Now/Next/Later」の優先順位付けとソート。

---
**統合テストの結果は `docs/integration_test_report.md` を参照してください。**
