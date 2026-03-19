# Implementation Readiness Signals

Date: 2026-03-19
Scope: APSF framework run planning
Purpose: 「この run は実装の見通しがかなり良い」と判断できる条件を明示し、見通しの悪い run との差分を設計品質として再利用する

---

## One-Line Summary

実装見通しが良い run は、**設計の未決定論点が build に持ち越されず、変更対象・依存関係・検証方法が局所化されている**。逆に見通しが悪い run は、build の中で API 設計・スコープ判断・移行方針・例外処理を同時に決める必要がある。

---

## Positive Signals

### 1. API / data shape が先に確定している

- 例: `run-013` は `run-012` 時点で `RunRepository` の taxonomy-aware 方針が固まっていた
- build で新しく考える必要があったのは「CLI からどう使うか」の接続だけだった

### 2. 変更対象が機械的に列挙できる

- 例: `main.py` 内の `settings.runs_dir / run_name` 箇所がレビューで 8 コマンドまで特定済みだった
- 「どこを直すか」が探索ではなく置換作業になっていた

### 3. 依存関係が 1 本線になっている

- 例: `init_run(taxonomy=)` を入れる → `start-run --taxonomy` をつなぐ → 他コマンドを fallback 解決へ寄せる
- build 中の分岐が少なく、実装順が自然に決まる

### 4. 既存挙動を守る軸が明確

- 例: `taxonomy=None` fallback を維持する前提があったため、互換性の判断がぶれなかった
- 「何を変えてよく、何を守るか」が先に書かれている

### 5. 検証観点が plan 時点で具体化されている

- 例: `start-run --taxonomy`、fallback 解決、既存 CLI 回帰、追加テストの4系統が build 前から見えていた
- 実装後に「何を確認すればいいか」で迷わない

---

## Negative Signals

### 1. build の中で設計を決める必要がある

- API 追加か既存 API 拡張か
- filesystem 直変更か metadata 先行か
- どこまで同 run に入れるか

この状態だと、build が実装ではなく設計再開になる。

### 2. スコープに複数の種類の意思決定が混在している

- 例: API 設計、CLI UX、filesystem 移行、cross-reference 更新を同時に扱う
- 実装工数よりもスコープ判断コストが高くなる

### 3. 対象箇所が「探してみないと分からない」

- 影響箇所の棚卸しが plan にない run は、build 中に探索コストが膨らむ
- その結果、漏れや途中方針変更が起きやすい

### 4. 成功条件がテスト可能な形に落ちていない

- 「だいたい動く」では build を閉じられない
- CLI / repository / docs のどこで何を確認するかが必要

---

## Why Run-013 Was Readable To Implement

`run-013_apsf_cli-taxonomy-aware` が見通し良好だった理由:

- taxonomy filesystem 自体は `run-012` で実装済みだった
- repository 側の lookup 方針が既に固定されていた
- CLI 側の未追随箇所が review で具体的に列挙されていた
- `start-run --taxonomy` の依存が `init_run(taxonomy=)` だと早い段階で露出していた
- 実装単位が「CLI の接続修正 + テスト追加」に圧縮されていた

要するに、`run-013` は「難しい問題を解く run」ではなく、「先に分解された問題を順に配線する run」になっていた。

---

## Planning Heuristic

実装 run に進めてよいかを見極める簡易基準:

- build 開始前に主要 open question が 0 か 1 個までに減っている
- 変更対象ファイルを列挙できる
- 依存順が 3 段階以内で説明できる
- 既存互換の保持点を 1 文で言える
- テストやスモークチェックの観点を build 前に言える

この5つが揃わないなら、実装 run ではなく設計 run を追加した方が速い可能性が高い。

---

## Suggested Follow-Up

- plan / build レビュー時に「implementation readiness」観点を明示チェック項目として追加する
- 特に大きい run では、`Open Questions` を build 前に 0〜1 件へ減らすことを受理条件にしてもよい
