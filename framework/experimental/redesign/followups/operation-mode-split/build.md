# Build

---

## Status

Done

---

## 1. Current State (Before)

The viewer currently presents operation hints as one blended block.
The player sees key labels and descriptions, but nothing visually signals:

- which keys belong to "where to place"
- which keys belong to "how to rotate"
- what the current interaction state is

As established in how-to-page-relief:

- `← →` already has two distinct meanings depending on context
  - in rotation phase: rotates the piece
  - in placement phase: moves the cursor
- the how-to page now separates these (Step 2 vs Step 3)
- but the in-game viewer shows no equivalent separation

The result: a first-time player watching the in-game hint area cannot tell
which kind of action they are about to take.

---

## 2. Target State (After)

The viewer hint area is split into two labeled groups:

### Group A — 置く場所を決める / Move & Place

- heading label: `📍 置く場所` (or `Move / Place`)
- shows: cursor movement keys

### Group B — 向きを回す / Rotate

- heading label: `🔄 向きを回す` (or `Rotate`)
- shows: rotation keys

Between or above these two groups:
a current-mode indicator (optional, if the game tracks mode state):

```
今: 向きを選んでいます  →  今: 置く場所を選んでいます
```

If a mode state is not surfaceable from the game's control model without
code change, this cue is skipped and the label split alone is sufficient.

---

## 3. Change Target

One file: the viewer's in-game operation hint component or section.

Likely targets (in order of preference):

1. A HUD / hint overlay component — add two labeled sections
2. An inline operation guide block — split into two labeled groups
3. A static text block — replace with two-section markup

Do not touch:
- the underlying control model
- keyboard bindings
- the how-to page (already updated in how-to-page-relief)
- any unrelated layout or visual system

---

## 4. Copy

Use the same language established in how-to-page-relief.

Japanese:
- Group A label: `📍 置く場所を決める`
- Group B label: `🔄 向きを回す`

English (if language toggle applies):
- Group A label: `📍 Move & Place`
- Group B label: `🔄 Rotate`

Keep labels short. One line each. The goal is recognition, not instruction.

---

## 5. What Was Not Done

- No control model change
- No keyboard remapping
- No new tutorial section
- No broad HUD redesign
- No current-mode state change (deferred; depends on whether mode is surfaceable)
- No language toggle integration (separate follow-up: language-toggle already closed)

---

## 6. Implementation Notes for Builder

The minimum acceptable change:

> Add two labeled group headings (`📍 置く場所を決める` / `🔄 向きを回す`)
> to the viewer's existing operation hint area, grouping current keys under each.

This requires no new interaction logic.
It is a label + layout change only.

If the viewer has no operation hint area at all:

> Add a minimal two-group hint block to the viewer,
> positioned near the board but not obstructing it.
> Two rows, each with a heading and the relevant key indicators.

The change should be local to one component or one section of one file.

---

## 7. Evaluation Readiness

result.md should answer:

1. Can a first-time player now distinguish "where to place" from "how to rotate"
   from the in-game UI alone?
2. Did the change stay local (one component / one file)?
3. Was the label split enough, or does a mode-state cue still feel missing?
