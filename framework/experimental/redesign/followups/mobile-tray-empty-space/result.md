# Result

---

## Status

Completed

---

## Diagnosis

The empty space below the horizontal mobile piece-selection area was not caused
primarily by tray card height.

The main cause was the combination of:

- mobile `.missing-section` stretching with `flex: 1`
- the parent sidebar keeping a fixed mobile height

This made the tray region occupy more vertical space than its content needed,
which showed up visually as dead space below the horizontal scroll area.

So the result was closer to:

- tray height: not primary
- parent spacing/stretch: primary
- mobile-only layout rule: primary

---

## What Changed

In the mobile layout rules for the SoChi BLOCKS viewer:

- `.missing-section` was changed from stretch behavior to content-height-oriented
  behavior
- `.missing-overlay` bottom padding was reduced
- `.piece-tray` bottom padding was reduced

The fix stayed in CSS and remained local to the tray zone.

---

## Why This Fix

This was the smallest change that addressed the observed cause directly.

It avoided:

- tray interaction redesign
- component structure changes
- desktop layout changes
- broader responsive cleanup

---

## Verification

- CSS cause identified before patching
- frontend build passed after the change
- the fix remained local and did not require multi-file layout restructuring

Build note:

- `npm run build` succeeded
- only the existing large-chunk warning remained

---

## Scope Check

The change stayed within the intended boundary:

- one layout area
- CSS-only adjustment
- no viewer behavior change

The follow-up did not widen into general mobile layout redesign.

---

## Stable Baseline

This follow-up confirmed a useful pattern:

- observe a visual issue in product validation
- diagnose whether it is content-size or parent-layout driven
- apply the smallest fix at the actual source

For this issue, parent/mobile layout rules mattered more than tray content size.

---

## Next Trigger

If mobile play still feels visually uneven later, the next natural question is:

- whether the entire mobile sidebar height strategy should be reconsidered

That would be a different and broader follow-up.
