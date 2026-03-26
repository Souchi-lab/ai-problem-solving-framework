# Result

---

## Final Decision

Accept with Minor Revisions.

The reconstruction-design package is strong enough to move forward as the basis
for later implementation-planning work, provided that the remaining minor
clarifications are preserved explicitly rather than left implicit.

---

## What Was Established

This design run established the following.

- APSF reconstruction should proceed as a design-first effort, not as immediate implementation.
- The preferred directory policy is a three-layer model:
  `core / legacy / experimental`.
- `core` is reserved for stable responsibility boundaries and contracts.
- `legacy` preserves the current APSF as a comparable operating reference.
- `experimental` is a discardable redesign space, not an already-adopted default.
- viewer remains an independent support layer for inspection, comparison,
  navigation, and operator guidance.
- durable Markdown remains the canonical run-record system for now.
- `shared` must remain minimal and must not absorb compare or migration materials.

---

## Why This Was Accepted

The package is acceptable because the major architectural risks are addressed directly.

- It avoids a false clean break from the current APSF.
- It avoids reducing redesign to a simple `v1 / v2` duplication model.
- It protects comparison with the current structure.
- It prevents viewer from becoming a shadow canonical record authority.
- It gives later runs a workable rule for rejecting misplaced `core` content.
- It keeps the current run at design scope rather than drifting into implementation.

---

## Minor Revisions To Carry Forward

The current design is accepted, but the following minor cautions should remain attached.

1. `framework/overview.md` should be treated as an extraction source, not assumed to move into `core` unchanged.
2. `src/apsf/storage/*` should remain `legacy` for now, but later runs may extract redesign-invariant storage contracts if they exist.
3. Comparison must remain possible at theme-level run granularity, not only at abstract architecture level.
4. `legacy` must remain readable as the current operating shape, not merely a leftovers area.
5. `experimental` should not use naming, placement, or references that imply adoption before an explicit decision.
6. If representative asset classification requires ad hoc exceptions, the classification rules should be questioned before the exceptions are accepted.

---

## Safe Interpretation

This result does not mean:

- that migration should begin immediately
- that file moves are now authorized
- that `experimental` is the new canonical structure
- that viewer can replace durable Markdown records
- that current APSF maintenance should stop

This result does mean:

- the design direction is coherent
- the design constraints are explicit enough for follow-up planning
- later implementation runs may use this package as an architectural reference

---

## Recommended Next Step

The next safe step is a follow-up planning run.

That next run should remain design-oriented unless the repo owner explicitly
decides to begin migration work.

It should convert this package into:

- a representative asset classification table
- a proposed directory mapping for current repo elements
- a compare document under `docs/compare`
- acceptance criteria for a future implementation-planning run

---

## Reusable Takeaway

For APSF reconstruction, the most important rule is:

Separation should increase without causing structural discontinuity.

In practice, this means:

- keep stable contracts narrow
- preserve the current system as a readable reference
- make experiments disposable
- keep comparison explicit
- never let UI convenience erase canonical durable records
