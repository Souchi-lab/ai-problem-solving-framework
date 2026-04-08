# Plan

---

## Follow-up Context

- Parent series: SoChi BLOCKS public-site improvement follow-ups
- Previous result: `operation-mode-split` separated move/place vs rotate hints
  visually; current-mode cue was noted as a possible next step but deferred
- New trigger: label grouping is now in place; question is whether a live
  mode indicator would add meaningful clarity
- Scope limit: viewer UI cue only, no control model change

---

## Run Metadata

- Pattern: P-01 Feature Implementation (conditional — see branching below)
- Goal: add a lightweight current-mode cue to the viewer if mode state is
  surfaceable, or close with a design record if not
- Output focus: investigation → implementation or bounded design

---

## Goal Readiness Check

- `operation-mode-split` already established the two-group hint structure
- The cue needs to align with that structure (not replace it)
- Whether a mode state exists in the viewer React state is the open question
- The run can close either as implementation (mode surfaceable) or design
  record (mode not surfaceable without deeper change)

Decision: Proceed — with a conditional branch

---

## Problem Structure

From `operation-mode-split`, the viewer now shows:

```
📍 置く場所を決める  ← → (cursor move)
🔄 向きを回す        ← → (rotate)
```

The player can read both groups but does not currently see which one is
"active right now." The cue should answer:

> "Which kind of action am I doing at this moment?"

The minimum form of that answer is something like:

- a highlighted active group
- a small "Now: ..." label above or between the two groups
- a state-dependent sublabel attached to the active group

All three rely on the game having a surfaceable current-mode concept.

---

## Key Investigation Question

Does the viewer have a concept of "current mode" or "current phase" in its
React state?

In SoChi BLOCKS, the same keys (`← →`) behave differently depending on
context:

- rotation phase: `← →` rotates the piece
- placement phase: `← →` moves the cursor

This suggests a mode or phase concept exists in the game logic.
The question is whether it is accessible from the hint-area component.

---

## Conditional Branch

### Branch A — Mode state is surfaceable

If the viewer exposes a mode or phase value accessible from the hint component:

- Add a small visual cue tied to that state
- Highlight or annotate the active group
- P-01 implementation: one component change

### Branch B — Mode state is not directly surfaceable

If no mode state is exposed at the hint level:

- Assess whether a small state lift or prop is feasible without restructuring
- If feasible in one change: implement it and the cue together
- If not feasible without broader refactor: close as design record + deferred

Branch B does not automatically mean "do nothing." It means assess the
cost first.

---

## Investigation Steps

1. Find the hint-area component introduced in `operation-mode-split`
2. Check what state or props it currently receives
3. Find where the rotation/placement phase is tracked in the viewer logic
4. Assess whether passing that state to the hint component is a small change

These four checks determine the branch.

---

## Cue Design (for Branch A or feasible Branch B)

| Form | Description | Cost |
|---|---|---|
| Active group highlight | The current group gets a border, background, or text weight change | CSS only |
| "Now: ..." label | A single line above the hint block showing current mode text | One state-bound element |
| State sublabel | Each group shows a sublabel when active ("← currently rotating") | Slightly more markup |

Prefer the smallest form that is readable at a glance.
The cue should not make the HUD feel busier than it currently does.

---

## Execution Plan

- [ ] Step 1: Find the hint-area component and check its current props/state
- [ ] Step 2: Locate the phase/mode state in the viewer logic
- [ ] Step 3: Determine branch (A or B) and cue form
- [ ] Step 4 (Branch A / feasible B): Implement the cue
- [ ] Step 4 (infeasible B): Write design record and close
- [ ] Step 5: Live inspection — does the cue read clearly without making the
  HUD busy?
- [ ] Step 6: Write result.md with branch taken, cue form chosen, and verdict

---

## Implementation Readiness

- [ ] Mode state location confirmed before writing code
- [ ] Branch selected before implementation
- [ ] Cue form chosen for minimum visual weight
- [ ] Change stays in hint-area component or one adjacent component
- [ ] `operation-mode-split` hint structure is preserved

---

## Scope Policy

Allowed:
- hint-area component state binding
- small CSS change for active group highlight
- one state-bound label element

Not allowed:
- control model change
- input remapping
- new mode system introduction
- HUD-wide layout change
- broader interaction redesign

---

## Deliverables

- branch determination with rationale
- implementation (Branch A or feasible B) or design record (infeasible B)
- result.md: was the cue worth adding after `operation-mode-split`?

---

## Review Policy

Review can be skipped if:
- the change is one component with a small state binding
- the branch determination is clear

Restore review if investigation reveals the mode state requires lifting
through multiple component layers.

---

## Result Evaluation Frame

result.md should answer:

1. Which branch was taken, and why?
2. What cue form was chosen?
3. Does it improve moment-to-moment clarity without making the HUD busy?
4. Was it worth adding after `operation-mode-split`, or was the label split
   already enough?
5. Did the change stay local to the hint area?
