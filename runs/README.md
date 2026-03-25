# runs/

## 概要

`runs/` は problem solving の一次記録を保存するディレクトリです。  
1 つの run は 1 つの problem solving cycle を表します。

---

## 基本構成

```text
YYYY-MM-DD_case-key_topic/
  execution-assignment.md
  model-assignment.md
  goal.md
  plan.md
  plan_review.md      # optional
  handoff.md
  build_review.md     # optional
  review_review.md    # optional
  improve_review.md   # optional
  build.md
  review.md
  improve.md
  result.md
  transcript.md       # optional
```

### 各文書の位置づけ

- 一次記録: 実際の判断・実装・レビューの記録
- 二次記録: 一次記録をもとに再構成した読み物

| ファイル | 主担当 | 用途 | 種別 |
|---|---|---|---|
| `execution-assignment.md` | 人間 | 役割分担 | 一次記録 |
| `model-assignment.md` | 人間 | model 割当 | 一次記録 |
| `goal.md` | 人間 | 問題定義 | 一次記録 |
| `plan.md` | Planner | 方針と build 境界 | 一次記録 |
| `plan_review.md` | 人間 / Critic / reviewer | 再計画の修正メモ | 任意の補助記録 |
| `handoff.md` | 各 role | role 間の受け渡し | 一次記録 |
| `build_review.md` | 人間 / Critic / reviewer | 再build の修正メモ | 任意の補助記録 |
| `review_review.md` | 人間 / Critic / reviewer | 再review の修正メモ | 任意の補助記録 |
| `improve_review.md` | 人間 / Judge / reviewer | 再improve の修正メモ | 任意の補助記録 |
| `build.md` | Builder | 実装記録 | 一次記録 |
| `review.md` | Critic | 独立レビュー | 一次記録 |
| `improve.md` | Judge / 人間 | 改善判断 | 一次記録 |
| `result.md` | 人間 | 最終結果 | 一次記録 |
| `transcript.md` | 人間 / tooling | 一次記録の可読化 | 二次記録 |

---

## taxonomy

run は taxonomy で大きく 2 系統に分かれます。

```text
runs/fw-improvement/YYYY-MM-DD-NNN_case-key_topic/
runs/work/YYYY-MM-DD-NNN_case-key_topic/
```

| taxonomy | 用途 |
|---|---|
| `fw-improvement` | framework, CLI, template, agent policy などの改善 |
| `work` | 実案件やプロダクト作業 |

legacy な top-level run は `runs/YYYY-MM-DD_case-key_topic/` に残ることがあります。

---

## parent / child run

必要なら run の下に child run を作れます。

```text
runs/
  work/
    2026-03-18-016_parent-run/
      goal.md
      plan.md
      ...
      016c1_child-run/
      016c2_child-run/
```

### child run の命名

- parent run の番号を継ぐ
- `c1`, `c2` のように子番号を付ける
- 末尾に topic を付ける

例:

```text
016c1_sochi-blocks_x-thread-content
```

---

## framework/templates と runs/_template

| パス | 用途 |
|---|---|
| `framework/templates/` | 正規テンプレート |
| `runs/_template/` | 新しい run を作るときのコピー元 |

---

## plan_review.md について

`plan_review.md` は正式な補助文書ですが必須ではありません。

使う場面:

- `plan.md` に対して structured な修正依頼を残したい
- `PLAN_NEEDED` に戻して再計画したい
- 再計画の理由を run に残したい

使わない場面:

- 通常の plan 作成
- 軽微な口頭メモだけで十分なとき

重要なのは、`plan_review.md` は `plan.md` を置き換えないことです。  
canonical な plan artifact は引き続き `plan.md` です。

---

## build_review.md について

`build_review.md` は正式な補助文書ですが必須ではありません。

使う場面:

- `build.md` や build 出力に対して structured な修正依頼を残したい
- `BUILD_NEEDED` に戻して再build したい
- 再build の理由を run に残したい

使わない場面:

- 通常の build
- 軽微な口頭メモだけで十分なとき

重要なのは、`build_review.md` は `build.md` を置き換えないことです。  
canonical な build artifact は引き続き `build.md` です。

---

## review_review.md について

`review_review.md` は正式な補助文書ですが必須ではありません。

使う場面:

