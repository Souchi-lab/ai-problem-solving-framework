# FW Improvement Note

Date: 2026-03-19
Theme: 親子 run のディレクトリ配置を filesystem 上でも親子に揃える
Scope: APSF run topology / naming / discovery / transcript traceability

---

## One-Line Summary

親子 run を導入するなら、子 run は `runs/` 直下の別 run として並べるのではなく、
**親 run ディレクトリ直下の子ディレクトリ**として配置した方がよい。

---

## Trigger

現行の試験運用では、論理上は親子関係にある run が以下のように `runs/` 直下へ並列配置されている。

- `runs/2026-03-18-016_sochi-blocks_x-post-experiment`
- `runs/2026-03-18-016_sochi-blocks_x-post-experiment/016c1_sochi-blocks_x-thread-content`
- `runs/2026-03-18-016_sochi-blocks_x-post-experiment/016c2_sochi-blocks_x-experiment-exec`

この配置でも名前だけで関係は推測できるが、filesystem 上の親子関係は失われる。

---

## Problem

親子関係を命名規則だけで持つと、以下の問題が起きやすい。

- `runs/` 一覧で親 run と子 run が分断される
- 親 run 配下の関連成果物をまとめて辿れない
- transcript / result / review から子 run を探す時に参照負荷が高い
- 子 run を別テーマの通常 run と見分けにくい
- 将来 `apsf next` や run discovery を改善する際、親子関係を文字列パースに頼りやすい

---

## Proposed Rule

子 run は親 run ディレクトリ直下に置く。

推奨イメージ:

```text
runs/
  2026-03-18-016_sochi-blocks_x-post-experiment/
    goal.md
    plan.md
    build.md
    ...
    016c1_sochi-blocks_x-thread-content/
      goal.md
      plan.md
      ...
    016c2_sochi-blocks_x-experiment-exec/
      goal.md
      plan.md
      ...
```

重要なのは `children/` の有無ではなく、
**「子 run が親 run ディレクトリ直下にいる」こと**を標準化する点である。

---

## Why This Is Better

### 1. Traceability

- 親 run を開けば、その run に属する子 run 群を一覧できる
- 親 run の goal / result と子 run の証拠が物理的に近くなる

### 2. Discovery Simplicity

- run discovery 時に「親 run の配下を見れば子 run がある」というルールにできる
- naming だけに依存しない

### 3. Transcript / Result Consistency

- 親 run transcript から子 run を参照しやすい
- 親 run result の統合判断と子 run result の対応が取りやすい

### 4. Reduced Naming Burden

- 子 run が親の近傍に存在するため、名前へ親情報を過剰に埋め込まなくて済む
- `016c1` のような短い子番号でも十分に意味を持ちやすい

---

## Tradeoffs

- `runs/` 直下だけを前提にした既存ツールや一覧スクリプトは調整が必要
- 現行の `run_repository` や phase detection が再帰探索に弱い場合、実装対応が要る
- 既存の試験運用 run との後方互換をどう扱うかを決める必要がある

---

## Recommendation

方針としては以下が妥当。

1. **新規の親子 run から直下子ディレクトリ方式を採用**
2. 既存の top-level 子 run は当面 legacy 扱いで許容
3. CLI / README / run discovery は後方互換ありで段階的に追随

---

## Expected Follow-Up

- `runs/README.md` に親子 run の標準配置を追記
- `apsf start-run` に親 run 配下での子 run 作成モードを設計
- run discovery / transcript / result 参照の実装が再帰構造を扱えるか確認
- `2026-03-18-015_apsf_parent-child-run-model` の命名規則案を topology 前提で更新

---

## Suggested Improvement Run

- `apsf_parent-child-directory-topology`

---

## Related Evidence

- [`runs/2026-03-18-015_apsf_parent-child-run-model/goal.md`](C:/Users/PC_User/PRJ/ai-problem-solving-framework/runs/2026-03-18-015_apsf_parent-child-run-model/goal.md)
- [`framework/improvement-notes/2026-03-19_fw-improvement-priority-map.md`](C:/Users/PC_User/PRJ/ai-problem-solving-framework/framework/improvement-notes/2026-03-19_fw-improvement-priority-map.md)
- [`runs/2026-03-18-016_sochi-blocks_x-post-experiment/goal.md`](C:/Users/PC_User/PRJ/ai-problem-solving-framework/runs/2026-03-18-016_sochi-blocks_x-post-experiment/goal.md)
