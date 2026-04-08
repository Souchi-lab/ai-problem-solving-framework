# Plan

---

## Follow-up Context

- Parent series: SoChi BLOCKS public-site improvement follow-ups
- Previous results: featured-card-meaning added a one-line reason to the
  featured card; puzzle-list and first-clear surfaces are now clear enough
- New trigger: the top-page progress area shows numbers/chips but a
  first-time user may not know what they count or why they matter
- Scope limit: progress summary area only, no system redesign

---

## Run Metadata

- Pattern: P-02 Bug Fix
- Goal: identify what makes the progress area hard to read at a glance and
  apply the smallest fix, or confirm no change needed
- Output focus: ambiguity diagnosis → copy / label fix or confirmed no-change

---

## Goal Readiness Check

- The progress area already exists on the top page
- The open question is whether its numbers/chips are self-explanatory
- This can be diagnosed by reading the current progress area content
- "No change needed" is a valid result

Decision: Proceed — with ambiguity-source confirmation first

---

## Problem Structure

### What to confirm

Three possible ambiguity sources:

| Type | Description | Fix direction |
|---|---|---|
| P-1: What the numbers count | Numbers or chips are shown but the user cannot tell what they represent (cleared puzzles? total available? today's?) | Label or unit copy |
| P-2: Local vs account progress unclear | Not obvious that progress is stored locally in the browser, not tied to an account | Short context cue |
| P-3: Empty / zero-clear state | The first-time user sees 0 clears and does not know if this is a problem or expected | Empty-state copy |

Or none — "no change needed" if the area is already self-explanatory.

### Key question

Can a first-time user read the progress area and understand:
- what is being counted?
- whether it reflects their own activity?
- whether seeing 0 clears is normal at the start?

---

## Investigation Steps

1. Read the progress area in `docs/index.html` — what is displayed?
2. Check each number/chip: does its label explain what it counts?
3. Check whether "local/browser progress" is communicated anywhere nearby
4. Check what the area shows for a zero-clear state
5. Determine ambiguity type (P-1 / P-2 / P-3 / none)

---

## Fix Directions by Type

### P-1: Add unit or label

If numbers have no label or unit:

- Add a short label per number: "クリア済み / Cleared", "挑戦中 / In progress"
- One label per metric, no description block

### P-2: Add local-progress context cue

If it is not clear that progress is browser-local:

- Add a one-line cue near the progress area: "このブラウザの記録 / Saved in this browser"
- One line only — do not over-explain

### P-3: Improve empty-state copy

If 0 clears looks broken or discouraging:

- Add a short prompt for the zero state: "まだクリアなし — 最初の1問を試してみよう"
- Or soften the display to feel like a starting point, not a failure

---

## Execution Plan

- [ ] Step 1: Read progress area content and structure
- [ ] Step 2: Determine type(s): P-1 / P-2 / P-3 / none
- [ ] Step 3: Select fix direction
- [ ] Step 4 (if change needed): Apply fix in `docs/index.html`
- [ ] Step 5: Check — can a first-time user now read the progress area without confusion?
- [ ] Step 6: Write result.md

---

## Implementation Readiness

- [ ] Current progress area content read before writing any fix
- [ ] Ambiguity type confirmed before choosing direction
- [ ] Change stays in progress area section of `docs/index.html`
- [ ] Progress system logic not modified

---

## Scope Policy

Allowed:
- label or unit copy on progress metrics
- one local-progress context cue
- empty-state copy improvement
- CSS adjustment for progress area only

Not allowed:
- progress system logic change
- account / sync feature
- leaderboard or achievement system
- full top-page redesign

---

## Deliverables

- ambiguity type diagnosis (P-1 / P-2 / P-3 / none)
- fix or "no change needed" observation
- result.md with progress clarity verdict

---

## Review Policy

Review can be skipped if:
- change stays in one section of one file
- ambiguity type is clear

---

## Result Evaluation Frame

result.md should answer:

1. What type(s) were found (P-1 / P-2 / P-3 / none)?
2. What was changed (label / context cue / empty-state copy / nothing)?
3. Can a first-time user now read the progress area without confusion?
4. Did the change stay local to the progress area section?
