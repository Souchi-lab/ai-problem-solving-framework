# Plan

---

## Follow-up Context

- Parent series: SoChi BLOCKS public-site improvement follow-ups
- Previous result: top-page-cta and how-to-page-relief resolved entry friction
  and first-step anxiety; difficulty selection is now the next hesitation point
- New trigger: difficulty cards currently rely on duration alone, leaving users
  without a reason to choose a specific level
- Scope limit: top-page difficulty section copy only

---

## Run Metadata

- Pattern: P-05 Document / Template Update
- Applied sub-patterns: P-09 (Generate-then-select), P-10 (Qualitative-to-structural)
- Goal: replace duration-only difficulty copy with short "what is hard here"
  explanations that help users select a level without hesitation
- Output focus: narrow copy change to one section of one HTML file

---

## Goal Readiness Check

- The difficulty levels (Easy / Medium / Hard) already exist
- The problem is the copy alongside them, not the levels themselves
- The fix is short selection-helping text, not a design system change
- This can be judged by whether a first-time user can choose a level more
  easily after the change

Decision: Proceed

---

## Problem Structure

### Current state (to confirm before writing)

The difficulty section currently shows something like a duration estimate per
level. It does not explain:

- what kind of challenge each level involves
- why a user would choose that level
- what skill or tolerance is being asked for

### What is needed

Each level card should answer one question for the user:

> "Why would I pick this level?"

That answer should be one line, factual, and selection-oriented.

---

## Structural Rules (P-10: Qualitative → Structural)

Converting "clearer and selection-helping" into concrete writing constraints:

| Rule | Detail |
|---|---|
| Length | One line per level. Maximum ~20 characters in Japanese, ~30 in English. |
| Tone | Plain description, not flavor text or encouragement |
| Focus | What is hard here, not how long it takes |
| Avoid | Abstract labels ("for beginners"), vague claims ("fun challenge") |
| Format | Can pair with duration, but duration must not be the only signal |

The three levels map to distinct challenge types in SoChi BLOCKS:

| Level | Core difficulty |
|---|---|
| Easy | Fewer pieces, simpler shapes — orientation mostly straightforward |
| Medium | More pieces, rotation required — need to track orientation |
| Hard | Many pieces, spatial reasoning — must plan backward from gaps |

---

## Candidate Generation and Selection (P-09: Generate-then-select)

### Step 1: Generate candidates

For each level, generate 2–3 short copy candidates based on the structural
rules above.

### Step 2: Select

Apply the following selection criteria:

1. Does it tell the user what is hard, not just how long?
2. Is it short enough to read at a glance?
3. Would it help a hesitant user decide?
4. Is it consistent in tone across all three levels?

Select one candidate per level. Record why others were not chosen.

---

## Execution Plan

- [ ] Step 1: Confirm current difficulty card copy in the target HTML file
- [ ] Step 2: Generate 2–3 candidates per level using structural rules
- [ ] Step 3: Apply selection criteria, pick one per level
- [ ] Step 4: Replace copy in the difficulty section of the HTML file
- [ ] Step 5: Read the section end-to-end — does it feel consistent?
- [ ] Step 6: Write result.md with before/after and selection rationale

---

## Implementation Readiness

- [ ] Current copy confirmed before writing candidates
- [ ] Structural rules applied before generating (not freeform)
- [ ] Selection rationale recorded (not just the winning copy)
- [ ] Change stays in the difficulty section, no other copy touched

---

## Change Target

One file: `docs/index.html` (or the equivalent top-page HTML file)
One section: the difficulty-entry / difficulty-card area

Do not touch:
- how-to page
- viewer copy
- CTA copy (already updated in top-page-cta)
- difficulty system logic

---

## Scope Policy

Allowed:
- difficulty card label text
- short explanatory copy per level
- duration can remain but must not be the only element

Not allowed:
- difficulty-system logic change
- full top-page copy rewrite
- new visual components or layout changes
- language-toggle or i18n integration

---

## Deliverables

- candidate generation record (2–3 per level)
- selection rationale
- updated difficulty section copy in target HTML
- result.md with before/after and scope confirmation

---

## Review Policy

Review can be skipped.

The change is short copy in one section. Scope is narrow and the selection
criteria are explicit enough to self-evaluate.

---

## Result Evaluation Frame

result.md should answer:

1. What was the previous copy?
2. What was selected, and why?
3. Does the difficulty area now communicate more than duration?
4. Would a hesitant user find it easier to choose a level?
5. Did the change stay within the difficulty section?
