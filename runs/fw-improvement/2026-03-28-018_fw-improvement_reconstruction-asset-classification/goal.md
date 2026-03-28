# Goal

Run: 2026-03-28-018_fw-improvement_reconstruction-asset-classification
Date: 2026-03-28

---

## Goal Readiness Check

- redesign パッケージは `Accept with Minor Revisions` でクローズ済み
- plan.md に 3 層モデルの classification rules が定義済み
- 今回は plan.md の定義を実際の repo 資産に適用し、4点の design output を生成する

Decision: Proceed

---

## Objective

`framework/experimental/redesign/` の設計パッケージを、
実際の repo 資産への適用結果として出力することで、
次の implementation-planning run が「開始してよいかを判断できる」状態を作る。

---

## Scope

この run が生成すべき 4 点:

1. **Representative asset classification table**
   - 対象: `framework/` と `src/apsf/` の主要ファイル群
   - 粒度: ファイル単位（ディレクトリ丸ごと分類は避ける）
   - 各ファイルに `core / legacy / experimental / viewer / docs` のいずれかを付与
   - 分類根拠を 1 行で添える
   - 「迷った」資産は迷いの理由を明記する

2. **Repo-specific directory mapping proposal**
   - 現在の `framework/` と `src/apsf/` のパスを、
     移行後の想定パスへマッピングした表
   - 移動しない（現状維持）資産も明示する

3. **Compare material** → `docs/compare/reconstruction-018.md`
   - 現構造 vs 提案構造の並列比較
   - テーマレベルの run が両構造で引き続き compareable であることを示す

4. **Implementation-planning acceptance criteria**
   - 「この条件が満たされれば次の実装 run を開始してよい」を箇条書きで定義
   - 「まだ決まっていないこと」も明示する

---

## Constraints on Output Granularity

### Representative asset の粒度

- `framework/templates/` ディレクトリ丸ごと `legacy` ではなく、
  ファイル単位で分類する
- ただし定型的なファイル群（例: templates/* の大半）は
  「グループとして legacy、例外あり」の表記を許容する
- 資産数は 30〜50 点程度を目安とする（網羅より代表性を優先）

### Compare material の厚さ

- 構造比較は「ディレクトリ責務レベル」で行う（ファイル 1 本ずつの比較は不要）
- 現構造と提案構造それぞれの「同じテーマの run をどこに置くか」を示す
- 1 ページ程度に収める（厚くしない）

### Acceptance criteria の境界

- 「移行 run を開始してよい条件」に絞る
- 「移行が完了した条件」や「設計品質の評価基準」はスコープ外
- 5〜8 項目程度

---

## Non-Goals

- 実ファイルの移動・リネーム
- import / path の変更
- CLI や repo 構造の変更
- 設計の全面再レビュー
- legacy retirement の条件定義

---

## Success Criteria

1. 30〜50 点の代表資産が `core / legacy / experimental / viewer / docs` に分類されている
2. 各分類に 1 行の根拠がある
3. 「迷った資産」が明示されている
4. directory mapping table が現パスと提案パスの対応を示している
5. compare material が `docs/compare/reconstruction-018.md` に存在する
6. acceptance criteria が 5〜8 項目で定義されている
7. 全出力が design-only で、ファイル移動を含まない

---

## Minor Revisions to Carry Forward (from redesign result.md)

1. `framework/overview.md` は extraction source として扱う（core にそのまま入れない）
2. `src/apsf/storage/*` は今回 legacy。将来の extraction 候補として記録
3. compare は theme-level run granularity で維持する
4. `legacy` は「現在の動作形状」として readable に保つ
5. `experimental` は採用前提の命名・参照をしない
6. 分類例外は規則を先に問い直してから受け入れる
