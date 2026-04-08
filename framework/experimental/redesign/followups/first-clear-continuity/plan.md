# Plan

---

## Follow-up Context

- Parent series: SoChi BLOCKS public-site improvement follow-ups
- Previous result: `next-recommendation` added a "Try the next puzzle →" link
  in `VictoryOverlay` after clear, using the same-day batch rule
- New trigger: having a next-puzzle link is not the same as making continuity
  feel natural; the gap may be in emphasis, competing elements, or copy
- Scope limit: post-clear surface only, no progression system change

---

## Run Metadata

- Pattern: P-01 Feature Implementation (conditional — gap type must be
  confirmed before writing any change)
- Goal: identify what weakens first-clear continuity in the current overlay
  and apply the smallest fix
- Output focus: gap diagnosis → targeted copy / emphasis / action-path change

---

## Goal Readiness Check

- `VictoryOverlay.tsx` already exists with a next-puzzle link
- `next-recommendation` already wired the same-day batch rule
- The open question is whether the current overlay makes "one more puzzle"
  feel natural enough for a first-time player
- This can be diagnosed by reading the overlay's current element structure

Decision: Proceed — with gap-type confirmation first

---

## Problem Structure

### What to confirm

Three possible gap sources:

| Type | Description | Fix direction |
|---|---|---|
| C-1: Weak next action | The "next puzzle" link exists but does not read as the primary action | Emphasis — make it visually primary |
| C-2: Competing elements | Other buttons or copy dilute the next-puzzle path | Reduction — simplify what is shown |
| C-3: Missing action in null case | When `nextPuzzleId` is null, there is no continuity path at all | Addition — add a fallback action |

More than one type can be present simultaneously.

### Key question

Does a first-time player, just after clearing, see **one clear next step**?

If yes: no change needed, close with that observation.
If no: identify which type (C-1 / C-2 / C-3) is responsible and fix narrowly.

---

## Investigation Steps

1. Read `VictoryOverlay.tsx` — what elements are currently rendered?
2. Identify all visible actions / buttons / links after clear
3. Check which element is visually primary (size, position, style)
4. Check the null case (`nextPuzzleId === null`) — what does the user see?
5. Determine gap type (C-1 / C-2 / C-3 / none)

---

## Fix Directions by Gap Type

### C-1: Emphasis fix

If the next-puzzle link exists but is not visually primary:

- Elevate the "Try the next puzzle →" element
- Could be: larger text, button style, top position in overlay
- Copy may also be adjusted if it reads as secondary

### C-2: Reduction fix

If competing elements dilute the next step:

- Remove or de-emphasize lower-priority elements in the overlay
- Do not add new elements — simplify what is already there

### C-3: Null-case addition

If there is no continuity path when `nextPuzzleId` is null:

- Add one fallback action: "Try another difficulty →" or "Back to puzzles →"
- One element only, no new recommendation logic

Fixes can be combined if multiple types are present, but keep the total
change to one component.

---

## Execution Plan

- [ ] Step 1: Read `VictoryOverlay.tsx` and identify current element structure
- [ ] Step 2: Determine gap type(s): C-1 / C-2 / C-3 / none
- [ ] Step 3: Select fix direction(s) — copy / emphasis / action-path
- [ ] Step 4: Apply the change in `VictoryOverlay.tsx`
- [ ] Step 5: Live check — does the post-clear moment now have one clear next step?
- [ ] Step 6: Write result.md

---

## Implementation Readiness

- [ ] Current overlay element structure read before writing any change
- [ ] Gap type identified before selecting fix
- [ ] Change stays in `VictoryOverlay.tsx` (and `App.css` if styling only)
- [ ] `next-recommendation` logic (`nextPuzzleId` calculation) not modified

---

## Scope Policy

Allowed:
- visual emphasis change in `VictoryOverlay`
- copy adjustment in `VictoryOverlay`
- one fallback action for null case
- CSS adjustment for overlay elements

Not allowed:
- `nextPuzzleId` calculation change (owned by `next-recommendation`)
- new progression or achievement logic
- top-page navigation change
- viewer layout change outside the overlay

---

## Deliverables

- gap type diagnosis (C-1 / C-2 / C-3 / none)
- targeted fix or "no change needed" observation
- result.md with post-clear clarity verdict

---

## Review Policy

Review can be skipped if:
- change stays in one component
- gap type is clear

---

## Result Evaluation Frame

result.md should answer:

1. What gap type(s) were found (C-1 / C-2 / C-3 / none)?
2. What was changed (emphasis / copy / action-path / nothing)?
3. Does the post-clear moment now have one clear next step?
4. Did the change stay within `VictoryOverlay.tsx`?
