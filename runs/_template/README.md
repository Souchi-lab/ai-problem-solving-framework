# Run Template

## run の始め方

```bash
apsf init-run YYYY-MM-DD_case-key_topic

# 手動で作る場合
cp -r runs/_template runs/YYYY-MM-DD_case-key_topic
```

---

## GUI Verification Rule

FW改善で GUI / Viewer / Agent OS を触る run では、`npm run build` や API 単体確認だけで完了扱いにしない。

- visible behavior が変わる変更では、少なくとも manual smoke で GUI の操作列を確認する
- 可能なら E2E を追加する
- 特に以下を含む変更では、child run を含む総合確認を優先する
  - run / child-run 切替
  - Agent OS タブ
  - assignment / recovery / operator action panel
  - confirm / apply / rerun など state を変える操作

最低限 build/review/result には、確認した操作列を明記する。

例:

- run を選択する
- child run に切り替える
- Agent OS タブを開く
- 必要な panel / candidate list が表示される
- Confirm / Apply 後に badge や state が更新される

GUI まで触れていない場合は、未確認であることを明記する。

---

## ファイル構成

1 run は 1 つの problem solving cycle を表します。基本構成は次のとおりです。

```text
execution-assignment.md   run 全体の役割分担
goal.md                   問題定義と成功条件
plan.md                   Planner の方針整理
plan_review.md            任意。再計画のための修正メモ
build_review.md           任意。再build のための修正メモ
review_review.md          任意。再review のための修正メモ
improve_review.md         任意。再improve のための修正メモ
build.md                  Builder の実装記録
review.md                 Critic のレビュー
improve.md                Judge の改善判断
result.md                 最終結果
transcript.md             任意。一次記録の可読化まとめ
```

`plan_review.md` / `build_review.md` / `review_review.md` / `improve_review.md` は正式な補助文書ですが任意です。`plan.md` / `build.md` / `review.md` / `improve.md` を置き換えるものではなく、差し戻し時の補助メモとして使います。

`execution-assignment.md` は default skeleton に含まれます。`model-assignment.md` / `handoff.md` は conditional artifact なので、default skeleton には含めません。必要になったら `framework/templates/` から作成してください。

```text
framework/templates/model-assignment.md
framework/templates/handoff.md
```

---

## 各ファイルの役割

### `execution-assignment.md`

- run の役割分担を定義する
- 各 role の責務境界だけを残す
- 詳細な操作説明や長い手順書にはしない

### `model-assignment.md`

- default skeleton には含まれない
- run 開始時に必須とは限らない
- role ごとの model 方針が outcome や独立性に効くときに作る
- provider / model と主要な理由だけを書く
- 重要でないコスト説明や定型文は最小限でよい

### `plan.md`

- `goal.md` をもとに Planner が方針を整理する
- 選択肢、採用理由、build 境界を書く
- Builder がどこまで進んでよいかを明記する

### `plan_review.md`

- 任意の補助文書
- Human / Critic / reviewer が Planner に再修正を依頼するときに使う
- `PLAN_NEEDED` に戻して再計画するときの根拠を残す

### `build_review.md`

- 任意の補助文書
- Human / Critic / reviewer が Builder に再修正を依頼するときに使う
- `BUILD_NEEDED` に戻して再build するときの根拠を残す

### `review_review.md`

- 任意の補助文書
- Human / Critic / reviewer が Critic に再修正を依頼するときに使う
- `REVIEW_NEEDED` に戻して再review するときの根拠を残す

### `improve_review.md`

- 任意の補助文書
- Human / Judge / reviewer が Judge に再修正を依頼するときに使う
- `IMPROVE_NEEDED` に戻して再improve するときの根拠を残す

### `handoff.md`

- default skeleton には含まれない
- role 間の受け渡しメモ
- 常時必須ではない
- `plan.md` / `build.md` / `review.md` の代替にはしない
- 追加の transfer context がないなら最小限でよい
- 次の role が最初に確認すべき点だけを優先する

### `transcript.md`

- 一次記録を役割別の発言形式で再構成した読み物
- `result.md` 完了後に生成する
- 任意だが初回 run では強く推奨

---

## 典型フロー

```text
Goal
  -> Plan
  -> Build
  -> Review
  -> Improve
  -> Result
```

役割の受け渡しは、追加の transfer context が必要なときだけこうなります。

```text
Planner -> (handoff.md if needed) -> Builder
Builder -> (handoff.md if needed) -> Critic
Critic  -> (handoff.md if needed) -> Judge
```

### phase / 差し戻し artifact 対応