- `review.md` に対して structured な修正依頼を残したい
- `REVIEW_NEEDED` に戻して再review したい
- 再review の理由を run に残したい

使わない場面:

- 通常の review
- 軽微な口頭メモだけで十分なとき

重要なのは、`review_review.md` は `review.md` を置き換えないことです。  
canonical な review artifact は引き続き `review.md` です。

運用上は 1 run あたり 1 つの `review_review.md` を想定します。再レビューをもう一度回す場合は、必要なら既存内容を退避してから上書きします。

---

## improve_review.md について

`improve_review.md` は正式な補助文書ですが必須ではありません。

使う場面:

- `improve.md` に対して structured な修正依頼を残したい
- `IMPROVE_NEEDED` に戻したまま Judge 判断をやり直したい
- 再improve の理由を run に残したい

使わない場面:

- 通常の improve
- 軽微な口頭メモだけで十分なとき

重要なのは、`improve_review.md` は `improve.md` を置き換えないことです。  
canonical な Judge artifact は引き続き `improve.md` です。

運用上は 1 run あたり 1 つの `improve_review.md` を想定します。再判断をもう一度回す場合は、必要なら既存内容を退避してから上書きします。

---

## rerun scripts

### phase / 差し戻し artifact / 実行経路

| phase | canonical artifact | 差し戻し artifact | rerun script | 次の実行経路 |
|---|---|---|---|---|
| `PLAN_NEEDED` | `plan.md` | `plan_review.md` | `apsf-rerun-plan.ps1` | `.\scripts\apsf-claude-act.ps1 $run` |
| `BUILD_NEEDED` | `build.md` | `build_review.md` | `apsf-rerun-build.ps1` | `apsf build $run` または `.\scripts\apsf-claude-build.ps1 $run` |
| `REVIEW_NEEDED` | `review.md` | `review_review.md` | `apsf-rerun-review.ps1` | `.\scripts\apsf-claude-act.ps1 $run` |
| `IMPROVE_NEEDED` | `improve.md` | `improve_review.md` | `apsf-rerun-improve.ps1` | `apsf next $run` を見て Human Judge が更新 |

`plan_review.md` / `build_review.md` / `review_review.md` / `improve_review.md` はいずれも補助文書です。phase の canonical artifact を置き換えず、差し戻し理由と再実行時の注意点を残すために使います。

### 典型的な差し戻しパターン

再計画:

```powershell
$run = "2026-03-23-001_sochi-2d_stock-pipeline-hardening"

.\scripts\apsf-rerun-plan.ps1 $run
.\scripts\apsf-claude-act.ps1 $run
```

再build:

```powershell
$run = "2026-03-23-001_sochi-2d_stock-pipeline-hardening"

.\scripts\apsf-rerun-build.ps1 $run
apsf build $run
```

`apsf-claude-build.ps1` が `Reached max turns` で停止した場合、その build は成功扱いしません。  
ただし途中成果物が disk に残ることはあります。その場合は phase を自動で進めず、人間または Critic が partial / incomplete な前進として扱うかを判断します。

再レビュー:

```powershell
$run = "2026-03-23-001_sochi-2d_stock-pipeline-hardening"

.\scripts\apsf-rerun-review.ps1 $run
.\scripts\apsf-claude-act.ps1 $run
```

再improve:

```powershell
$run = "2026-03-23-001_sochi-2d_stock-pipeline-hardening"

.\scripts\apsf-rerun-improve.ps1 $run
apsf next $run
```

`apsf-rerun-plan.ps1` は必要に応じて `plan_review.md` 雛形を、`apsf-rerun-build.ps1` は必要に応じて `build_review.md` 雛形を、`apsf-rerun-review.ps1` は必要に応じて `review_review.md` 雛形を、`apsf-rerun-improve.ps1` は必要に応じて `improve_review.md` 雛形を作ります。

---

## transcript.md

`transcript.md` は一次記録をそのまま貼るのではなく、役割ごとの要点を読みやすく要約した文書です。任意ですが、初回 run や振り返り価値の高い run では推奨です。

---

## 関連ファイル

- template guide: [runs/_template/README.md](/C:/Users/PC_User/PRJ/ai-problem-solving-framework/runs/_template/README.md)
- canonical boundaries: [framework/responsibility-matrix.md](/C:/Users/PC_User/PRJ/ai-problem-solving-framework/framework/responsibility-matrix.md)
