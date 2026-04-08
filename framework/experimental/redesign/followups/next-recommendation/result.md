# Result
---
## Outcome

`next-recommendation` closed as a narrow adjustment, not a new recommendation engine.

- Surface taken: `S-1 after-clear`
- Rule taken: `R-1 next ID`
- Result: `VictoryOverlay` now recommends the next puzzle within the same daily set, not the next raw item in manifest order

## What Was Confirmed

The investigation showed that the core path already existed.

- `VictoryOverlay` already accepted `nextPuzzleId`
- `App.tsx` already passed `nextPuzzleId` into the overlay
- `manifest.json` already contained enough puzzle IDs to derive a next recommendation

So the task was not "build recommendation from zero." It was "check and adjust the existing path."

## What Changed

In the SoChi BLOCKS repo:

- `frontend/src/App.tsx`
  - changed `nextPuzzleId` calculation from `manifest[idx + 1]`
  - now filters to the same `YYYYMMDD_*` group and picks the next higher numeric suffix
  - explicitly sets `null` when there is no next puzzle or manifest lookup fails
- `frontend/src/components/VictoryOverlay.tsx`
  - changed copy from `Next Puzzle →` to `Try the next puzzle →`

## Why This Branch Was Correct

The original manifest order is reverse-chronological and grouped by date, so `idx + 1` could jump from:

- `20260330_001` -> `20260329_004`

That is a navigation rule, but not a good recommendation rule.

The adjusted rule is better aligned with user expectation after clear:

- `20260330_001` -> `20260330_002`
- `20260330_002` -> `20260330_003`
- `20260330_003` -> `20260330_004`
- `20260330_004` -> `null`

This keeps recommendation continuity inside the same daily set and avoids difficulty-crossing jumps caused only by manifest ordering.

## Verification

- `npm run build` succeeded in `frontend/`
- null case is now handled explicitly
- the change stayed within the existing after-clear overlay path

## Stable Baseline

`next-recommendation` did not require a new surface or new state model.

The stable baseline is now:

1. recommendation appears only after clear
2. recommendation stays inside the same daily batch
3. the last puzzle in the batch safely shows no recommendation
