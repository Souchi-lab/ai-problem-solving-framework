# Result

---

## Status

Completed

---

## Outcome

The viewer hint area now separates the two operation concepts visibly:

- `📍 置く場所を決める`
- `🔄 向きを回す`

This made the move/place vs rotate distinction easier to infer from the live UI
without changing the underlying control model.

---

## What Changed

- The viewer hint block was split into two grouped sections
- `R` and `Enter` were shown under placement-related guidance
- `WASD / Q/E` was shown under rotation-related guidance
- The change stayed local to the hint presentation layer

Implementation stayed narrow:

- viewer hint area only
- no control remap
- no HUD-wide redesign
- no language-toggle work

---

## Evaluation Against Build Questions

### 1. Did move/place vs rotate become easier to see?

Yes.

The grouped hint structure made the two action families more legible than the
previous single blended shortcut block.

### 2. Did the scope remain narrow?

Yes.

The work stayed within the intended local viewer hint change and did not expand
into broader interaction redesign.

### 3. Was current-mode display required?

Not for this version.

The label/group split was already a meaningful improvement on its own.
A current-mode cue may still be considered later, but it was not required to
make this follow-up worthwhile.

---

## Verification

- Local viewer check: improved clarity confirmed by direct inspection
- Frontend build: passed after removing an unrelated unused variable

Build note:

- `src/hooks/useAutoPlayer.ts` had an unused `isAssembly` variable
- it was removed during verification
- `npm run build` succeeded afterward

---

## What Was Not Done

- No control-model redesign
- No tutorial-system change
- No broader mobile layout cleanup
- No work on the tray empty-space issue below the horizontal scroll area

---

## Scope-Out Observation

One mobile-only layout issue remains visible:

- there is noticeable empty space below the horizontal piece-selection scroll
  bar

This was observed during validation, but it is outside the scope of
`operation-mode-split`.

---

## Stable Baseline

The repo now has a small, working pattern for improving interaction clarity
without widening into a full viewer redesign:

- define the ambiguity narrowly
- implement local grouping in the live UI
- verify that the change improves prediction without changing core controls

---

## Next Trigger

If a later viewer pass is needed, the next natural question is:

- whether a lightweight current-mode cue is still worth adding

Separately, the mobile tray empty-space issue can be cut as its own narrow
follow-up if it starts to matter in actual use.
