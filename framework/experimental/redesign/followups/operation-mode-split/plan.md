# Plan

---

## Follow-up Context

- Parent series: SoChi BLOCKS public-site improvement follow-ups
- Previous result: top-page and how-to improvements clarified entry and relief,
  but in-viewer operation ambiguity remains
- New trigger: move vs rotate is still one of the biggest first-play confusion
  points
- Scope limit: small viewer-side UI clarification only
- Non-goals: full input redesign, tutorial rebuild, broad HUD rewrite

---

## Run Metadata

- Follow-up: operation-mode-split
- Goal: separate position-selection vs rotation more clearly in the play UI
- Output focus: minimal viewer UI plan with a short evaluation path
- Non-goal reminder: do not widen into a full control-system redesign

---

## Goal Readiness Check

- The problem statement is already narrow: clarify prediction, not redesign all
  controls
- Earlier follow-ups already improved top-page entry and how-to framing, so this
  can stay viewer-focused
- The likely solution space is small enough to compare in one plan
- This can be judged by before/after clarity rather than long research

Decision: Proceed

---

## Execution Intent

### Main Question

What minimum viewer-side UI change best separates "where to place" from "how to
rotate" in the player's mind?

### Output Shape

- one selected small approach
- one rejected larger approach set
- one short evaluation frame for result.md

---

## Problem Structure

The current confusion is not primarily about lack of features.
It is about lack of separation between two mental models:

- selecting a placement target
- changing a piece orientation

The player should be able to infer, before acting:

- which family of action they are taking
- what the current UI hint refers to
- what kind of change to expect on screen

That means this follow-up should optimize for prediction clarity, not raw
instruction volume.

---

## Selected Approach

Approach:

- keep the existing control model
- improve the viewer's visible grouping of operations into two categories:
  `Move / Place` and `Rotate`
- add a lightweight current-state cue where possible
- prefer label/layout/icon/text grouping over deeper interaction changes

Why this approach:

- it directly targets the confusion source
- it can remain a small viewer-side change
- it avoids destabilizing existing controls
- it can be judged quickly after implementation

---

## Alternatives Considered

### A. Full control remap

Rejected for this follow-up.

Why rejected:

- too wide
- changes user muscle memory
- turns a clarity problem into a larger interaction redesign

### B. New tutorial-first solution

Rejected for this follow-up.

Why rejected:

- teaches around the problem instead of reducing it in the live UI
- broader than needed

### C. Pure copy-only fix

Rejected as insufficient by itself.

Why rejected:

- wording matters, but without visible grouping in the viewer, prediction is
  still weak

---

## Scope Policy

Allowed:

- viewer-side labels
- grouping headers
- small icon/text treatment
- current-mode or current-action cue if it fits naturally
- narrow how-to/viewer wording alignment if needed

Not allowed:

- broad input-system rewrite
- large layout redesign
- tutorial system expansion
- unrelated SEO / i18n / KPI work

---

## Deliverables

- a narrow implementation target for viewer-side move/rotate separation
- explicit record of why larger redesign was deferred
- result criteria based on prediction clarity for first-time users

---

## Working Definitions

- `Move / Place`: actions that answer "where does this piece go?"
- `Rotate`: actions that answer "what orientation should this piece have?"
- `Enough separation`: the UI no longer presents both ideas as one blended
  explanation block

---

## Result Evaluation Frame

result.md should judge at least these three points:

1. Can a first-time player more easily tell move/place from rotate?
2. Did the change stay small and local, or did it start to widen?
3. Was visible grouping enough, or is a later control-model change still needed?

---

## Review Policy

Review can be skipped if the implementation remains:

- viewer-local
- small in surface area
- free of control remapping

If the work expands into input redesign, review should be restored.

---

## Next Trigger

If this follow-up works:

- use the result as a template for other "clarity without full redesign"
  improvements in the viewer

If this follow-up is too weak:

- open a deeper follow-up focused on control-model redesign rather than UI
  grouping alone
