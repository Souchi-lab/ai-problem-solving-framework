# Plan

---

## Follow-up Context

- Parent series: SoChi BLOCKS public-site improvement follow-ups
- Previous results: entry friction, difficulty clarity, and viewer interaction
  clarity are now improved; "what do I do next?" is the remaining hesitation
- New trigger: after initial selection or clear, there is no signal pointing
  to a next reasonable puzzle
- Scope limit: one recommendation, one rule, one UI surface

---

## Run Metadata

- Pattern: P-01 Feature Implementation (conditional — surface and rule must be
  confirmed before implementation)
- Goal: add a lightweight deterministic next-puzzle recommendation at the most
  cost-effective UI surface
- Output focus: surface selection + simple rule + narrow implementation

---

## Goal Readiness Check

- The improvement goal is clear: reduce "what next?" hesitation
- The rule should be deterministic and stateless (no localStorage, no ranking)
- The surface needs to be confirmed via investigation before writing code
- The run can close as P-01 if surface + rule fit in a local change, or
  as P-06 if the best surface requires new architecture

Decision: Proceed — with surface confirmation step first

---

## Problem Structure

### Two decisions to make before implementation

**Decision 1 — Rule**

What determines the next recommendation?

| Option | Rule | Cost | Dependency |
|---|---|---|---|
| R-1 | Same difficulty, next puzzle ID | Very low | Puzzle ID ordering exists |
| R-2 | Same difficulty, any puzzle (fixed pick) | Very low | Static data |
| R-3 | One difficulty step up | Low | Difficulty mapping |
| R-4 | Incomplete puzzle in same difficulty | Medium | localStorage |

Prefer R-1 or R-2 — stateless, no personalization, explainable.
R-4 is out of scope (stateful, requires localStorage tracking).

**Decision 2 — Surface**

Where does the recommendation appear?

| Surface | Trigger | Cost | Effectiveness |
|---|---|---|---|
| S-1: After-clear in viewer | `gameStatus === 'clear'` or equivalent | Low if state exists | High — natural moment |
| S-2: Viewer sidebar / hint area | Always visible when playing | Very low | Medium — competes with hints |
| S-3: Top page near puzzle list | Static HTML addition | Low | Medium — seen before play |

Prefer S-1 if viewer has a clear-state.
S-3 is the fallback if S-1 requires new viewer architecture.

---

## Investigation Steps

1. Check if `useGameState.ts` or `App.tsx` has a post-clear state
   (e.g., `gameStatus === 'clear'`, `isClear`, completion callback)
2. Check if puzzle data has a stable ID/order that supports R-1 or R-2
3. If S-1 is not feasible, check whether S-3 (top page) has a suitable
   static slot near the difficulty section or puzzle list

These three checks determine the surface and rule.

---

## Conditional Branch

### Branch A — Viewer has post-clear state

If `useGameState` or `App.tsx` already surfaces a clear/completion state:

- Place the recommendation in the after-clear moment (S-1)
- Use R-1 or R-2 for the rule
- Add a small "次のパズルへ / Next puzzle →" prompt with a link or button
- Change is local to `App.tsx`

### Branch B — No post-clear state, top page is the fallback

If the viewer has no accessible clear state:

- Place the recommendation near the difficulty entry area on the top page (S-3)
- Use R-2 (fixed static pick per difficulty) as the rule
- Add one line of copy + link per difficulty level: "次はこれ → [link]"
- Change is local to `docs/index.html`

### Branch C — Neither surface is feasible without new architecture

- Close as P-06: document what would be needed
- Defer to a structural follow-up

---

## Execution Plan

- [ ] Step 1: Check for post-clear state in viewer (S-1 feasibility)
- [ ] Step 2: Check puzzle data for ID/order (R-1 / R-2 feasibility)
- [ ] Step 3: Select branch (A / B / C) and confirm rule
- [ ] Step 4: Implement the recommendation at the selected surface
- [ ] Step 5: Verify — does "what next?" become easier to answer?
- [ ] Step 6: Write result.md with surface chosen, rule used, and verdict

---

## Implementation Readiness

- [ ] Post-clear state availability confirmed (or ruled out)
- [ ] Puzzle data ordering confirmed (or ruled out)
- [ ] Branch selected before writing code
- [ ] Change stays in one file (`App.tsx` or `docs/index.html`)
- [ ] Recommendation is one item, not a list

---

## Rule Constraints (applies to any branch)

- One recommendation only
- Deterministic — same input always gives same output
- Stateless — no localStorage, no server calls
- Explainable — "same difficulty, next in sequence" or "same difficulty, fixed pick"
- Not gamification — no points, streaks, or achievement framing

---

## Scope Policy

Allowed:
- one recommendation prompt in one surface
- one deterministic rule
- small copy + link/button

Not allowed:
- full recommendation engine
- personalization or history tracking
- multi-step progression system
- puzzle-list redesign
- analytics integration

---

## Deliverables

- surface and rule determination record
- implementation (Branch A or B) or design handoff (Branch C)
- result.md: did "what next?" become easier to answer?

---

## Review Policy

Review can be skipped if:
- surface is one file, rule is one condition
- branch determination is clear

---

## Result Evaluation Frame

result.md should answer:

1. Which branch was taken (A / B / C)?
2. Which surface and rule were used?
3. Does the recommendation reduce "what next?" hesitation?
4. Did the change stay in one file?
5. Is there a remaining gap (e.g., post-clear surface still missing)?