| phase | canonical artifact | 差し戻し artifact | rerun script | 次の実行経路 |
|---|---|---|---|---|
| `PLAN_NEEDED` | `plan.md` | `plan_review.md` | `apsf-rerun-plan.ps1` | `.\scripts\apsf-claude-act.ps1 $run` |
| `BUILD_NEEDED` | `build.md` | `build_review.md` | `apsf-rerun-build.ps1` | `apsf build $run` または `.\scripts\apsf-claude-build.ps1 $run` |
| `REVIEW_NEEDED` | `review.md` | `review_review.md` | `apsf-rerun-review.ps1` | `.\scripts\apsf-claude-act.ps1 $run` |
| `IMPROVE_NEEDED` | `improve.md` | `improve_review.md` | `apsf-rerun-improve.ps1` | `apsf next $run` を見て Human Judge が更新 |

差し戻し artifact はすべて任意です。`plan.md` / `build.md` / `review.md` / `improve.md` の代わりではなく、再実行時の補助メモとして扱います。

再計画が必要なときは次の流れを使います。

```text
reviewer / Human
  -> plan_review.md
  -> PLAN_NEEDED に戻す
  -> Planner が plan.md を更新
```

再build が必要なときは次の流れを使います。

```text
reviewer / Human
  -> build_review.md
  -> BUILD_NEEDED に戻す
  -> Builder が build.md を更新
```

`apsf-claude-build.ps1` が `Reached max turns` で止まった場合は、成功ではなく partial / incomplete として扱います。途中成果物が残ることはありますが、phase は自動で進めず、人間側が続行判断を行います。

---

## transcript の書き方

`transcript.md` では、一次記録をそのまま貼るのではなく要約します。

例:

```text
Planner: goal.md を読んで X・Y・Z を構造化した。採用アプローチは A。
Plan Review: 必要なら plan_review.md に修正要求を残し、PLAN_NEEDED に戻して再計画する。
Builder: A・B・C を実施した。未解決は D。
Critic: Critical なし、Minor 2 件。次 run で対処可能。
Judge: Minor のみなので採用。
```

---

## 参照元テンプレート

| ファイル | テンプレート | 主担当 | 種別 |
|---|---|---|---|
| `execution-assignment.md` | `framework/templates/execution-assignment.md` | 人間 | 一次記録 |
| `model-assignment.md` | `framework/templates/model-assignment.md` | 人間 | 条件付きの一次記録 |
| `goal.md` | `framework/templates/goal.md` | 人間 | 一次記録 |
| `plan.md` | `framework/templates/plan.md` | Planner | 一次記録 |
| `plan_review.md` | `framework/templates/plan-review.md` | 人間 / Critic / reviewer | 任意の補助記録 |
| `handoff.md` | `framework/templates/handoff.md` | 各 role | 条件付きの一次記録 |
| `build_review.md` | `framework/templates/build-review.md` | 人間 / Critic / reviewer | 任意の補助記録 |
| `review_review.md` | `framework/templates/review-review.md` | 人間 / Critic / reviewer | 任意の補助記録 |
| `improve_review.md` | `framework/templates/improve-review.md` | 人間 / Judge / reviewer | 任意の補助記録 |
| `build.md` | `framework/templates/build.md` | Builder | 一次記録 |
| `review.md` | `framework/templates/review.md` | Critic | 一次記録 |
| `improve.md` | `framework/templates/improve.md` | Judge / 人間 | 一次記録 |
| `result.md` | `framework/templates/result.md` | 人間 | 一次記録 |
| `transcript.md` | `framework/templates/transcript.md` | 人間 / tooling | 二次記録 |

---

## framework/templates と runs/_template の違い

| パス | 用途 |
|---|---|
| `framework/templates/` | 設計上の正規テンプレート |
| `runs/_template/` | 新しい run をコピーするときの雛形 |

テンプレートの意味を変えるときは、まず `framework/templates/` を直し、その後必要に応じて `runs/_template/` に反映します。

---

## run 開始時チェック

- [ ] run 名が `YYYY-MM-DD_case-key_topic` 形式になっている
- [ ] `execution-assignment.md` を書いた
- [ ] `model-assignment.md` が mandatory / recommended / optional のどれか判断した
- [ ] 必要なら `framework/templates/model-assignment.md` から `model-assignment.md` を作成した
- [ ] `goal.md` の成功条件が明確
- [ ] 必要なら `apsf dry-run <run-name>` を実行して role の流れを確認した

## run 完了時チェック

- [ ] `result.md` を書いた
- [ ] `result.md` の `Generalization` と `Reusable Prompt` を書いた
- [ ] 必要なら `transcript.md` を生成した
