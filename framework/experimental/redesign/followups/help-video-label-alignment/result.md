# Result
---
## Outcome

`help-video-label-alignment` closed as a copy-only fix.

- mismatch type: `M-2`
- path taken: align the label to the current destination
- destination was intentionally left unchanged

## What Was Confirmed

The investigation showed:

- the top page used a video-first label
- the destination page did contain tutorial videos
- but the destination itself was a help page where video was a supplement, not the primary surface

So the issue was not "video is missing."
It was "the label promises a video-first experience more strongly than the destination actually delivers."

## Why Destination Was Not Changed

The current help page structure was already established by the earlier `how-to-page-relief` direction:

- text-first quick understanding
- video as optional support

Reversing that here would conflict with the earlier design intent.

So the correct narrow fix was not to move the video upward.
It was to make the label match the already-chosen destination structure.

## What Changed

In the SoChi BLOCKS repo:

- `docs/index.html`
  - JA: `動画で遊び方を見る` -> `遊び方を見る（動画あり）`
  - EN: `Watch How to Play` -> `How to Play (video included)`

No destination, layout, or video placement change was made.

## Stable Baseline

The stable baseline is now:

- help entry labels should not promise a video-first destination unless the landing page is actually video-first
- if video is supplementary, the label should say so

## Verification Note

This is an HTML copy change, so final close should be based on browser rendering confirmation rather than shell output alone.
