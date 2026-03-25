# FW Improvement Note

Date: 2026-03-20
Theme: Heavy `plan.md` generation should decompose before timeout expansion
Scope: Planner UX / `apsf-claude-act.ps1` / `-UntilPlan` operation

---

## Observation

run `2026-03-19-027_apsf_role-boundary-execution-guard` succeeded in
generating `execution-assignment.md`, but `plan.md` generation timed out even
after the wrapper timeout was extended to 600 seconds.

Observed pattern:

- setup-sized output succeeds
- heavy design-plan output stalls for 10 minutes and returns no file
- wrapper UX is now better, but the planning unit itself is still too large

This suggests the main problem is not only timeout length. The problem is that
some runs ask Planner to produce too much structure in one pass.

---

## Hypothesis

`plan.md` generation should be treated as variable-weight work.

In lighter runs, one-shot `-UntilPlan` is fine.
In heavier design runs, Planner should generate the plan in stages, for example:

1. problem structure / hypotheses / selected approach
2. build policy / execution plan / readiness

Timeout extension is still useful as a safety margin, but it should not be the
primary answer to heavy-plan failure.

---

## Proposed Improvements

1. Introduce a "heavy-plan" mode for `-UntilPlan`
   - first create a shorter plan skeleton
   - then fill execution details in a second pass

2. Add plan-budget guidance by P-TYPE
   - heavy design / framework runs should request fewer options and shorter
     first-pass outputs

3. Add prompt-weight heuristics
   - if goal / setup size exceeds a threshold, default to staged planning

4. Keep timeout configurable, but treat it as secondary
   - decomposition first
   - timeout second

---

## Why This Matters

Current UX can now explain waiting and timeout clearly, which is a real
improvement. But if heavy runs still routinely hit timeout, the framework will
keep pushing users toward manual recovery.

This is not only a wrapper issue. It is a planning-architecture issue.

---

## Follow-up Candidate

`apsf_heavy-plan-decomposition`

Goal:
- define when `plan.md` should be staged,
- define the minimum first-pass plan,
- update wrapper / planner prompts to support it.
