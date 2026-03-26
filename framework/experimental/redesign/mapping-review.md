# Review

---

## Review Scope

This review evaluates the repo-specific mapping package:

- `mapping-goal.md`
- `mapping-plan.md`

It reviews whether the mapping method is strong enough to guide later
classification and compare work without drifting into migration execution.

It does not review:

- file move mechanics
- import rewrite plans
- runtime behavior
- viewer implementation changes

---

## Review Standard

The mapping design should satisfy all of the following.

1. It must remain design-oriented.
2. It must classify by responsibility rather than by current location alone.
3. It must allow uncertainty through explicit outcome categories rather than false certainty.
4. It must preserve comparison with the current APSF.
5. It must keep `shared` minimal.
6. It must keep viewer separate from canonical durable record ownership.

---

## Primary Review Questions

### 1. Is the classification unit sensible?

The unit of classification must be precise enough to reveal real responsibility,
but not so fine-grained that the run becomes mechanical inventory work.

Review for:

- coherent file-level classification for key design documents
- directory-cluster classification where responsibility is homogeneous
- representative-file treatment for mixed areas
- no blind all-files classification rule

Failure mode:

The mapping becomes either too coarse to be useful or too detailed to remain a planning run.

---

### 2. Are the outcome categories being used honestly?

The four outcome categories are one of the strongest protections in this mapping design.
They must be used to capture uncertainty rather than bypass it.

Review for:

- appropriate use of `Immediate Placement`
- appropriate use of `Legacy-For-Now`
- explicit marking of `Extraction Candidate`
- willingness to use `Hold / Review Later`

Failure mode:

Ambiguous assets are forced into confident placements in order to appear complete.

---

### 3. Is `shared` still protected from convenience-driven expansion?

The mapping run must not solve uncertainty by moving unresolved materials into `shared`.

Review for:

- explicit exclusion of compare tables and migration mappings
- explicit exclusion of repo-specific placement proposals
- no operational procedure material entering shared
- no mixed documents entering shared merely because they are reused by both sides

Failure mode:

`shared` becomes a convenience zone instead of a stable minimal common layer.

---

### 4. Is `docs/compare` clearly distinct from `shared`?

Comparison material should have a home, but it must not be mistaken for neutral shared contract.

Review for:

- clear routing of compare material into `docs/compare`
- explicit recognition of transitional comparison artifacts
- no attempt to hide weak placement rules behind expanding compare documentation

Failure mode:

comparison survives only through ad hoc supporting documents, while placement rules remain weak.

---

### 5. Are difficult areas being treated cautiously enough?

Some current repo areas are more likely than others to contain mixed responsibility.
These should be treated as review hotspots rather than routine placements.

Priority hotspots:

- `src/apsf/storage/*`
- `src/apsf/orchestration/*`
- `framework/planning-patterns.md`
- `framework/overview.md`

Review for:

- whether these are being placed too quickly
- whether extraction-candidate logic is used where needed
- whether legacy-for-now decisions are justified rather than habitual
- whether overview-style documents are treated as extraction sources rather than all-or-nothing moves

Failure mode:

mixed-responsibility assets are flattened into premature one-step placement.

---

### 6. Is viewer still clearly separate?

The mapping must preserve viewer as an inspection and operator-support layer.

Review for:

- no placement rationale that treats viewer as canonical record authority
- no assumption that GUI presence reduces durable Markdown responsibility
- no use of viewer as a shortcut for unresolved storage or artifact questions

Failure mode:

viewer absorbs record authority by implication.

---

### 7. Is comparison preserved at theme-run level?

The mapping should keep the redesign comparable to the current APSF in a way
that remains meaningful for later planning runs.

Review for:

- whether the same theme-level run can be discussed in both structures
- whether compare outputs have a defined home
- whether mapping choices preserve interpretability rather than merely reducing files

Failure mode:

the redesign becomes a structurally separate path that cannot be meaningfully compared.

---

## Severity Model

### Critical

A flaw that invalidates the mapping run as a safe design step.

Examples:

- the mapping implies migration authorization
- `shared` absorbs compare or operational material
- viewer is treated as canonical durable record authority
- mixed hotspots are forced into confident placement with no hold path

### Major

A flaw that does not break the run completely, but would distort later
classification or compare work.

Examples:

- classification units are inconsistent
- `Hold` is available in theory but avoided in practice
- compare routing is defined but weakly enforced
- `storage` or `orchestration` are placed with weak rationale

### Minor

A flaw that affects clarity or reviewability more than structure.

Examples:

- rationale language is too abstract
- a representative example set is slightly underpowered
- extraction-candidate wording is correct but underspecified

---

## Acceptance Conditions

The mapping package should be accepted for forward progress if all of the following are true.

- No Critical issue remains open
- classification units are useful and not mechanical
- ambiguous cases can be held explicitly
- `shared` remains minimal by policy and by examples
- `docs/compare` has a clear responsibility
- priority hotspots are treated cautiously
- viewer remains separate from durable-record authority
- the package still reads as planning, not migration

If Major issues remain, the package may still proceed only if those issues are
made explicit as follow-up cautions rather than hidden behind overconfident placement.

---

## Recommended Review Pass

The next review pass should test the mapping rules on concrete examples and ask:

- does this asset clearly fit one layer?
- if not, should it be `Legacy-For-Now`, `Extraction Candidate`, or `Hold`?
- if compare notes are needed, is the compare note valid, or is the placement rule weak?

Recommended example checks:

- `framework/overview.md`
- `framework/planning-patterns.md`
- `src/apsf/storage/run_repository.py`
- `src/apsf/storage/markdown_repository.py`
- `src/apsf/orchestration/phase_detector.py`
- `src/apsf/viewer/api.py`

If even one of these requires an ad hoc exception to fit the model,
the classification rules should be questioned before the exception is accepted.

---

## Review Conclusion Template

- Decision:
  Accept / Accept with Minor Revisions / Rework Needed
- Critical findings:
- Major findings:
- Minor findings:
- Open questions:
- Safe next step:

---

## Current Review Position

Current position:

- Accept with Minor Revisions

Rationale:

- the mapping method is concrete enough to test against the real repo
- the outcome categories reduce false certainty
- `shared` and `docs/compare` are usefully separated
- the remaining risk is mainly in how difficult assets are handled, not in the mapping structure itself
