# Build

---

## Types Found: P-2 + P-3

P-1 is mild — "Cleared: x / y" is already readable.

P-2: Progress is localStorage-derived but nothing in the UI signals
"this is your own browser record."

P-3: `renderProgressSummary` hides the entire area when `clearedTotal === 0`,
so first-time users never see the progress feature exists.

---

## Investigation Summary

| Item | Finding |
|---|---|
| P-1 (what is counted) | Mild — "クリア済み: x / y 問 / Cleared: x / y" is readable |
| P-2 (local vs account) | Present — `localStorage('sochi_clears')` source not surfaced in UI |
| P-3 (empty state) | Present — `clearedTotal === 0` hides the entire summary block |

---

## What to Change

One file: `docs/index.html`
Two changes, both local to the progress summary area.

---

### Change 1 — P-2: Add local-progress context cue

Add a one-line label near the progress summary:

| | Copy |
|---|---|
| JA | `このブラウザの記録` |
| EN | `Saved in this browser` |

Placement: below or alongside the progress summary heading.
One line only. Do not add an explanation paragraph.

---

### Change 2 — P-3: Show empty state instead of hiding

Change `renderProgressSummary` behavior:

**Before:** return nothing (entire block hidden) when `clearedTotal === 0`

**After:** show a minimal empty-state line when `clearedTotal === 0`

Suggested empty-state copy:

| | Copy |
|---|---|
| JA | `まだクリアなし — 最初の1問を試してみよう` |
| EN | `No clears yet — try your first puzzle` |

The empty state should be visually subdued (muted text, smaller size) so it
reads as a starting point, not a status problem.

Do not show the full progress bar or chip in the empty state — just the
one-line prompt is enough.

---

## What Was Not Changed

- Progress calculation logic (`localStorage('sochi_clears')`) — unchanged
- Cleared count display format — unchanged
- Any other top-page section
- Puzzle list, featured card, difficulty section

---

## Verification Steps

1. Open the top page with zero clears — does the empty-state line appear?
2. Open the top page with some clears — does the "このブラウザの記録" cue appear?
3. Confirm the cue does not appear on sections unrelated to progress
4. Browser-render both Japanese lines to confirm encoding is intact
5. No build step required (HTML/JS in-page only)

---

## Result Evaluation Frame

result.md should answer:

1. Where was the "このブラウザの記録" cue placed?
2. What does the zero-clear state now show?
3. Can a first-time user now understand the progress area from the start?
4. Did both changes stay within the progress summary section?
