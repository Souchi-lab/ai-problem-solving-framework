# Plan

---

## Follow-up Context

- Parent series: 軽量 follow-up 運用の実地検証
- Previous result: video-intro-assembly — 小実装タスクに4点セットが機能することを確認
- New trigger: 毎回 goal/plan/review/result を手で組む摩擦を CLI コマンドで除去する
- Scope limit: `src/apsf/cli/main.py` への `init-followup` コマンド追加のみ
- Non-goals: AI 自動生成 / runs/ への適用 / GUI / init-run の変更

---

## Run Metadata

- Follow-up: init-followup-cmd
- Goal: `apsf init-followup <slug>` で4ファイルのスケルトンを生成する
- Output focus: コマンド実装 + 動作確認 + 心理コスト評価
- Non-goal reminder: テンプレートの全文自動生成・AI 連携はやらない

---

## Goal Readiness Check

- 変更対象が `main.py` 1ファイルに限定されている
- テンプレートの粒度判断の基準（実績2件）が手元にある
- 心理コスト評価の観点（4点）が goal で定義されている

Decision: Proceed

---

## Execution Intent

### 表層: CLI コマンドの実装

`apsf init-followup <slug>` を追加し、
`framework/experimental/redesign/followups/<slug>/` に
4ファイルのスケルトンを生成する。

### 裏層: 形式検証

「CLI 拡張を伴う小実装タスク」に4点セットが機能するかを記録する。
今回は実装規模が小さいため、review は skip して build → result に進む。

---

## Problem Structure

### 1. 追加するコマンドの仕様

```
apsf init-followup <slug> [--force]
```

- `slug`: follow-up 名（例: `twitter-tag-improvement`）
- `--force / -f`: 既存ディレクトリを上書き
- 出力先: `framework/experimental/redesign/followups/<slug>/`
- 生成ファイル: goal.md / plan.md / review.md / result.md

### 2. 出力先パスの組み立て

`Settings` に新しい property を追加せず、
`main.py` 内で `settings.framework_root / "framework/experimental/redesign/followups"` を直接組み立てる。

理由: followups ディレクトリは experimental 配下の固定パスであり、
env var で差し替える需要がまだない。v1 はシンプルに保つ。

### 3. テンプレートの置き場

コード内定数として `main.py` に定義する（外部ファイルなし）。

理由:
- 外部ファイルにすると `package_data` 設定や `importlib.resources` が必要になる
- 4ファイル × 数十行 = 合計200行程度であり、コード内定義で十分
- 変更頻度が低いテンプレートを外部化するメリットは小さい

### 4. テンプレートの粒度

実績2件（twitter-tag / video-intro）から共通構造を抽出した最小セット。

**goal.md**:
- Follow-up Context（5フィールド）
- Goal Statement / Background / Success Criteria / Expected Outputs
- Non-Goals / Constraints / Notes For Planner

**plan.md**:
- Follow-up Context / Run Metadata / Goal Readiness Check
- Execution Intent（表層/裏層）/ Problem Structure
- Selected Approach / Scope Policy / Deliverables
- Review Checklist / Planned Output Shape
- Assumptions & Open Questions
- What This Follow-up Decides / Does Not Decide

**review.md**:
- Follow-up Context
- Gate Questions（3問プレースホルダー）
- Decision / Notes

**result.md**:
- Status
- 番号付きセクション（実装差分 / 評価 / 採用判断 / 形式評価）
- Closing（Stable Baseline / Open Conditional / Next Trigger）

---

## Selected Approach

Approach:

`main.py` に `@app.command("init-followup")` を追加し、
4つのテンプレート文字列をコード内定数として定義する。
`init-run` と同じ `typer.Argument` + `typer.Option(--force)` パターンに従う。

Reasoning:

- 既存コマンドとの実装一貫性を保てる
- 外部依存（template ファイル、settings 追加）がゼロ
- テンプレートの変更が main.py 1ファイルで完結する

---

## Scope Policy

この follow-up に含めるもの:

- `main.py` への `init-followup` コマンド追加
- 4ファイルのテンプレート文字列（コード内定数）
- `apsf init-followup <slug>` の手動動作確認

この follow-up に含めないもの:

- `settings.py` の変更
- 既存コマンドの変更
- テンプレートファイルの外部化
- 自動テストの追加（手動確認で十分）

---

## Deliverables

- `src/apsf/cli/main.py` 差分（`init-followup` コマンド + 4テンプレート定数）
- 手動動作確認（`apsf init-followup test-slug` が通ること）
- result での心理コスト評価

---

## Review Checklist

- 実装が `main.py` 1ファイルの変更に収まっている
- 既存コマンドの動作が変わっていない
- `--force` なしで既存 slug に対してエラーが出る
- 生成された4ファイルに Follow-up Context / closing block が含まれている

---

## Planned Output Shape

result は次の構成でまとめる。

1. 実装差分サマリー（変更行数・テンプレート構造）
2. 動作確認結果
3. 心理コスト評価（4観点: 開始までの迷い / 手作業量 / 命名迷い / 初期構造の再発明量）
4. 形式評価（CLI 拡張タスクへの4点セット適合度）
5. Closing（Stable Baseline / Open Conditional / Next Trigger）

---

## Assumptions & Open Questions

Assumptions:

- テンプレートはコード内定義で十分（外部ファイル不要）
- `followups/` の場所は `framework/experimental/redesign/followups/` 固定でよい
- review は skip して build → result に進む

Open questions:

- 将来 followups/ の場所が変わる場合は settings.py に `followups_dir` を追加する
- テンプレートが肥大化した場合は外部ファイル化を検討する

---

## What This Follow-up Decides

- `init-followup` コマンドの実装方針（コード内テンプレ / main.py 単体変更）
- v1 テンプレートの構造（粒度・セクション構成）

---

## What This Follow-up Does Not Decide

- テンプレートの AI 自動カスタマイズ
- `runs/` 系への適用
- followups/ パスの env var 化
