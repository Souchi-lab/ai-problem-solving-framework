# Execution Assignment

<!-- 1 run の開始時に model-assignment.md と一緒に作成する -->
<!-- 「どのモデルを使うか」ではなく「どうやって実行するか」を定義する -->
<!-- execution type: cli / human / future-api -->

---

## Run Name

<!-- runs/ のフォルダ名 -->

## Goal Summary

<!-- goal.md から 1〜2 文で転記 -->

---

## Role Execution Assignments

| Role | Execution Type | Tool / Method | Workspace | Notes |
|---|---|---|---|---|
| Planner | human | 手動 | workspaces/planner/ | 人間推奨 |
| JuniorBuilder | cli | gemini-cli | workspaces/junior_builder/ | |
| Builder | cli | claude | workspaces/builder/ | 高付加価値工程 |
| Critic | human / cli | ChatGPT / 手動 | workspaces/critic/ | Builder と別系統推奨 |
| Judge | human | 手動 | workspaces/judge/ | 人間必須（v0.1） |

---

## Workspace Mapping

<!-- どの workspace を使うか。不要な role は削除してよい -->

```
workspaces/planner/       ← plan.md の作成拠点
workspaces/junior_builder/ ← 候補案の生成拠点
workspaces/builder/        ← 成果物の生成拠点
workspaces/critic/         ← review.md の作成拠点
workspaces/judge/          ← 判断・result.md の記録拠点
```

---

## Command or Manual Procedure

<!-- 各 role の実行手順を具体的に書く -->

### Planner（human）
1. `goal.md` を読む
2. ChatGPT / 自分で plan.md を作成する
3. `runs/<run-name>/plan.md` に保存する
4. `handoff.md` を更新して次の role に渡す

### JuniorBuilder（cli）
```bash
cd workspaces/junior_builder/
# plan.md を参照して候補案を生成する
# 例: gemini-cli や ChatGPT CLI を使う
```

### Builder（cli）
```bash
cd workspaces/builder/
# claude を起動し、plan.md + handoff.md を読ませて成果物を生成する
```

### Critic（human / cli）
1. `build.md` と成果物を読む
2. Critical / Major / Minor の観点でレビューする
3. `review.md` に記録する

### Judge（human）
1. `review.md` を読む
2. Goal の成功基準と照合して判断する
3. `improve.md` または `result.md` を書く

---

## Why This Execution Plan

<!-- なぜこの実行手段にしたか -->

-

---

## Operational Risks

<!-- この実行計画で想定されるリスク -->

- [ ]
