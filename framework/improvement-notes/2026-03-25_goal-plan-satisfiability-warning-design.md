# Goal-Plan Satisfiability Warning Design

Date: 2026-03-25
Source run: `2026-03-25-015_apsf_goal-plan-satisfiability-gate`

---

## Problem

APSF can accept a `plan.md` that is internally coherent while still being
unsatisfiable against the run's own success criteria and unresolved required
prerequisites.

Current failure pattern:

1. `goal.md` requires execution-ready output or strict verification.
2. `plan.md` leaves required prerequisites unresolved.
3. Existing readiness language does not clearly surface the contradiction.
4. Builder proceeds provisionally.
5. Critic/review becomes the first explicit detection point.

This is a signal problem before it is a phase problem.

---

## Design Position

This improvement keeps the current phase model unchanged.

It does **not** introduce:

- a new phase such as `PLAN_BLOCKED`
- a hard stop before Builder
- a broad workflow redesign

Instead, it adds a satisfiability classification signal to existing readiness
surfaces and makes that signal visible through existing `decision_reason`
display paths.

---

## Classification

### `SATISFIED`

All prerequisites required by the goal's success criteria are resolved or have
an explicit accepted substitute.

Framework behavior:

- proceed normally
- no warning required

### `EXPLORATORY`

The run is explicitly provisional or exploratory, and the goal does not require
execution-ready output at the current stage.

Framework behavior:

- proceed normally
- optional low-severity note only

### `UNSATISFIED`

The goal requires execution-ready output or strict verification, but the plan
leaves one or more required prerequisites unresolved.

Framework behavior:

- phase stays unchanged
- Builder may still proceed in this iteration
- contradiction is surfaced as an additive warning

---

## Source Surfaces

The warning should be derived from existing APSF surfaces, not a new gate:

- `Goal Readiness Check`
- `Implementation Readiness`
- `Assumptions & Open Questions`
- `decision_reason`

The primary extension point is `Implementation Readiness`, because it already
sits closest to the build boundary.

---

## decision_reason Contract

When classification is `UNSATISFIED` or `EXPLORATORY`, `decision_reason` should
carry short, readable text that Viewer can surface directly.

Recommended format:

```text
[SATISFIABILITY: UNSATISFIED] Required prerequisites unresolved: CAD model, material.
Goal success criteria require execution-ready output, so this run proceeds with a visible contradiction warning.
```

Recommended exploratory format:

```text
[SATISFIABILITY: EXPLORATORY] Unknowns remain, but the current goal is explicitly provisional.
No execution-readiness contradiction is detected.
```

For `SATISFIED`, no extra marker is required.

---

## Viewer Display Rule

Viewer should continue showing the current phase badge unchanged.

When `decision_reason` contains a satisfiability marker:

- display it in the existing explanation/readiness area
- keep it additive to the current phase display
- visually distinguish warning severity through copy/styling only
- do not map it to a new phase or new run state

This keeps the UX stable while making the contradiction legible earlier.

---

## Trigger Example

`2026-03-25-011_work_whiskey-5axis-v2` should classify as `UNSATISFIED`.

Reason:

- goal required strict feasibility verification
- plan left CAD, material, and machine configuration unresolved
- build could only rationally produce a provisional design

The contradiction was therefore detectable before Critic fail, even though APSF
did not surface it clearly.

---

## Follow-On Scope

Suggested implementation run:

- extend plan template guidance to require satisfiability classification in
  `Implementation Readiness`
- define where `decision_reason` is populated from that classification
- confirm Viewer displays the warning through the existing explanation area

This follow-on should remain additive and should not change the phase model.
