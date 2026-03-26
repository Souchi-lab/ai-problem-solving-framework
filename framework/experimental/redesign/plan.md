# Plan

---

## Goal Readiness Check

This planning task is ready to proceed.

- Scope is design-only and explicitly excludes implementation.
- The primary architectural direction is already chosen:
  `core / legacy / experimental` with viewer as an independent support layer.
- The main remaining work is not option discovery from zero, but disciplined
  classification and boundary-setting.
- The largest design risks are known:
  `core` inflation, `shared` sprawl, and viewer / durable Markdown confusion.

Decision:

- Proceed

---

## Problem Structure

This run is solving one design problem with four linked sub-problems.

- Sub-problem 1:
  Separate invariant framework value from current operational convenience.
- Sub-problem 2:
  Preserve comparability with the current APSF while still creating room for reduction.
- Sub-problem 3:
  Prevent viewer responsibility from expanding into canonical durable record ownership.
- Sub-problem 4:
  Produce a directory policy that is strong enough to guide later implementation runs.

---

## Selected Approach

Approach:

Adopt a three-layer directory model for both `framework/` and `src/apsf/`,
with viewer maintained as an independent support layer rather than collapsed
into `legacy` or `experimental`.

Reasoning:

- `core` preserves the contract layer:
  role boundaries, artifact meaning, durable-record policy, naming, and other
  responsibilities that should survive redesign.
- `legacy` preserves the current APSF as a comparable reference implementation.
- `experimental` provides an explicit place for redesign drafts that can be
  revised or discarded without forcing premature migration.
- viewer remains independent because its job is inspection, navigation,
  comparison, and operator support, not authorship of canonical records.

Why this is preferable to a direct `v1 / v2` split:

- The redesign goal is not only versioning.
- It is primarily separation of stable contracts from current operational shape.
- A pure version split keeps comparison easy, but tends to preserve redundancy.
- The chosen approach preserves comparison while making later trimming easier.

---

## Planning Outputs

This run should produce the following design outputs.

- A concrete directory proposal for `framework/`
- A concrete directory proposal for `src/apsf/`
- Responsibility definitions for each top-level layer
- Placement rules for existing repo elements
- Shared-placement rules:
  what belongs in shared, and what does not
- Core prohibition rules:
  what must never enter `core`
- Comparison policy:
  how old and new structure remain comparable during parallel operation
- Decision boundary:
  what this run settles, and what remains explicitly undecided

---

## Classification Policy

All placement decisions in this run should follow these rules.

### Rule 1: Put only stable contracts into `core`

`core` is for responsibilities that should remain meaningful even if
implementation style, file layout, or operator tooling changes.

Examples:

- role boundary definitions
- artifact meaning definitions
- durable record policy
- naming and vocabulary rules

### Rule 2: Put current operational shape into `legacy`

`legacy` is for what the current APSF needs in order to function today,
especially where the design is coupled to current templates, current CLI flow,
current prompt structure, or current Markdown file expectations.

Examples:

- current workflow docs
- current templates
- current agent role docs
- current CLI-oriented orchestration behavior

### Rule 3: Put redesign drafts into `experimental`

`experimental` is for redesign candidates that are not yet canonical and must
remain discardable.

Examples:

- alternative workflow drafts
- reduced template sets
- redesign notes and acceptance criteria
- trial directory policies

### Rule 4: Keep viewer separate

viewer is not a storage authority for durable canonical run records.
It is a support layer for inspection, comparison, action support, and
navigation across APSF state.

Therefore viewer should not be used as justification for collapsing
durable Markdown responsibilities into UI state.

---

## Shared Policy

`shared` exists only for the minimum common vocabulary and convention set
needed by both `legacy` and `experimental`.

Shared should include:

- glossary
- naming rules
- phase vocabulary
- lightweight contract-neutral terminology

Shared should not include:

- compare tables
- migration mappings
- old-to-new correspondence lists
- current template bodies
- viewer-specific specifications
- CLI procedure detail

Reasoning:

- compare and migration materials are transitional by nature
- shared must remain small, stable, and non-operational
- if shared becomes a staging area for redesign convenience, it will stop being shared

Transitional compare material should live under `docs/compare`.

---

## Core Prohibitions

The following must not enter `src/apsf/core` or `framework/core`.

