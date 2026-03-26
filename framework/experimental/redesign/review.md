# Review

---

## Review Scope

This review evaluates the reconstruction-design `goal.md` and `plan.md`
for architectural soundness.

It does not review implementation quality, file move mechanics, or runtime behavior.
The purpose of this review is to determine whether the current design plan is
sufficiently stable to guide later implementation runs without collapsing back into:

- version-only branching
- `core` inflation
- `shared` sprawl
- viewer / durable Markdown responsibility confusion
- non-comparable parallel structures

---

## Review Standard

This design should be reviewed against the following standard.

1. It must preserve parallel operation with the current APSF.
2. It must increase structural separation without creating architectural断絶.
3. It must keep durable Markdown as the canonical record system unless a later
   run explicitly changes that contract.
4. It must keep viewer in a support-layer role.
5. It must define `core` narrowly enough that future implementation runs can
   reject misplaced operational detail.
6. It must preserve meaningful comparison between current structure and redesign candidates.

---

## Primary Review Questions

### 1. Is `core` narrow enough?

The central review question is whether the proposed `core` remains a contract layer
or whether it is beginning to absorb current implementation convenience.

Review for:

- stable role / artifact / responsibility boundaries only
- explicit exclusion of current operational detail
- no hidden dependency on current file layout
- no hidden dependency on current CLI flow
- no hidden dependency on current template body shape

Failure mode:

`core` becomes a renamed copy of the current framework.

---

### 2. Is `legacy` preserved as a comparable reference rather than a dumping ground?

`legacy` should keep the current APSF understandable and comparable.
It should not become an unexamined leftovers directory.

Review for:

- whether current operational assets are preserved for comparison
- whether "keep in legacy" decisions have a responsibility basis
- whether future extraction candidates are marked as such
- whether `legacy` remains interpretable as the current operating shape

Failure mode:

`legacy` becomes an archive bucket with no design meaning.

---

### 3. Is `experimental` truly discardable?

`experimental` exists to support redesign without forcing adoption.
If the design makes `experimental` feel canonical too early, the structure loses safety.

Review for:

- whether experimental materials are explicitly draft or proposal-level
- whether comparison with current structure remains possible
- whether later removal or replacement would be structurally easy
- whether no migration commitment is implied prematurely

Failure mode:

`experimental` silently becomes the new default without explicit adoption.

---

### 4. Is viewer kept separate from canonical durable record ownership?

This is one of the most important review points.
The design should treat viewer as a support layer for inspection, comparison,
navigation, and operator guidance, not as the canonical source of durable decisions.

Review for:

- explicit separation between viewer state and durable run record
- no language that makes viewer the default writer of canonical artifacts
- no collapse of Markdown record responsibilities into GUI convenience
- no assumption that UI presence makes durable documents unnecessary

Failure mode:

viewer becomes a shadow authority over durable records.

---

### 5. Is `shared` kept minimal?

`shared` should carry only minimal cross-layer vocabulary and convention.
It should not absorb compare artifacts, migration tables, or operational shortcuts.

Review for:

- whether shared contents are stable and cross-layer by nature
- whether compare and mapping materials remain outside shared
- whether shared stays small enough to remain understandable
- whether any included item is truly neutral between legacy and experimental

Failure mode:

`shared` becomes a convenience zone for unresolved design materials.

---

### 6. Is comparison preserved at run-theme level?

The redesign must remain comparable to the current APSF in a way that is useful,
not only at abstract architecture level.

Review for:

- whether the same theme-level run can be discussed in old and new structure terms
- whether comparison outputs have a defined location
- whether redesign proposals still allow side-by-side reasoning
- whether changes reduce redundancy without destroying interpretability

Failure mode:

the redesign becomes structurally separate but practically non-comparable.

---

## Severity Model

Use this severity model when reviewing follow-up drafts.

### Critical

A flaw that breaks the reconstruction-design purpose itself.

Examples:

- viewer is allowed to replace canonical durable records by implication
- `core` absorbs current operational implementation detail
- comparison with the current APSF is lost
- design scope expands into implementation commitment

### Major

A flaw that does not break the whole design, but would likely distort later implementation runs.

Examples:

- `shared` is under-defined and likely to sprawl
- `legacy` is defined too loosely to remain comparable
- extraction candidates are not marked, creating later ambiguity
- `experimental` reads as de facto canonical

### Minor

A flaw that reduces clarity, reviewability, or maintainability but does not alter the main structure.

Examples:

- a placement rationale is too abstract
- comparison rules are correct but underspecified
- terminology is consistent enough to proceed but still slightly ambiguous

---

## Acceptance Conditions

This design plan should be accepted for forward progress if all of the following are true.

- No Critical issue remains open
- `core` admission rules are strong enough to reject misplaced operational detail
- viewer / durable Markdown separation is explicit and stable
- `shared` remains minimal by policy
- representative existing assets can be classified without obvious contradiction
- comparison with the current APSF remains possible at run-theme level
- design-only scope remains intact

If Major issues remain, the plan may still proceed only if each issue is converted into
an explicit caution or follow-up question rather than left implicit.

---

## Recommended Review Pass

The next review pass should test the design with concrete examples from the current repo.

Recommended checks:

- try classifying `framework/operating-model.md`
- try classifying `framework/overview.md`
- try classifying `framework/templates/plan.md`
- try classifying `src/apsf/storage/run_repository.py`
- try classifying `src/apsf/viewer/api.py`
- try classifying `framework/planning-patterns.md`

If the rules hold on these examples without ad hoc exceptions,
the design is likely strong enough for a later implementation-planning run.

---

## Review Conclusion Template

Use the following review conclusion shape for follow-up runs.

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

- The three-layer structure is coherent.
- Viewer is correctly treated as an independent support layer.
- `core` and `shared` risks are already anticipated in the design.
- Remaining risk is mostly in later misapplication, not in the current architectural direction.
