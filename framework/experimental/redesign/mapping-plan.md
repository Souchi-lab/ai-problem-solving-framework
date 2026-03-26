# Plan

---

## Goal Readiness Check

This planning task is ready to proceed.

- The architectural direction is already defined:
  `core / legacy / experimental` with viewer as an independent support layer.
- The current task is narrower than reconstruction design itself.
- The main work is to map representative current repo assets into the proposed structure.
- The main risks are known:
  premature implementation drift, over-classification, `shared` inflation,
  and loss of comparison at theme-run level.

Decision:

- Proceed

---

## Problem Structure

This run solves one follow-up planning problem through five linked sub-problems.

- Sub-problem 1:
  Define what unit of repo material should be classified in this run.
- Sub-problem 2:
  Define how to assign those units to
  `core / legacy / experimental / viewer / docs/compare`.
- Sub-problem 3:
  Separate immediate placements from provisional placements and extraction candidates.
- Sub-problem 4:
  Define what should explicitly stay out of `shared`.
- Sub-problem 5:
  Preserve comparison with the current APSF while keeping the run design-oriented.

---

## Selected Approach

Approach:

Produce a repo-specific mapping proposal based on representative existing assets,
using responsibility-based placement rather than location-based placement.

Reasoning:

- The reconstruction package already defines the structural model.
- The next useful planning step is not another abstract redesign pass.
- It is a concrete mapping pass that tests whether the rules survive contact with the actual repo.
- A representative mapping proposal is sufficient for this run because it provides
  enough evidence to validate the structure without forcing premature full classification.

Why this approach is preferable to full repo classification now:

- full classification would increase scope without proportionate design value
- representative mapping is enough to expose rule weakness
- difficult cases can be marked as hold / extract-later candidates
- later compare work becomes more concrete once representative placements exist

---

## Planning Outputs

This run should produce the following.

- a repo-specific directory mapping proposal
- a representative asset list grouped by destination layer
- explicit placement rationales
- a hold list for unresolved assets
- an extraction-candidate list
- a `shared` exclusion list
- a compare-material routing rule for `docs/compare`

This run does not need to produce a complete inventory of the entire repo.
Representative coverage is sufficient if the examples stress the rules properly.

---

## Classification Unit Policy

This run should classify by the smallest unit that is useful without becoming noisy.

Preferred units:

- top-level design documents when the document has a coherent single responsibility
- directory groups when files share one operational responsibility
- file-level examples when a directory contains mixed responsibility

Avoid:

- classifying every file mechanically without design value
- splitting a clearly coherent artifact into artificial fragments
- using path shape alone as the classification rule

Practical default:

- classify by file for key design documents
- classify by directory cluster for strongly homogeneous code areas
- classify by representative files for mixed areas

---

## Placement Rules

Apply the following rules in order.

### Rule 1: Stable contract goes to `core`

Place an asset in `core` only if its main value survives changes in:

- file layout
- CLI routing
- prompt body shape
- viewer mechanics
- current run-operation convenience

Examples:

- role boundary definitions
- durable record meaning
- naming / vocabulary conventions

### Rule 2: Current operational shape goes to `legacy`

Place an asset in `legacy` if it mainly explains, supports, or implements
how APSF currently operates.

Examples:

- current workflows
- current templates
- current CLI flow
- current file-based orchestration assumptions

### Rule 3: Discardable redesign draft goes to `experimental`

Place an asset in `experimental` if it exists primarily to test,
refine, or compare a redesign candidate that is not yet adopted.

Examples:

- redesign package documents
- reduced template concepts
- restructuring drafts

### Rule 4: Inspection and operator support stays in `viewer`

Place an asset in `viewer` if its main role is:

- inspection
- comparison support
- navigation
- action support
- operator visibility

Do not place assets in `viewer` if they define canonical durable record meaning.

### Rule 5: Transitional comparison material goes to `docs/compare`

Place an asset in `docs/compare` if it mainly exists to compare:

- old structure versus new candidate structure
- current responsibility versus proposed responsibility
- legacy placement versus redesign placement

Do not place such materials in `shared`.

---

## Outcome Categories

Each representative asset in this run should be assigned one of these outcome types.

### Immediate Placement

The destination is clear enough now and no caution beyond rationale is needed.

### Legacy-For-Now

The asset should remain in `legacy` in this run,
but may later yield a stable contract that belongs elsewhere.

