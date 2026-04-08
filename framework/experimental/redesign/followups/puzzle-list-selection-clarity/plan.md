# Plan

---

## Follow-up Context

- Parent series: SoChi BLOCKS public-site improvement follow-ups
- Previous results: difficulty-card-clarity improved top-page level selection;
  next-recommendation added continuity after clear
- New trigger: once a user selects a difficulty, they face the puzzle list —
  "which puzzle?" may still be a hesitation point
- Scope limit: puzzle list surface only, no full list redesign

---

## Run Metadata

- Pattern: P-02 Bug Fix
- Goal: identify the source of selection hesitation in the puzzle list and
  apply the smallest fix, or record "no change needed" if the list is
  already clear enough
- Output focus: hesitation source diagnosis → targeted copy / emphasis /
  grouping / ordering cue change, or confirmed no-change

---

## Goal Readiness Check

- The puzzle list already exists and is navigable
- `difficulty-card-clarity` improved the level-selection step before this
- The open question is whether the individual puzzle list adds a new hesitation
  point or is already clear enough
- This can be diagnosed by reading the current puzzle card structure

Decision: Proceed — with hesitation-source confirmation first

---

## Problem Structure

### What to confirm

Three possible hesitation sources:

| Type | Description | Fix direction |
|---|---|---|
| H-1: Cards look identical | No visual distinction between puzzle cards; user cannot tell them apart at a glance | Emphasis or ordering cue |
| H-2: Card labels are weak | Title / difficulty / date on each card does not help the user decide | Copy adjustment |
| H-3: No "start here" signal | Nothing tells a first-time user which card is the easiest or most natural first choice | Grouping or ordering cue |

More than one type can apply. Or none — in which case "no change needed" is the result.

### Key question

Can a first-time user glance at the puzzle list and pick one without hesitating?

If yes → no change needed, close with that observation.
If no → identify which type (H-1 / H-2 / H-3) and fix narrowly.

---

## Relationship to Previous Follow-ups

| Follow-up | Surface | What it addressed |
|---|---|---|
| `difficulty-card-clarity` | Top-page difficulty section | Which level to start |
| `next-recommendation` | Post-clear overlay | What to do after a clear |
| `puzzle-list-selection-clarity` | Puzzle list | Which specific puzzle to open |

This follow-up is downstream of difficulty selection, upstream of play.

---

## Investigation Steps

1. Find the puzzle list surface (top page, or a dedicated list page)
2. Read current puzzle card structure — what is shown on each card?
3. Check whether cards are visually distinguishable from each other
4. Check whether any "start here" or recommended-first signal exists
5. Determine hesitation type (H-1 / H-2 / H-3 / none)

---

## Fix Directions by Hesitation Type

### H-1: Emphasis fix

If cards look identical:

- Add a small visual distinction (e.g., piece-count, difficulty badge, date)
- Do not redesign the card layout — add one differentiating element

### H-2: Copy fix

If labels are weak:

- Adjust card title or subtitle to be more decision-helpful
- Keep copy short — one line per card

### H-3: Ordering / grouping cue

If there is no "start here" signal:

- Add a lightweight indicator on the most approachable card
- Could be: "Easy start" badge, first-card emphasis, or ordering by difficulty
- One element only — do not introduce a full recommendation system

---

## Execution Plan

- [ ] Step 1: Find the puzzle list surface and read current card structure
- [ ] Step 2: Determine hesitation type(s): H-1 / H-2 / H-3 / none
- [ ] Step 3: Select fix direction — emphasis / copy / grouping cue / no change
- [ ] Step 4 (if change needed): Apply fix, staying local to puzzle list surface
- [ ] Step 5: Check — can a first-time user now pick a puzzle without hesitating?
- [ ] Step 6: Write result.md

---

## Implementation Readiness

- [ ] Current card structure read before writing any change
- [ ] Hesitation type identified before selecting fix
- [ ] Change stays in puzzle list HTML or one component
- [ ] `difficulty-card-clarity` and `next-recommendation` not modified

---

## Scope Policy

Allowed:
- copy on puzzle cards
- one visual distinction element per card
- one "start here" style cue
- CSS adjustment for card list

Not allowed:
- full list layout redesign
- recommendation engine logic
- difficulty system change
- personalization or history tracking

---

## Deliverables

- hesitation type diagnosis (H-1 / H-2 / H-3 / none)
- fix or "no change needed" observation
- result.md with selection clarity verdict

---

## Review Policy

Review can be skipped if:
- change stays in one surface
- hesitation type is clear

---

## Result Evaluation Frame

result.md should answer:

1. What hesitation type(s) were found (H-1 / H-2 / H-3 / none)?
2. What was changed (emphasis / copy / grouping cue / nothing)?
3. Can a first-time user now pick a puzzle more easily?
4. Did the change stay local to the puzzle list surface?
