# Transcript: {{run_name}}

<!--
  二次成果物 — 正式記録ではない

  ═══════════════════════════════════════════════════════════════
  【定義】
  このファイルは一次記録（goal.md 〜 result.md）を
  「役割別の発言形式で再構成した可読化文書」である。

  - 逐語ログではない（会話をそのまま保存したものではない）
  - 会話の再現・創作ではない（それっぽい発言を作り上げない）
  - 元ファイルをもとに「何を判断し、何を渡したか」を要約した記録である

  正確な情報が必要な場合は、必ず一次記録（goal.md〜result.md）を参照すること。
  ═══════════════════════════════════════════════════════════════

  【引用と要約のルール】
  - 元ファイルの原文を「そのまま」転記する場合のみ > (blockquote) を使う
  - 要約・再構成・解釈には > を使わない（通常テキストで書く）
  - handoff の内容は要約で書く（引用ブロックにしない）
  ★ 迷ったら引用より要約が安全。根拠が複数ファイルにまたがる場合は必ず要約にする。

  【制約】
  - 元ファイルに書かれていないことを追加しない
  - 「それっぽい会話」を創作しない。元ファイルにない発言を補完しない
  - 各ロールブロックは 3〜5 行を目安にする
  - 事実ベースで書く。推測・補完・脚色をしない

  生成タイミング: result.md 完了後
  参照元:
    execution-assignment.md  どうやって実行したか（計画・実績）
    goal.md                  何を解いたか
    plan.md                  どう分解・構造化したか
    handoff.md               何を引き継いだか（最終状態）
    build.md                 何を作ったか
    review.md                何を指摘されたか
    improve.md               どう判断したか
    result.md                何が一般化されたか
    workspaces/*/            JuniorBuilder のドラフト等（該当する場合）
-->

---

## Run Overview

**Run**: {{run_name}}
**Date**: {{date}}
**Case**: {{case_key}}
**Topic**: {{topic}}
**Status**: Completed

**Planned Assignment** (execution-assignment.md より):

| Role | Planned Execution | Planned Tool |
|---|---|---|
| Planner | {{planner_planned_execution}} | {{planner_planned_tool}} |
| JuniorBuilder | {{junior_builder_planned_execution}} | {{junior_builder_planned_tool}} |
| Builder | {{builder_planned_execution}} | {{builder_planned_tool}} |
| Critic | {{critic_planned_execution}} | {{critic_planned_tool}} |
| Judge | human | — |

**Actual Execution** (実際に使用したツール・方法):

| Role | Actual Execution | Actual Tool |
|---|---|---|
| Planner | {{planner_actual_execution}} | {{planner_actual_tool}} |
| JuniorBuilder | {{junior_builder_actual_execution}} | {{junior_builder_actual_tool}} |
| Builder | {{builder_actual_execution}} | {{builder_actual_tool}} |
| Critic | {{critic_actual_execution}} | {{critic_actual_tool}} |
| Judge | human | — |

---

## Goal

**Human**: {{goal_statement_1sentence}}

*背景*: {{background_1sentence}}

*成功基準（要約）*:
{{success_criteria_summary}}

*Planner へのメモ*: {{notes_to_planner}}

---

## Planning

**Planner**: {{planning_summary}}

問題の構造:
- {{problem_structure_point_1}}
- {{problem_structure_point_2}}

採用アプローチ:
{{selected_approach}}

Builder への品質基準:
- {{quality_criterion_1}}
- {{quality_criterion_2}}

**Planner から JuniorBuilder / Builder への引き継ぎ要点**:
{{planner_handoff_summary}}

---

## Draft Generation (JuniorBuilder)

<!--
  JuniorBuilder を使わなかった場合はこのセクションを「該当なし」に変更してよい
-->

**JuniorBuilder**: {{draft_summary}}

生成物:
- {{draft_output_description}}

**JuniorBuilder から Builder への引き継ぎ要点**:
{{junior_builder_handoff_summary}}

---

## Build

**Builder**: {{build_summary}}

作成物:
- {{what_was_built}}

採用した判断:
- {{decision_1}}
- {{decision_2}}

Plan からの逸脱:
- {{deviation_or_none}}

**Builder から Critic への引き継ぎ要点**:
{{builder_handoff_summary}}

---

## Review

**Critic**: {{review_summary}}

評価結果:
- Critical: {{critical_issues_or_none}}
- Major: {{major_issues_or_none}}
- Minor: {{minor_issues}}

総合評価: {{overall_assessment}}

**Critic から Judge への引き継ぎ要点**:
{{critic_handoff_summary}}

---

## Judge Decision

**Judge**: {{judge_decision}}

判断: **{{adopt_or_revise_or_reject}}**

理由:
{{decision_reason}}

次 iteration スコープ:
- {{next_iteration_item_1}}
- {{next_iteration_item_2}}

---

## Result

**Human**: {{result_summary}}

成功基準の充足:
{{success_criteria_result_table}}

総合判定: {{overall_verdict}}

---

## Generalization Notes

<!--
  result.md の Generalization セクションの要点を抜粋する
  原文は result.md を参照すること
-->

{{generalization_key_points}}

**再利用できるパターン**:
- {{reusable_pattern_1}}
- {{reusable_pattern_2}}

---

## Framework Notes

<!--
  result.md の Framework Feedback セクションの要点を抜粋する
-->

{{framework_feedback_summary}}

---

*このファイルは二次成果物です。正確な情報は各 .md ファイルを参照してください。*
*参照元: execution-assignment.md / goal.md / plan.md / handoff.md / build.md / review.md / improve.md / result.md*
