# Plan

---

## Run Metadata

- Run:
  docs/compare follow-up
- Goal:
  fix compare routing design for a small set of evidence-backed candidate assets
- Output focus:
  compare candidate shortlist and routing reasons
- Non-goal reminder:
  this run does not write the full compare documents

---

## Goal Readiness Check

- The compare target is already narrowed to three central assets
- Strong versus conditional compare pressure is already visible from row execution
- Compare is explicitly scoped as routing design, not prose authoring
- Exclusion pressure is known:
  unread or merely unresolved material must not be promoted into compare by default

Decision:

- Proceed

---

## Execution Intent

This run exists to define when an asset should enter `docs/compare`,
not to expand compare material by momentum.

The main question is not:

- "What can be compared?"

It is:

- "Under what conditions is compare justified enough to deserve a place in `docs/compare`?"

The desired outcome is a small, defensible compare candidate set with explicit routing reasons.

---

## Compare Candidate Selection Policy

An asset should be considered for compare routing only when it does one or both of the following.

1. Exposes a structural ambiguity that matters to the redesign
2. Explains a meaningful old-versus-new responsibility difference

This means compare is justified when an asset helps explain:

- why direct placement is not yet honest
- why two destinations remain materially plausible
- why a hotspot stresses a boundary rule
- why a later rule refinement may be necessary

Compare is not justified merely because an asset is difficult or important.

---

## Strong Vs Conditional Decision Policy

### Strong Compare Candidate

Use this when:

- compare value is already structural, not provisional
- the asset directly exposes a rule boundary that later readers will need explained
- the ambiguity is real enough that compare would add durable explanatory value

### Conditional Compare Candidate

Use this when:

- compare may become valuable later, but that value depends on a condition
- the ambiguity may disappear after closer file-content or boundary review
- the current uncertainty may still be evidential rather than structural

### Initial Temperature For Current Focus Assets

- `framework/planning-patterns.md`
  - strong compare candidate
- `src/apsf/viewer/api.py`
  - strong compare candidate
- `src/apsf/storage/run_repository.py`
  - conditional compare candidate

---

## Compare Routing Reason Policy

Every compare candidate must have a routing reason.

That reason must explain one of the following.

- structural ambiguity
- structural difference
- boundary stress
- extraction-versus-whole-placement explanation

The routing reason should be short, but it must answer:

- why this belongs in compare
- why this is not just a hold note
- why this is not only a temporary unread state

---

## Compare Exclusion Policy

An asset should not be sent to `docs/compare` for any of the following by itself.

- unread or uninspected status
- vague uncertainty
- generic importance
- mere hotspot status
- simple lack of time

Compare should also not be used as:

- a fallback for weak placement logic
- a substitute for `Hold / Review Later`
- a hidden extension of `shared`

If compare candidates increase because many rows are merely unresolved,
the correct response is to revisit the rules, not to enlarge compare output.

---

## Final Candidate Set

| asset | current compare temperature | proposed routing status | routing basis |
|---|---|---|---|
| `framework/planning-patterns.md` | strong | route to `docs/compare` shortlist | durable-guidance versus current-operational-advice ambiguity appears structural rather than incidental |
| `src/apsf/viewer/api.py` | strong | route to `docs/compare` shortlist | viewer path versus durable-record / compare-support responsibility is a direct boundary-stress case |
| `src/apsf/storage/run_repository.py` | conditional | keep as conditional compare candidate | compare is justified only if storage-boundary disagreement remains after deeper review |

---

## Deliverables

This run should produce:

- compare candidate shortlist
- routing reason list
- strong compare candidate list
- conditional compare candidate list
- compare exclusion note

---

## Review Checklist

- every compare candidate has a routing reason
- strong versus conditional is explicitly distinguished
- no candidate is included merely because it is unread or unresolved
- compare remains distinct from hold logic
- compare remains distinct from shared
- the candidate set remains small and explainable

---

## Planned Output Shape

The output should be structured in this order.

1. strong compare candidates
2. conditional compare candidates
3. compare exclusions
4. carry-forward notes for later compare authoring

---

## Assumptions & Open Questions

Assumptions:

- current evidence is enough to identify at least a small compare shortlist
- compare value should remain selective rather than comprehensive
- the strongest compare value currently sits in mixed-responsibility hotspots

Open questions:

- whether `framework/planning-patterns.md` will remain compare-worthy after deeper guidance extraction thinking
- whether `src/apsf/viewer/api.py` remains the strongest compare candidate after viewer-boundary refinement
- whether `src/apsf/storage/run_repository.py` will survive as compare-worthy once storage-boundary review goes deeper

---

## What This Run Decides

- compare routing criteria
- strong versus conditional compare distinction
- the initial compare shortlist for the current strongest cases

---

## What This Run Does Not Decide

- final compare prose
- compare document structure in full detail
- storage/viewer rule refinement itself
- migration readiness
