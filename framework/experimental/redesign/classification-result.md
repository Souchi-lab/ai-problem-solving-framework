# Result

---

## Final Decision

Accept with Minor Revisions.

The concrete example classification package is strong enough to support
representative row execution as the next safe planning step.
It is sufficiently constrained to remain design-oriented, provided that the
remaining cautions are carried forward explicitly.

---

## What Was Established

This classification run established the following.

- The purpose of the concrete pass is rule validation through representative assets,
  not full repo classification.
- Classification should use a fixed row structure:
  `asset / proposed destination / outcome category / one-line rationale / caution`.
- `compare routing reason` should be recorded when an example is marked as compare-worthy.
- The fixed decision sequence is part of the method, not an optional suggestion.
- Hotspots must be treated more cautiously than routine assets.
- `Hold / Review Later` is a valid design outcome, not a failure state.
- `shared` remains opt-in and must not be used as fallback.
- Viewer remains a support layer, not a durable-record authority.

---

## Why This Was Accepted

This package is acceptable because it turns the mapping method into a usable
concrete classification procedure without crossing into migration work.

It is strong enough because:

- representative asset selection is explicit
- the decision sequence is reviewable
- rationale and caution are separated
- hotspots are isolated as special handling cases
- compare routing is captured without requiring compare prose
- implementation actions remain clearly out of scope

---

## Minor Revisions To Carry Forward

The package is accepted, but the following cautions should remain attached.

1. Each concrete row should record whether it is mainly confirming the rule or stressing the rule.
2. `src/apsf/viewer/api.py` should not be treated as trivially `viewer`-owned merely because of its path.
3. `storage/*` and `orchestration/*` should continue to be treated as mixed-responsibility hotspots.
4. `Hold` should be used whenever confidence is weak, rather than softened into `Legacy-For-Now`.
5. If compare-worthy examples increase quickly, the classification rules should be questioned before compare material expands.
6. If repeated ad hoc exceptions appear across rows, the method should be revised before the example set grows.

---

## Safe Interpretation

This result does not mean:

- that representative rows are already complete
- that the repo is now classified
- that file movement is authorized
- that compare documentation should be written in full now
- that viewer may absorb durable Markdown authority

This result does mean:

- the classification method is stable enough to use on concrete examples
- the next run may execute representative row classification safely
- later compare work now has a stronger evidence base

---

## Recommended Next Step

The next safe step is representative concrete row execution.

That next run should still remain design-oriented.
It should produce a classification table with, for each example:

- asset
- proposed destination
- outcome category
- one-line rationale
- caution
- compare routing reason, when applicable
- note on whether the example confirms the rule or stresses the rule

It should also update:

- the hold list
- the extraction-candidate list
- the compare-candidate set

---

## Reusable Takeaway

For APSF concrete classification, the key rule is:

Do not confuse a usable classification procedure with migration readiness.

In practice, this means:

- classify representative examples before scaling scope
- preserve uncertainty honestly
- protect hotspots from routine-speed decisions
- keep compare routing explicit
- keep viewer and durable Markdown responsibilities separate
