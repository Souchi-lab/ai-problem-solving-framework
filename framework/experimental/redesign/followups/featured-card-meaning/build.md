# Build

---

## Ambiguity Type: A-1

The featured card is highlighted and labeled, but it does not explain why.
A first-time user can see it is special, but cannot easily infer
"this is where I should start today."

A-2 and A-3 are mild but not the primary issue.

---

## Investigation Summary

| Item | Finding |
|---|---|
| Label | Present ("Today's Puzzle" / "Featured" or equivalent) |
| Visual treatment | Card is visually elevated / highlighted |
| Reason copy | Not present — no one-line explanation of why this is surfaced |
| A-1 (no reason) | Primary — label exists, rationale does not |
| A-2 (overlap with first-puzzle) | Mild — roles are distinct enough |
| A-3 (context-dependent) | Mild — label is legible but not fully self-explaining |

---

## What to Change

One file: `docs/index.html`
One location: featured card section — label area or card info block

Add one short subtitle line below or near the featured label.

### Selected copy

| | Copy |
|---|---|
| JA | `今日のおすすめから始める` |
| EN | `A good place to start today` |

Keep it one line. Do not add a description block or paragraph.

### Placement

Directly below the featured label, or as a card subtitle — whichever fits
the existing markup more naturally.

---

## What Was Not Changed

- Featured card visual treatment — unchanged
- First-puzzle card — unchanged
- Puzzle list — unchanged
- Difficulty section — unchanged
- Any other top-page section

---

## Verification Steps

1. Read the featured card in the browser — does the subtitle appear?
2. Does it explain why the card is surfaced without being verbose?
3. Confirm first-puzzle card and puzzle list are unchanged
4. Browser-render the Japanese line to confirm encoding is intact
5. No build step required (HTML/copy only)

---

## Result Evaluation Frame

result.md should answer:

1. Was A-1 the correct diagnosis?
2. Where was the subtitle placed (below label / card info)?
3. Does the featured card now communicate "start here" without needing prior context?
4. Did the change stay in the featured card section only?
