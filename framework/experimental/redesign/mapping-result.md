# Result

---

## Final Decision

Accept with Minor Revisions.

The repo-specific mapping package is strong enough to support the next planning step.
It is sufficiently structured to guide concrete classification work without
collapsing into migration execution, provided that the remaining cautions remain explicit.

---

## What Was Established

This mapping run established the following.

- The current task is repo-specific mapping design, not reconstruction execution.
- Mapping decisions should be made by responsibility, not by current path alone.
- Representative asset coverage is sufficient for this run; full repo classification is not required yet.
- Mapping outcomes should use four categories:
  `Immediate Placement`, `Legacy-For-Now`, `Extraction Candidate`, and `Hold / Review Later`.
- `shared` must remain a narrow common vocabulary layer and must exclude compare and migration materials.
- Transitional comparison artifacts belong in `docs/compare`.
- Viewer remains an independent inspection and operator-support layer.
- Durable Markdown remains the canonical record authority for now.

---

## Why This Was Accepted

This package is acceptable because it answers the main planning question cleanly:

How should the real current repo be mapped into the proposed structure
without prematurely beginning migration?

It is strong enough because:

- the unit of classification is defined
- the placement rules are explicit
- uncertainty has a formal place through outcome categories
- difficult mixed-responsibility areas are treated as review hotspots
- compare material has a defined destination
- the run remains design-oriented

---

## Minor Revisions To Carry Forward

The package is accepted, but the following cautions should remain attached.

1. `storage/*` should not be flattened into `legacy` without checking whether stable contracts can later be extracted.
2. `orchestration/*` should not be treated as a homogeneous operational block without file-level or representative-file scrutiny.
3. `planning-patterns` material should be handled carefully as possible invariant-extraction territory rather than routine `legacy`.
4. `overview.md` should continue to be treated as an extraction source, not a wholesale placement candidate.
5. If a representative example requires an ad hoc exception, the rule should be questioned before the exception is normalized.
6. Each future concrete classification example should record, in one line, why its chosen outcome category is justified.

---

## Safe Interpretation

This result does not mean:

- that file moves are now authorized
- that mapping is complete for the whole repo
- that `experimental` is now the canonical structure
- that compare materials should start being mixed into `shared`
- that viewer may replace durable Markdown authority

This result does mean:

- the mapping method is sound enough to apply to concrete examples
- the package can guide a classification-focused follow-up run
- later compare work now has a stable routing model

---

## Recommended Next Step

The next safe step is a concrete example classification pass.

That next run should still remain design-oriented.
It should apply this mapping package to representative assets and produce:

- outcome-category decisions for concrete examples
- one-line rationale per example
- a refined hold list
- a refined extraction-candidate list
- materials that can later feed `docs/compare`

---

## Reusable Takeaway

For repo-specific APSF mapping, the key rule is:

Do not force certainty where the structure is still mixed.

In practice, this means:

- map by responsibility, not by current location
- prefer explicit hold over weak confidence
- keep compare material out of `shared`
- treat viewer as support, not authority
- keep the run in planning mode until migration is explicitly authorized
