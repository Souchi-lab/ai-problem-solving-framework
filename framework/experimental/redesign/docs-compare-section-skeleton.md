# Docs/Compare Section Skeleton

Purpose:

- first prose-writing pass for `docs/compare`
- based only on already-routed compare evidence
- not a rule-refinement document
- not a migration judgment document

---

## 1. Compare Purpose

Write a short opening that states:

- this compare note explains why certain assets require compare treatment
- the goal is to preserve structural explanation
- the goal is not to resolve the redesign completely

Suggested intent:

This compare note records cases where direct placement alone would hide an
important structural distinction. It exists to explain the ambiguity or boundary
stress already identified in the routing evidence.

---

## 2. Why These Subjects Are In Compare

Write a short framing section that says:

- not every difficult asset belongs in compare
- these subjects were selected because their compare value is structural
- the current note uses a narrow shortlist

Suggested points:

- compare is selective
- compare is not a fallback for unresolved design
- compare is not a substitute for hold

---

## 3. Primary Subject A

Target:

- `framework/planning-patterns.md`

Section intent:

- explain why this asset is compare-worthy
- explain the structural ambiguity
- avoid proposing the final redesign answer

Suggested subsection flow:

### 3.1 Current Reading

Describe, at a high level:

- why the asset appears to mix durable guidance and current operational advice

### 3.2 Why Direct Placement Is Not Enough

Explain:

- why direct `core` placement would overstate stability
- why direct non-core placement would hide potential durable guidance value

### 3.3 Compare Value

Explain:

- what the reader learns only by seeing the ambiguity explicitly

### 3.4 Boundary Of This Note

State clearly:

- this note does not decide the final extraction or placement outcome

---

## 4. Primary Subject B

Target:

- `src/apsf/viewer/api.py`

Section intent:

- explain why the viewer path alone does not settle responsibility
- explain the boundary stress
- keep the note descriptive rather than prescriptive

Suggested subsection flow:

### 4.1 Current Reading

Describe, at a high level:

- why `viewer` is the leading destination
- why path ownership is still insufficient on its own

### 4.2 Why Direct Placement Is Not Enough

Explain:

- why simple `viewer` ownership can hide durable-record or compare-support entanglement

### 4.3 Compare Value

Explain:

- what the reader learns by seeing the viewer-boundary stress explicitly

### 4.4 Boundary Of This Note

State clearly:

- this note does not refine the storage/viewer rule itself

---

## 5. Conditional Subject Note

Target:

- `src/apsf/storage/run_repository.py`

Section intent:

- keep this subordinate
- explain why it is not a primary compare subject yet

Suggested subsection flow:

### 5.1 Current Reading

Describe:

- why compare pressure exists
- why hold remains the more honest primary state

### 5.2 Why It Remains Conditional

Explain:

- compare becomes stronger only if deeper review confirms structural storage-boundary disagreement

### 5.3 Boundary Of This Note

State clearly:

- this note does not elevate the asset into a primary compare topic

---

## 6. Compare Exclusions

Write a short exclusion section that states explicitly:

- unread state alone is not enough
- hotspot status alone is not enough
- generic importance is not enough
- compare is not being used to store unresolved design work

This section is important because it keeps compare narrow.

---

## 7. Reading Guidance

Write a short closing that says:

- these compare sections explain why routing to compare was justified
- they do not provide redesign instructions
- they should be read as structural explanation, not migration planning

---

## Paragraph Test

Use this test on every paragraph before accepting it:

Does this paragraph explain why compare is needed,
or is it starting to argue what the redesign should do next?

If it is doing the latter, rewrite or remove it.
