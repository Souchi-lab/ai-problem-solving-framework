# Build

---

## Branch Taken: A

Mode state is already surfaceable in `App.tsx` where the hint area lives.
No state lift required.

---

## Investigation Summary

| Item | Finding |
|---|---|
| Hint area location | Inline in `App.tsx` — not a separate component |
| Mode state source | `useGameState.ts`: `selectedPiece`, `rotationIndex`, `cursorIndex` |
| Derived state in App | `sortedAnchors`, `isFitting` already computed |
| State lift required | None — hint area and mode state are co-located |

---

## Cue Logic

Use existing derived state to determine which group is currently active:

```ts
// Placement focus: a piece is selected and there are placement candidates
const isPlacementFocus = selectedPiece !== null && sortedAnchors.length > 0;

// Rotation focus: a piece is selected but placement is not the current action
// (or use isFitting / rotationIndex as the signal — confirm against actual state)
const isRotationFocus = selectedPiece !== null && !isPlacementFocus;
```

Adjust the condition to match the actual game flow after reading `App.tsx`.

---

## Cue Form: Active Group Highlight + "今:" Label

Chosen form: **state-dependent sublabel** on the active group.

Rationale:
- smallest change that reads clearly at a glance
- stays within the existing two-group hint structure from `operation-mode-split`
- does not add a new visual element outside the hint block

### Render shape

```tsx
{/* 📍 置く場所 group */}
<div className={`hint-group ${isPlacementFocus ? 'hint-group--active' : ''}`}>
  <span className="hint-label">📍 置く場所を決める</span>
  {isPlacementFocus && <span className="hint-now">← 今ここ</span>}
  {/* existing key indicators */}
</div>

{/* 🔄 向きを回す group */}
<div className={`hint-group ${isRotationFocus ? 'hint-group--active' : ''}`}>
  <span className="hint-label">🔄 向きを回す</span>
  {isRotationFocus && <span className="hint-now">← 今ここ</span>}
  {/* existing key indicators */}
</div>
```

Or if a single "今:" line above both groups is simpler:

```tsx
{selectedPiece && (
  <div className="hint-current-mode">
    今: {isPlacementFocus ? '置く場所を選ぶ' : '向きを調整する'}
  </div>
)}
```

Choose whichever form fits the existing markup more naturally.
Do not introduce both — pick one.

---

## What to Change

One file: `frontend/src/App.tsx`

- Add the active-group condition (2–3 lines of logic)
- Add the cue element to the hint block (1 element)
- Add CSS for `.hint-group--active` or `.hint-current-mode` if needed
  (can be inline style or small addition to existing CSS file)

Do not touch:
- `useGameState.ts` (read only, no changes)
- control model or input handling
- `operation-mode-split` hint grouping structure
- any other component

---

## What Was Not Done

- No control model change
- No new mode system
- No state lift
- No HUD-wide layout change
- No animation

---

## Verification Steps

1. Run the game with a piece selected in placement phase
   — active group or "今:" label should show placement focus
2. Run the game in rotation phase
   — label should shift to rotation focus
3. Run with no piece selected — cue should not appear
4. Confirm `npm run build` passes
5. Confirm `operation-mode-split` grouping is unchanged

---

## Result Evaluation Frame

result.md should answer:

1. Which cue form was used (sublabel per group, or single "今:" line)?
2. Does it read clearly without making the HUD feel busier?
3. Was it worth adding after `operation-mode-split`, or was the label split
   already sufficient?
4. Did the change stay in `App.tsx` only?
