# Plan

---

## Follow-up Context

- Parent series: SoChi BLOCKS public-site improvement follow-ups
- Previous results: how-to-page-relief improved the help page structure;
  video was moved to supplementary position
- New trigger: "watch a video" style labels may be creating an expectation
  that does not match what users actually reach
- Scope limit: help/video entry path only, no broad help redesign

---

## Run Metadata

- Pattern: P-02 Bug Fix
- Goal: identify the label-vs-destination mismatch and apply the smallest fix
- Output focus: mismatch diagnosis → targeted copy or link-target change

---

## Goal Readiness Check

- The problem type is clear: user expectation set by label ≠ actual destination
- The fix space is narrow: copy adjustment, destination adjustment, or both
- This can be resolved by checking two things: what the label says, where it goes
- Judgment is a short before/after check

Decision: Proceed

---

## Problem Structure

### What to confirm

| Item | Check |
|---|---|
| Label text | What does the current "video" or "how to play" label promise? |
| Click destination | Does it go to a video, a text page, a section, or a tab? |
| Expectation gap | Is the user expecting video but getting text? Or expecting in-page but leaving? |

### Mismatch type determines the fix

| Type | Fix |
|---|---|
| M-1: Label says "video" but destination is text-only | Fix A: change label copy to match text destination |
| M-2: Label is correct but destination page has no video surfaced | Fix B: adjust destination or surface video more prominently |
| M-3: Label and destination are misaligned in both directions | Fix C: copy + destination, but keep both changes minimal |

Only one fix type should be applied. Do not widen into general help redesign.

---

## Investigation Steps

1. Find every "video" or "watch" or "how to play" label on the top page and
   how-to page
2. Follow each label's link — where does it go?
3. At the destination: is video content immediately visible or buried?
4. Determine mismatch type (M-1 / M-2 / M-3)

---

## Execution Plan

- [ ] Step 1: Find all video/help labels on the public site surfaces
- [ ] Step 2: Follow each link and record the destination
- [ ] Step 3: Determine mismatch type (M-1 / M-2 / M-3)
- [ ] Step 4: Apply the smallest fix (copy / destination / both)
- [ ] Step 5: Verify — does the label now match what the user reaches?
- [ ] Step 6: Write result.md with mismatch type, fix applied, and verdict

---

## Implementation Readiness

- [ ] Every relevant label identified before writing any fix
- [ ] Mismatch type confirmed before choosing fix direction
- [ ] Fix stays in one or two files (HTML / copy only)
- [ ] No fix touches viewer interaction or help page structure

---

## Fix Constraints

- One change per mismatch (copy or destination, not both unless necessary)
- No new video production
- No help-page structural redesign
- No navigation restructuring
- Label changes should match the actual content, not promise more

---

## Scope Policy

Allowed:
- label copy change on top page or how-to page
- link target adjustment for a specific label
- making video visible at destination if already present but buried

Not allowed:
- new video content
- full help page redesign
- viewer interaction change
- broad navigation restructuring

---

## Deliverables

- mismatch type diagnosis
- targeted fix (copy / destination / both)
- result.md with before/after and scope confirmation

---

## Review Policy

Review can be skipped if:
- the fix is one or two copy/link changes
- the mismatch type is clear

---

## Result Evaluation Frame

result.md should answer:

1. What was the mismatch (M-1 / M-2 / M-3)?
2. What was changed (copy / destination / both)?
3. Does the label now match what the user reaches?
4. Did the fix stay local to one or two files?
