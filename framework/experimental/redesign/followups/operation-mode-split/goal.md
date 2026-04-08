# Goal

---

## Objective

Clarify the difference between position selection and piece rotation in the
SoChi BLOCKS play UI so that first-time users can more easily predict what an
input will do.

This follow-up should improve beginner comprehensibility, not redesign the full
viewer.

---

## Why This Follow-up

The current public-site improvement report identified operation ambiguity as one
of the highest-value UX issues remaining after the first-wave top-page and
how-to improvements.

In particular, a first-time player can struggle to tell:

- whether they are choosing a place or changing orientation
- which on-screen hints belong to movement vs rotation
- what will happen before they press a key or click

This makes the first playable minute heavier than it should be.

---

## In Scope

- Clarify move vs rotate as two distinct operation concepts
- Improve UI wording and on-screen guidance for those two concepts
- Make the current interaction state easier to infer
- Prefer small viewer-side changes over broad redesign

---

## Out of Scope

- Full control-scheme redesign
- New tutorial system
- New hint system
- Large visual redesign of the entire viewer
- Keyboard remapping as a broad feature

---

## Success Criteria

1. A first-time player can distinguish "where to place" from "how to rotate"
   more quickly from the UI alone.
2. The UI no longer relies on one blended explanation block for both concepts.
3. The change stays narrow enough to implement as a small viewer-focused
   follow-up.
4. The result can be evaluated with a short before/after judgement, not a large
   research cycle.
5. The outcome improves prediction clarity without forcing a full input-model
   rewrite.

---

## Notes For Planner

The most important planning question is not "how many controls can be
explained," but:

- what minimum change best separates move vs rotate in the player's mind

Good options may include:

- labeling
- layout split
- current-mode indication
- small icon/text grouping

The planner should prefer the smallest change that materially improves
predictability.

---

## Non-Goals

- Solving all onboarding problems at once
- Rewriting the whole play HUD
- Introducing a GUI-level settings system
- Mixing this follow-up with SEO, i18n, or KPI work

---

## Desired Landing

At the end of this follow-up, the repo should have:

- a clear small-scope plan for separating move vs rotate in the viewer UI
- a result that records whether a narrow split was enough
- a cleaner bridge from "how to play" copy into actual in-game interaction
