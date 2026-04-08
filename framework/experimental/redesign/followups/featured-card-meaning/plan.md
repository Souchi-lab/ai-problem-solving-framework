# Plan

---

## Follow-up Context

- Parent series: SoChi BLOCKS public-site improvement follow-ups
- Previous result: `puzzle-list-selection-clarity` confirmed that the puzzle
  list is already clear enough, and noted that "first puzzle / featured /
  today's puzzle" serves as the H-3 signal for the list
- New trigger: if the featured card serves as the "start here" signal,
  it should be legible as such — its role and reason for being highlighted
  should be clear to a first-time user
- Scope limit: featured card surface only

---

## Run Metadata

- Pattern: P-02 Bug Fix
- Goal: identify whether the featured card's meaning is currently ambiguous
  and apply the smallest fix, or record "no change needed" if it is already
  clear
- Output focus: ambiguity diagnosis → copy / label fix, or confirmed no-change

---

## Goal Readiness Check

- The featured card already exists on the top page
- `puzzle-list-selection-clarity` noted it as the "start here" signal
- The open question is whether its label and meaning are legible without context
- This can be diagnosed by reading the card's current content

Decision: Proceed — with ambiguity-source confirmation first

---

## Problem Structure

### What to confirm

Three possible ambiguity sources:

| Type | Description | Fix direction |
|---|---|---|
| A-1: Label does not explain why | Card is highlighted but gives no reason (e.g., just "Featured" with no context) | Copy — add a one-line reason |
| A-2: Role overlaps with nearby surfaces | First-puzzle and featured card look the same or serve the same role | Differentiation — clarify what makes featured distinct |
| A-3: Meaning depends on external context | The card is understandable only if the user already knows what "today's puzzle" means | Copy — add a minimal contextual cue |

Or none — in which case "no change needed" is the result.

### Key question

Can a first-time user understand why this card is highlighted and whether
they should start here?

If yes → no change needed.
If no → which ambiguity type (A-1 / A-2 / A-3) and what is the smallest fix?

---

## Relationship to Previous Follow-ups

| Follow-up | What it addressed |
|---|---|
| `difficulty-card-clarity` | Which difficulty level to pick |
| `puzzle-list-selection-clarity` | Which puzzle in the list to pick |
| `featured-card-meaning` | Why this specific card is surfaced at the top |

The featured card sits above the difficulty selection in the decision flow.
If it is confusing, it creates friction before the user even reaches difficulty selection.

---

## Investigation Steps

1. Read the featured card's current label, subtitle, and any descriptive copy
2. Check what the card communicates without any prior context
3. Check how it differs visually and textually from the first-puzzle card and
   puzzle list cards
4. Determine ambiguity type (A-1 / A-2 / A-3 / none)

---

## Fix Directions by Ambiguity Type

### A-1: Add a reason to the label

If the card is highlighted but gives no reason:

- Add a short subtitle: "今日のおすすめ" / "Today's pick"
- Or annotate the label with a one-line context cue
- Keep it one line — do not add a description block

### A-2: Differentiate from nearby surfaces

If featured and first-puzzle overlap in role:

- Clarify what makes the featured card distinct in copy or badge
- Or consolidate — if they serve the same role, decide which to keep

### A-3: Add minimal contextual cue

If meaning depends on prior knowledge:

- Add a very short cue that makes the role self-evident
  (e.g., "毎日更新 / Updated daily" or "今日のパズル / Today's puzzle")
- One element only

---

## Execution Plan

- [ ] Step 1: Read featured card content and structure in `docs/index.html`
- [ ] Step 2: Determine ambiguity type(s): A-1 / A-2 / A-3 / none
- [ ] Step 3: Select fix — copy / label cue / no change
- [ ] Step 4 (if change needed): Apply fix in `docs/index.html`
- [ ] Step 5: Check — can a first-time user now understand why this card is here?
- [ ] Step 6: Write result.md

---

## Implementation Readiness

- [ ] Current featured card content read before writing any fix
- [ ] Ambiguity type confirmed before choosing direction
- [ ] Change stays in `docs/index.html` (featured card section only)
- [ ] `difficulty-card-clarity` and `puzzle-list-selection-clarity` not modified

---

## Scope Policy

Allowed:
- featured card label or subtitle copy
- one small contextual cue element
- CSS adjustment for featured card only

Not allowed:
- full top-page redesign
- difficulty section changes
- puzzle list restructuring
- recommendation logic changes

---

## Deliverables

- ambiguity type diagnosis (A-1 / A-2 / A-3 / none)
- fix or "no change needed" observation
- result.md with featured card clarity verdict

---

## Review Policy

Review can be skipped if:
- change stays in one section of one file
- ambiguity type is clear

---

## Result Evaluation Frame

result.md should answer:

1. What ambiguity type(s) were found (A-1 / A-2 / A-3 / none)?
2. What was changed (copy / label cue / nothing)?
3. Can a first-time user now understand why the featured card is highlighted?
4. Did the change stay local to the featured card section?