- Markdown file topology dependent behavior
- direct CLI entrypoint assumptions
- viewer API assumptions
- template-body-dependent branching
- current rerun procedure logic
- implementation details needed only because the current APSF works a certain way today

Reasoning:

If these enter `core`, the redesign will only rename the current structure
instead of separating stable contracts from operational detail.

---

## Existing Element Placement Strategy

This run should classify existing materials by responsibility class,
not only by current location.

### Strong `core` candidates

- `framework/operating-model.md`
- `framework/responsibility-matrix.md`
- invariant concepts extracted from `framework/overview.md`

Note:

`framework/overview.md` should not be treated as a full `core` document by default.
It should be treated as an extraction source, because it may contain both stable
principles and current explanatory framing.

### Strong `legacy` candidates

- `framework/workflow/v0.1.md`
- `framework/workflow/v0.2.md`
- current `framework/templates/*`
- current `framework/agents/*`
- `src/apsf/cli/*`
- `src/apsf/storage/*`
- current `src/apsf/orchestration/*` implementations tied to current files

Note:

`src/apsf/storage/*` should be treated as `legacy` for this run, but not as
permanently fixed to `legacy`. Later runs may extract stable storage contracts
from current storage implementations if those contracts prove redesign-invariant.

### Strong `experimental` candidates

- redesign directory proposal docs
- reduced template proposals
- comparison policy drafts
- acceptance criteria for reconstruction design

### Temporary holding rule

Assets that may contain invariant knowledge but are still operationally shaped
should stay in `legacy` first and be treated as later extraction candidates.

Examples:

- `planning-patterns`
- skill-like operational guidance documents

---

## Comparison Policy

Parallel operation must remain possible during redesign.

Comparison should remain possible at these levels.

- Directory responsibility:
  old structure versus new candidate structure
- Artifact responsibility:
  durable record versus viewer support versus operational helper
- Workflow responsibility:
  what remains current, what becomes experimental
- Run-level comparability:
  the same redesign theme must still be discussable in terms of old and new structure

Minimum comparison rule:

The same theme-level run must remain comparable between the current structure
and the redesign candidate structure, so the redesign does not become a
non-comparable parallel system.

Comparison outputs should be stored in `docs/compare`,
not absorbed into `shared`.

---

## Implementation Readiness

This run is not implementation-ready by design.
It is decision-ready if the following conditions are met.

- Layer boundaries are explicit enough that later file moves can be evaluated mechanically
- Existing examples are sufficient to test the rules against real repo contents
- `core` admission rules are strict enough to prevent inflation
- viewer / durable Markdown separation is explicit enough to survive later implementation pressure
- undecided matters are clearly listed rather than left implicit

---

## Build / Execute Policy

This run does not authorize codebase restructuring.

Allowed:

- design documents
- directory proposals
- classification tables
- comparison policy
- acceptance criteria for later implementation runs

Not allowed:

- moving source files
- changing imports
- rewiring CLI behavior
- merging viewer and durable-record responsibilities
- declaring migration complete

---

## Execution Plan

- Step 1:
  Restate the three-layer model in repo-specific terms.
- Step 2:
  Define directory responsibilities for `framework/`, `src/apsf/`, and viewer.
- Step 3:
  Classify representative existing assets into `core / legacy / experimental / viewer`.
- Step 4:
  Define what may enter `shared` and what must stay outside it.
- Step 5:
  Define comparison policy for parallel operation.
- Step 6:
  List migration cautions and explicit non-decisions.

---

## Assumptions & Open Questions

Assumptions:

- current APSF still needs to remain runnable and referenceable during redesign
- durable Markdown remains the canonical record system for now
- viewer continues as a support surface rather than a record authority

Open questions:

- whether any part of current `orchestration/` can later be split into contract versus implementation layers
- whether some planning-pattern material eventually belongs in `core` or in a separate docs layer
- how minimal the future experimental template set can become without harming comparison quality

---

## What This Run Decides

- the directory-layer model
- responsibility criteria for each layer
- placement rules for representative existing assets
- `shared` inclusion and exclusion rules
- comparison-preserving design constraints
- the boundary between design work and later implementation work

---

## What This Run Does Not Decide

- final migration timing
- final adoption of the redesign
- exact file move sequence
- exact import path plan
- final reduced template bodies
- viewer integration mechanics
- legacy retirement conditions
