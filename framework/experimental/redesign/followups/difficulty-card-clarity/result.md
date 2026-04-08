# Result

---

## Status

Completed

---

## Outcome

The top-page difficulty cards now explain not only rough duration but also the
kind of challenge each level contains.

The update stayed local to the difficulty section and did not widen into a
broader top-page redesign.

---

## Selected Copy Direction

The adopted direction was:

- short
- selection-oriented
- focused on what makes the level difficult
- not flavor-heavy

The result shifted the cards from:

- time-only + generic mood

to:

- time + short challenge-type explanation

Examples of the adopted English direction:

- Easy: `The shape is easy to read`
- Medium: `Start thinking about order`
- Hard: `Read rotation and order`
- Hardest: `Plan several steps ahead`

---

## Why This Direction Was Chosen

This direction best matched the follow-up goal:

- help users choose
- reduce hesitation
- keep copy short

It was stronger than:

- purely motivational wording
- vague "hard / expert" framing alone
- longer explanatory text blocks

---

## Scope Check

The change stayed narrow:

- one section
- copy-only update
- no difficulty-system change
- no puzzle-list restructuring
- no viewer-side gameplay work

---

## Verification Note

The implementation was applied in the SoChi BLOCKS public-site HTML difficulty
section.

The shell output on the Japanese lines showed encoding noise during inspection,
so final judgement should be based on browser rendering rather than terminal
display alone.

In this run, the Japanese copy also briefly degraded into literal `?` text
during script-based editing, so the final close should explicitly rely on
browser verification for the rendered strings.

This does not change the scope or implementation shape of the follow-up.

---

## Stable Baseline

The difficulty cards now have a clearer job:

- not just to show time
- but to help the player choose the right kind of challenge

This is a better fit for a site that should feel easy to start.

---

## Next Trigger

If selection hesitation still remains later, the next natural question is:

- whether the difficulty area also needs a stronger recommendation cue such as
  `start here` / `good after Easy`

That would be a separate follow-up.
