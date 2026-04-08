# Build

---

## Branch Taken: A (already implemented path)

The investigation revealed that the recommendation infrastructure is already
present:

- `VictoryOverlay.tsx` renders a "Next Puzzle" link when `nextPuzzleId` is
  provided
- `App.tsx` holds `nextPuzzleId` state, reads `manifest.json`, and passes the
  value to `VictoryOverlay`
- `manifest.json` has `id / date / difficulty` with a stable ordering

The task is not to build from scratch.
The task is to verify the existing path works as intended and tune if needed.

---

## Investigation Summary

| Item | Finding |
|---|---|
| Post-clear surface | `VictoryOverlay.tsx` — already exists |
| `nextPuzzleId` state | Already in `App.tsx` |
| Manifest read + next-ID logic | Already in `App.tsx` |
| Manifest structure | `id / date / difficulty` — orderable |
| Surface → rule connection | Already wired to `VictoryOverlay` |

---

## What to Check and Adjust

### Check 1 — VictoryOverlay copy

Does the current "Next Puzzle" wording read as a natural recommendation,
or does it feel mechanical?

- If it reads naturally: no copy change needed
- If it feels flat: adjust to one short recommendation-framing line
  (e.g., "次はこれはどう？" / "Try this next →")

### Check 2 — Manifest ordering vs recommendation intent

Does the current `nextPuzzleId` calculation follow the `manifest.json` order
in a way that gives a sensible recommendation?

- Same difficulty → next ID: good
- Jumps difficulty unexpectedly: adjust the selection logic in `App.tsx`
- End of list → no next: confirm the null/empty case is handled gracefully

### Check 3 — Null/empty case

When there is no next puzzle (end of list, or manifest not loaded):

- Confirm `VictoryOverlay` handles `nextPuzzleId = null` without breaking
- Confirm it degrades gracefully (no broken link, no empty button)

---

## What to Change (if needed)

Changes are expected to be small:

| Change | File | Condition |
|---|---|---|
| Copy adjustment | `VictoryOverlay.tsx` | If wording feels mechanical |
| Next-ID selection logic | `App.tsx` | If ordering jumps difficulty unexpectedly |
| Null-case handling | `VictoryOverlay.tsx` or `App.tsx` | If not already graceful |

No new files. No new state. No routing change.

---

## What Was Not Done

- No recommendation engine
- No personalization
- No localStorage tracking
- No puzzle-list redesign
- No new surface introduction

---

## Verification Steps

1. Clear a puzzle — does `VictoryOverlay` show a next-puzzle recommendation?
2. Is the recommended puzzle sensible (same difficulty, next in sequence)?
3. Does the wording feel like a recommendation, not just a navigation link?
4. Clear the last puzzle in the list — does the null case degrade gracefully?
5. Confirm `npm run build` passes

---

## Result Evaluation Frame

result.md should answer:

1. Was the existing path sufficient, or were adjustments needed?
2. What was adjusted (copy / ordering logic / null handling)?
3. Does the after-clear moment now feel like a recommendation rather than
   just a next-page link?
4. Did the change stay within the existing files?
