# Review

---

## Review Scope

This review evaluates the concrete example classification package:

- `classification-goal.md`
- `classification-plan.md`

It reviews whether the classification method is strong enough to support
representative concrete classification without drifting into migration execution
or collapsing into arbitrary example-by-example judgment.

It does not review:

- actual file moves
- import rewrites
- runtime behavior
- compare document prose
- viewer implementation changes

---

## Review Standard

The classification design should satisfy all of the following.

1. It must keep the run design-oriented.
2. It must preserve the fixed decision sequence.
3. It must allow uncertainty through outcome categories.
4. It must treat hotspots more cautiously than routine assets.
5. It must keep `shared` from becoming fallback.
6. It must keep compare routing explicit but secondary.
7. It must preserve viewer / durable Markdown separation.

---

## Primary Review Questions

### 1. Is the fixed decision sequence strong enough and usable?

The plan defines a fixed decision sequence. This is one of the main quality controls.

Review for:

- primary responsibility identified before destination
- destination proposed before outcome category
- rationale and caution kept distinct
- compare routing decided after placement, not instead of placement

Failure mode:

Examples are classified by intuition, with the sequence only nominally present.

---

### 2. Are representative assets well selected?

The example set must stress the rules rather than merely confirm easy cases.

Review for:

- coverage of likely `core`, `legacy`, and `viewer` examples
- inclusion of genuinely mixed or difficult assets
- explicit short selection reason for each chosen example
- no drift toward a convenience sample of only easy cases

Failure mode:

The run appears orderly only because it avoids the difficult assets.

---

### 3. Is `Hold` used honestly?

`Hold / Review Later` exists to preserve architectural honesty.

Review for:

- willingness to use `Hold` where evidence is insufficient
- no pressure to overproduce `Immediate Placement`
- no weak confidence disguised as `Legacy-For-Now`
- no ambiguity hidden in rationale instead of reflected in outcome category

Failure mode:

The run forces clean answers where the design is still mixed.

---

### 4. Are hotspots being handled with enough caution?

Hotspots are not ordinary examples and should not be treated as such.

Priority hotspots:

- `framework/overview.md`
- `framework/planning-patterns.md`
- `src/apsf/storage/*`
- `src/apsf/orchestration/*`
- `src/apsf/viewer/api.py`

Review for:

- stricter caution on hotspots than on routine examples
- use of extraction-candidate logic where appropriate
- no default assumption that path alone determines destination
- no routine-speed placement of mixed-responsibility examples

Failure mode:

Hotspots are classified as if they were clean one-responsibility assets.

---

### 5. Is `shared` still protected from fallback use?

This classification run should not resolve difficulty by pushing materials into `shared`.

Review for:

- explicit opt-in treatment of `shared`
- no evidence of `shared` being used to avoid difficult placements
- no compare or migration material entering shared
- no mixed documents treated as shared merely because both sides may reuse them

Failure mode:

`shared` becomes the escape hatch for unresolved structure.

---

### 6. Is compare routing under control?

Compare routing is useful, but it must not become a substitute for good placement rules.

Review for:

- compare-worthiness marked explicitly
- compare routing reason recorded
- compare candidates limited to cases that genuinely explain structural difference
- willingness to question the rules if compare candidates become too numerous

Failure mode:

Placement weakness is hidden behind growing compare notes.

---

### 7. Is viewer separation preserved in concrete examples?

The classification pass should preserve the rule that viewer is support,
not durable-record authority.

Review for:

- no assumption that viewer path implies simple viewer ownership
- no collapse of durable-record questions into viewer placement
- no weakening of Markdown authority because GUI support exists

Failure mode:

Viewer gains record authority by implication through concrete example handling.

---

## Severity Model

### Critical

A flaw that invalidates the classification pass as a safe planning step.

Examples:

- the pass implies migration authorization
- the fixed decision sequence is not actually being followed
- hotspots are treated as routine cases
- viewer is allowed to erode durable Markdown authority

### Major

A flaw that does not break the whole pass, but would weaken later compare
or implementation-planning work.

Examples:

- `Hold` is underused
- compare routing reasons are not recorded
- representative asset selection is too easy or too narrow
- `shared` fallback pressure is visible in the examples

### Minor

A flaw that affects clarity or reuse more than structural correctness.

Examples:

- rationale wording is uneven
- caution lines are too vague
- selection reasons are present but weak

---

## Acceptance Conditions

The classification package should be accepted for forward progress if all of the following are true.

- No Critical issue remains open
- the fixed sequence is usable and reviewable
- difficult assets are present in the example set
- hotspot treatment is stricter than routine treatment
- `Hold` is available and actually used where justified
- `shared` is not functioning as fallback
- compare routing reasons are recorded
- viewer remains separate from durable-record authority

If Major issues remain, the package may still proceed only if those issues are
explicitly carried forward as cautions instead of hidden under overconfident rows.

---

## Recommended Review Pass

The next review pass should test the method on concrete example rows and ask:

- Was the decision sequence followed in order?
- Is the outcome category honest?
- Does the caution add unresolved risk rather than repeat the rationale?
- Is compare routing justified?
- Would this example still make sense when later used in `docs/compare`?

Recommended row checks:

- one routine contract-like example
- one routine current-operational example
- one viewer-side example
- at least three hotspot examples

If the concrete rows require repeated ad hoc exceptions to stay coherent,
the classification rules should be revised before the example set is expanded.

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

- the classification method is concrete and reviewable
- hotspot handling is explicitly stronger than routine handling
- compare routing and shared protection are both present
- the remaining risk is mainly in future execution discipline, not in the design of the method itself
