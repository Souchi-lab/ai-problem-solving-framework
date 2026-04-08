# Result

---

## Status

Completed

---

## Branch Taken

Branch A

The required state was already available in the viewer:

- `selectedPiece`
- `sortedAnchors.length`
- existing hint-area rendering in `App.tsx`

No meaningful state lift was required.

---

## What Changed

A lightweight current-mode cue was added above the separated hint groups in the
viewer.

The cue uses the existing live state to show:

- `今: 置く場所を選ぶ` / `Now: choosing where to place`
- `今: 向きを調整する` / `Now: adjusting rotation`

The cue appears only when a piece is selected.

That keeps the cue aligned with the existing interaction flow:

- no piece selected -> no current mode
- placeable state -> placement-focused cue
- not currently placeable -> rotation-focused cue

---

## Why This Was Cheap Enough

The implementation path was already present in the current viewer structure:

- the hint area is rendered directly in the viewer app
- the relevant state is already computed there
- the cue could be added without introducing a new mode system

So this follow-up stayed in refinement territory rather than expanding into
interaction redesign.

---

## Scope Check

The work stayed narrow:

- viewer-local
- App.tsx / App.css level change
- no control remap
- no HUD-wide redesign
- no new tutorial logic

---

## Verification

- frontend build passed
- the cue was added without widening state architecture

Build note:

- `npm run build` succeeded
- only the existing large-chunk warning remained

As with earlier Japanese copy work, browser rendering should be treated as the
final verification step for localized strings.

---

## Stable Baseline

The viewer now has a three-step clarity progression:

1. hint groups are separated
2. the current focus can be surfaced
3. all of this happens without changing the underlying control model

This confirms that small clarity improvements can continue to stack before any
larger control-system redesign is considered.

---

## Next Trigger

If this cue still feels too subtle or too noisy in live use, the next natural
question is:

- whether the cue should be toned down, restyled, or removed

That would be a calibration follow-up, not a structural one.
