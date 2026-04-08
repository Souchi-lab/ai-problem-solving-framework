# Execution Assignment

<!-- APSF CONTRACT: one run has one execution-assignment.md -->
<!-- Keep this file focused on execution ownership and role boundaries. -->
<!-- Do not use this file as a long PM brief or tool manual. -->

---

## Run Name

<!-- Folder name under runs/ -->

## Goal Summary

<!-- Summarize goal.md in 1-3 lines -->

---

## Role Execution Assignments

<!-- Keep the standard role table. -->
<!-- Planner / Critic specialist tags are optional and belong in Notes only when relevant. -->

| Role | Execution Type | Tool / Method | Workspace | Notes |
|---|---|---|---|---|
| Planner | human | Human / Codex | workspaces/planner/ | Main planning responsibility and planning boundary |
| JuniorBuilder | cli | gemini-cli | workspaces/junior_builder/ | Optional draft / low-risk support only if useful |
| Builder | cli | claude / codex | workspaces/builder/ | Main implementation responsibility and build boundary |
| Critic | human / cli | Human / Codex | workspaces/critic/ | Main review lens and acceptance concerns |
| Judge | human | Human | workspaces/judge/ | Final accept / continue decision standard |

---

## Minimum Procedure

<!-- Record only the durable core. The viewer already carries phase, actions, and recent execution state. -->

### Planner

1. Read `goal.md`
2. Write `plan.md`
3. Leave `handoff.md` only if the next role needs transfer context that canonical artifacts do not already carry

### Builder

1. Read `plan.md`
2. Implement the scoped work
3. Write `build.md`

### Critic

1. Read `plan.md` and `build.md`
2. Review with the assigned lens
3. Write `review.md`

### Judge

1. Read `review.md`
2. Decide whether to continue or adopt
3. Write `improve.md` or `result.md`

---

## Why This Execution Plan

<!-- Explain only why this role split is appropriate for this run. -->

- 

---

## Operational Risks

<!-- Record only meaningful execution risks for this run. -->

- [ ]

---

## Optional Specialist Notes

### Planner Specialist

- Primary P-TYPE:
- Specialist Path:
- Selection Basis:

### Critic Specialist

- Primary C-TYPE:
- Specialist Path:
- Selection Basis:

### Builder Specialist

- Primary B-TYPE:
- Specialist Path:
- Selection Basis:
