# Build

---

## Mismatch Type: M-2

The label promises video-first content.
The destination (`how-to-play.html`) is text-first, with video as supplementary.

The destination structure is intentional — it was set by `how-to-page-relief`.
Reverting it would conflict with that design decision.

Therefore: **fix the label, not the destination.**

---

## Investigation Summary

| Item | Finding |
|---|---|
| Label (JA) | `動画で遊び方を見る` |
| Label (EN) | `Watch How to Play` |
| Destination | `docs/how-to-play.html` |
| Video present at destination? | Yes — `tutorial_ja.mp4` / `tutorial_en.mp4` |
| Video position at destination | Supplementary — below the 3-step text guide |
| Destination structure | Text-first (by `how-to-page-relief` design) |
| Mismatch | Label sets video-first expectation; page is text-first |

---

## Why Not Fix the Destination

`how-to-page-relief` deliberately moved the video below the steps.
The reasoning was:

- steps should be readable without video
- video is supplementary confirmation, not the primary instruction path

Reversing that decision in this follow-up would widen scope and conflict
with a confirmed design choice. The correct fix is label alignment.

---

## What to Change

One file: `docs/index.html`

Change the "watch video" style labels to reflect the actual destination:
a how-to page where video is available but not the primary content.

### Candidate copy

| | Current | Option 1 | Option 2 |
|---|---|---|---|
| JA | `動画で遊び方を見る` | `遊び方を見る（動画あり）` | `遊び方ページへ` |
| EN | `Watch How to Play` | `How to Play (video included)` | `How to Play →` |

**Recommended: Option 1**

- preserves the signal that video exists
- removes the "video is the main event" framing
- stays honest about the destination structure

Option 2 is also acceptable if brevity is preferred over the video signal.
Do not use both.

---

## What Was Not Changed

- `how-to-play.html` structure — unchanged
- video position on the how-to page — unchanged
- any other navigation label
- viewer interaction

---

## Verification Steps

1. Check the label on the top page — does it still set a video-first expectation?
2. Click through to `how-to-play.html` — does the label now match what you find?
3. Confirm `how-to-play.html` was not modified
4. Browser-render the Japanese label to confirm encoding is intact

---

## Result Evaluation Frame

result.md should answer:

1. Which copy option was chosen (Option 1 / Option 2 / other)?
2. Does the label now match the destination without overselling video?
3. Did the `how-to-play.html` structure remain unchanged?
4. Was the fix one file only?
