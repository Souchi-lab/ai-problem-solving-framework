# APSF Viewer Specification

APSF Viewer は、APSF フレームワークの実行状態と成果物をブラウザ上で可視化・確認するためのリードオンリー GUI ツールです。

## 1. 機能要件

### 1.1 実行リスト管理
- **一覧表示**: `runs/` ディレクトリ内の全実行（子要素含む）を表示します。
- **検索**: 実行名（ディレクトリ名）による部分一致検索。
- **フィルタ**: フェーズ（`PLAN_NEEDED`, `REVIEW_NEEDED` 等）による絞り込み。
- **メタデータ**: 直近の更新日時、タクソノミ（`work`, `fw-improvement` 等）の表示。

### 1.2 進捗可視化（Workflow Diagram）
以下の 5 ステージで進捗を可視化します：
1. **GOAL**: `goal.md` の存在
2. **PLAN**: `plan.md`, `plan_review.md`
3. **BUILD**: `build.md`, `build_review.md`
4. **REVIEW**: `review.md`, `review_review.md`
5. **RESULT**: `result.md`, `improve_review.md`

- **フェーズマッピング**: 
    - `PLAN_NEEDED` → GOAL 完了, PLAN 進行中
    - `BUILD_NEEDED` → PLAN 完了, BUILD 進行中
    - `REVIEW_NEEDED` / `IMPROVE_NEEDED` → BUILD 完了, REVIEW 進行中
    - `RESULT_NEEDED` → REVIEW 完了, RESULT 進行中 (Judge)
    - `COMPLETE` / `TRANSCRIPT_RECOMMENDED` → 全て完了

### 1.3 差し戻し（RE-WORK）検知
特定のレビュー成果物が存在する場合、該当ステップに `REWORK` バッジを表示します：
- `plan_review.md` → PLAN ステップ
- `build_review.md` → BUILD ステップ
- `review_review.md` → REVIEW ステップ
- `improve_review.md` → RESULT ステップ

### 1.4 アーティファクトプレビュー
- **Markdown レンダリング**: `react-markdown` + `remark-gfm` + `@tailwindcss/typography`。
- **プレビュー内容**: 見出し、強調、リスト、表（テーブル）、コードブロック等の正式なレンダリング。
- **階層対応**: 子孫ディレクトリにある実行のアーティファクトも正しく取得。

### 1.6 トランスクリプト（Transcript）
- **連結出力**: `goal.md`, `plan.md`, `build.md`, `review.md`, 各種 Review (Rework) ファイル、`result.md` 等を 1 つの `transcript.md` に連結して出力します。
- **最新化**: 差し戻し等の経緯も含め、時系列順（所定の定義順）に最新の状態をまとめます。
- **自動生成**: `TranscriptGenerator` クラスにより、実行ディレクトリ内のアーティファクトから自動生成されます。

## 2. 技術仕様

### 2.1 バックエンド (Python/FastAPI)
- **サーバー**: Uvicorn (Port 8000)
- **API エンドポイント**:
    - `GET /api/runs`: 実行サマリーリストの取得
    - `GET /api/runs/{taxonomy}/{run_name}`: 特定の実行の詳細（アーティファクト一覧含む）
    - `GET /api/runs/{taxonomy}/{run_name}/artifacts/{filename}`: アーティファクト内容の取得
- **プロジェクトルート発見**: `find_project_root()` により実行場所に関わらず `runs/` を正確に探索。

### 2.2 フロントエンド (React/TypeScript)
- **フレームワーク**: Vite + React
- **スタイリング**: Tailwind CSS v4
- **アイコン**: Lucide React
- **ビルド出力**: `dist/` フォルダに出力され、FastAPI によって静的ファイルとして配信。

### 2.3 CLI 統合
- **コマンド**: `apsf view`
- **動作**: 
    1. FastAPI サーバーをバックグラウンドで起動（uvicorn）。
    2. デフォルトブラウザで `http://localhost:8000` を自動オープン。