### Extraction Candidate

The asset should not move wholesale into `core`,
but parts of it may later be extracted into `core` or a more stable neutral location.

### Hold / Review Later

The asset currently lacks a clean placement decision and should be explicitly held
rather than forced into a false certainty.

This category is preferable to weak justification.

---

## Shared Exclusion Policy

`shared` should be treated as a narrow common vocabulary layer only.

The following should be excluded from `shared` by default.

- compare tables
- migration mappings
- repo-specific placement proposals
- current template bodies
- rerun mechanics
- viewer-specific design material
- current CLI procedure detail
- mixed documents that combine invariant terms with current operational explanation

Reasoning:

If a document is only shared because it is convenient to reuse during redesign,
it does not belong in `shared`.

---

## Representative Asset Set

This run should stress the rules using representative assets from the current repo.

Recommended examples:

- `framework/overview.md`
- `framework/operating-model.md`
- `framework/responsibility-matrix.md`
- `framework/planning-patterns.md`
- `framework/workflow/v0.1.md`
- `framework/templates/plan.md`
- `framework/templates/execution-assignment.md`
- `framework/improvement-notes/*`
- `src/apsf/storage/run_repository.py`
- `src/apsf/storage/markdown_repository.py`
- `src/apsf/orchestration/phase_detector.py`
- `src/apsf/orchestration/next_instruction_builder.py`
- `src/apsf/viewer/api.py`
- `src/apsf/viewer/specification.md`
- a future responsibility-remap note comparing current structure to proposed structure

This set is intentionally mixed.
If the rules survive these examples, the mapping model is probably usable.

---

## Compare Routing Policy

Any artifact whose primary value is cross-structure comparison should be routed to `docs/compare`.

Comparison should remain possible at:

- responsibility level
- directory level
- representative asset level
- theme-run level

Minimum compare rule:

The same theme-level run must remain discussable in both current-structure terms
and redesign-candidate terms.

If a mapping choice breaks that comparability, the choice should be reconsidered.
If comparability only survives by adding ad hoc comparison notes, the placement
rules themselves should be questioned before the notes are expanded.

---

## Implementation Readiness

This run is not implementation-ready by design.
It is mapping-ready if all of the following are true.

- representative assets can be placed without repeated ad hoc exceptions
- difficult cases are captured as holds rather than hidden
- `shared` exclusions are explicit
- compare routing is explicit
- viewer remains clearly separated from canonical durable record ownership
- the proposal is concrete enough to support a later classification table

---

## Build / Execute Policy

This run authorizes design outputs only.

Allowed:

- placement proposals
- rationale tables
- hold lists
- extraction-candidate notes
- compare routing rules

Not allowed:

- moving files
- renaming packages
- changing imports
- changing CLI behavior
- changing viewer behavior
- declaring migration underway

---

## Execution Plan

- Step 1:
  Restate the mapping problem in repo-specific terms.
- Step 2:
  Select representative existing assets from `framework/`, `src/apsf/`, and viewer.
- Step 3:
  Assign each example a destination and an outcome category.
- Step 4:
  Record responsibility rationale for each assignment.
- Step 5:
  Separate `shared` exclusions and compare-material routing.
- Step 6:
  Record unresolved or extraction-candidate cases explicitly.

---

## Assumptions & Open Questions

Assumptions:

- durable Markdown remains canonical for now
- viewer remains a support layer
- representative coverage is sufficient for this run
- current APSF remains the active reference system during planning

Open questions:

- whether parts of current `storage/` contain stable contracts worth later extraction
- whether parts of `orchestration/` are too operational to classify cleanly in this run
- whether `planning-patterns` should remain `legacy` only or later split into extracted invariant guidance
- how much compare material is enough before `docs/compare` becomes necessary in practice

Priority review targets:

- `src/apsf/storage/*`
- `src/apsf/orchestration/*`
- `framework/planning-patterns.md`

---

## What This Run Decides

- the repo-specific mapping method
- representative placements for major existing asset types
- the categories:
  immediate placement / legacy-for-now / extraction candidate / hold
- `shared` exclusion rules at repo level
- compare routing rules for later materials

---

## What This Run Does Not Decide

- actual file move order
- migration timing
- final reduced template set
- final adoption of any experimental structure
- implementation sequencing
- legacy retirement conditions
