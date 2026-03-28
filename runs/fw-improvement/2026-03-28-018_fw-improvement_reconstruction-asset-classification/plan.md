# Plan

---

## Goal Readiness Check

- goal.md 定義済み（4 点出力・粒度制約・minor revisions すべて明記）
- redesign plan.md の classification rules が参照可能な状態にある
- repo 資産（`framework/` + `src/apsf/`）のファイルリストが確認済み
- design-only run。ファイル移動なし

Decision: Proceed

---

## Problem Structure

この run が解く問題は 1 つ：

> 「設計パッケージの分類ルールを、実際の repo 資産に適用し、
>   次の implementation-planning run が開始判断できる状態を作る」

4 点の出力はすべてこの 1 問題の facet。

---

## Selected Approach

### 分類方法

redesign plan.md の 4 ルールをそのまま適用する。

| ルール | 適用基準 |
|---|---|
| Rule 1: `core` | 安定した契約・責務境界・成果物の意味定義 |
| Rule 2: `legacy` | 現在の APSF が動作するために必要な運用形状 |
| Rule 3: `experimental` | 正式採用前の再設計ドラフト |
| Rule 4: `viewer` | 独立サポート層（検索・比較・ナビゲーション） |
| 補足: `docs` | 運用外の説明・参照文書 |

迷いが生じた場合は「分類ルールに立ち戻って問い直す」（Minor Revision 6 を遵守）。

### 粒度方針

- ファイル単位で分類（ディレクトリ丸ごとの分類は避ける）
- `framework/templates/*` の大半など明白に同類のグループは
  「グループとして legacy、例外あり」形式で記載を許容
- 目安: 30〜50 点

---

## Execution Steps

### Step 1 — 資産スキャン（内部作業）

対象ディレクトリのファイル構造を確認し、分類対象の代表資産を選定する。

選定基準:
- 各責務クラスの代表例を網羅する
- 「迷い」が生じそうな境界ケースを優先的に含む
- viewer / `__pycache__` / `node_modules` などのビルド成果物・依存物は除外

### Step 2 — Output 1: Representative asset classification table

`result.md` 内に埋め込む形式で作成。

| パス | 分類 | 根拠（1行） |
|---|---|---|
| ... | core / legacy / experimental / viewer / docs | ... |

「迷い資産」は表の末尾に専用セクションを設ける。

### Step 3 — Output 2: Repo-specific directory mapping proposal

現パス → 移行後の想定パスの対応表。
現状維持（移動しない）資産も `(stay)` で明示する。

### Step 4 — Output 3: Compare material

`docs/compare/reconstruction-018.md` を新規作成。
構造比較はディレクトリ責務レベルで行い、1 ページ以内に収める。
「同じテーマの run を両構造でどこに置くか」を示す。

### Step 5 — Output 4: Implementation-planning acceptance criteria

「移行 run を開始してよい条件」を 5〜8 項目で定義。
「まだ決まっていないこと」も併記する。

---

## Scope Policy

### 含めるもの
- 4 点の design output（分類表・mapping・compare・acceptance criteria）

### 含めないもの
- 実ファイルの移動・リネーム
- import / path の変更
- CLI や repo 構造の変更
- legacy retirement 条件の定義
- 設計の全面再レビュー

---

## Deliverables

| 成果物 | 場所 |
|---|---|
| 資産分類表 + mapping + acceptance criteria | `result.md` |
| Compare material | `docs/compare/reconstruction-018.md` |

---

## Review Policy

この run は design-only かつ単一 executor（Claude）なので review は skip。
result.md の success criteria 照合をもって完了とする。
