# Initial Structural Compare Note

This note records a narrow compare shortlist for APSF reconstruction.

Its purpose is to explain why certain assets require compare treatment even when
they already have a leading destination candidate.
It does not decide the redesign completely, and it does not authorize migration.

---

## Why These Subjects Are In Compare

Not every difficult asset belongs in compare.
The assets below were selected because their compare value is structural, not
because they are merely important, broad, or unfinished.

This note uses a deliberately small shortlist.
It is meant to preserve explanation where direct placement alone would hide an
important distinction.
It is not a fallback store for unresolved design work, and it is not a
substitute for `Hold / Review Later`.

---

## Primary Subject A: `framework/planning-patterns.md`

### Current Reading

`framework/planning-patterns.md` currently reads as a mixed guidance asset rather
than as a clean single-responsibility contract.
The strongest ambiguity is that durable guidance and current operational advice
may still coexist in the same document.

### Why Direct Placement Is Not Enough

Direct `core` placement would currently risk overstating the stability of the
whole document.
Direct non-core placement would risk hiding the fact that some of the guidance
may still be durable enough to matter beyond the present operating shape.

### Compare Value

This subject belongs in compare because the important point is not only where it
goes, but why whole-document placement currently hides a structural distinction.
Compare makes that distinction visible without pretending the final extraction
decision has already been made.

### Boundary Of This Note

This note does not decide whether the document should later be extracted into
`core`, split across multiple destinations, or remain largely outside `core`.
At this stage, it only records that the ambiguity is structural enough to merit
compare treatment.

---

## Primary Subject B: `src/apsf/viewer/api.py`

### Current Reading

`src/apsf/viewer/api.py` has `viewer` as its leading destination because its
path and visible role point toward viewer support.
Even so, path ownership alone does not fully settle its responsibility.

### Why Direct Placement Is Not Enough

Simple `viewer` placement can hide a more important question:
whether viewer-support logic is still entangled with durable-record authority or
compare-support responsibility.
That is why this asset is more than a path-routing example.

### Compare Value

This subject belongs in compare because it directly stresses the boundary
between viewer ownership and non-viewer authority.
The value of compare here is to make that boundary stress readable without
turning the note into a redesign proposal.

### Boundary Of This Note

This note does not refine the storage/viewer rule and does not declare that the
asset is wrongly placed in `viewer`.
It only records that path-based routing alone is insufficient to explain the
case completely.

---

## Conditional Subject Note: `src/apsf/storage/run_repository.py`

### Current Reading

`src/apsf/storage/run_repository.py` carries compare pressure, but not at the
same strength as the two primary subjects.
At present, hold remains the more honest primary state.

### Why It Remains Conditional

Compare becomes more useful here only if deeper review shows a real structural
storage-boundary disagreement.
If the current uncertainty turns out to be evidential or implementation-local,
then compare should weaken rather than expand.

### Boundary Of This Note

This subject is included only as a conditional compare note.
It is not a primary compare topic in this first writing pass.

---

## Compare Exclusions

The following are not sufficient reasons for compare by themselves:

- unread state alone
- hotspot status alone
- generic importance
- unresolved design work with no structural compare value

Compare is being used here only where structural ambiguity, structural
difference, or boundary stress already justify it.

---

## Reading Guidance

These sections explain why compare routing was justified for this shortlist.
They do not provide redesign instructions, migration planning, or rule
refinement proposals.

They should be read as structural, non-prescriptive explanation only.
