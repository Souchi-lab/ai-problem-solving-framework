# Review

---

## Review Verdict

Accept with Minor Revisions.

The current compare follow-up goal and plan are structurally sound and can guide
a small, defensible compare-routing step without drifting into compare sprawl.
The remaining risks are mainly about operational discipline in candidate handling,
not about the design of the compare follow-up itself.

---

## Goal / Plan Alignment

The goal and plan are well aligned.

- The goal limits the task to compare routing design, not compare prose authoring.
- The plan preserves that limit and turns it into explicit routing criteria.
- The routing criteria are consistent with the evidence already produced in the
  row-execution package.
- The three focus assets remain central, and their temperature differences are explicit.

This means the package is not drifting into general compare work.
It remains a narrow follow-up to row-execution evidence.

---

## Structural Strengths

### 1. Compare has positive criteria, not just convenience triggers

The package does not ask "what seems worth comparing?"
It asks whether compare is justified by:

- structural ambiguity
- structural difference
- boundary stress
- extraction-versus-whole-placement explanation

That makes compare defensible rather than impressionistic.

### 2. Compare exclusion is explicit

The plan clearly rejects compare expansion based only on:

- unread status
- vague uncertainty
- generic importance
- mere hotspot status

This is a major strength because it protects `docs/compare` from becoming a catch-all.

### 3. Strong versus conditional is defined early

The initial temperature assignment is one of the best parts of the package.

- `framework/planning-patterns.md` is strong
- `src/apsf/viewer/api.py` is strong
- `src/apsf/storage/run_repository.py` is conditional

This keeps the shortlist interpretable and prevents later drift from looking like neutrality.

### 4. Candidate-set size is part of the design

The package explicitly aims for a small, defensible compare set.
That helps keep compare useful as explanation rather than as overflow.

---

## Issues

### Major Issues

No Major structural issue currently blocks forward progress.

### Minor Issues

1. Compare could still drift into substitute-hold behavior if routing reasons are written too loosely.
2. The distinction between strong and conditional candidates must be preserved carefully in later wording.
3. `src/apsf/storage/run_repository.py` needs continued restraint so it does not become a strong compare case by momentum alone.
4. Candidate-set size should be watched so the shortlist remains selective.

---

## Required Revisions / Minor Revisions

The package can proceed, but the following minor cautions should remain attached.

1. Review every routing reason to ensure it is structural, not merely difficulty-based.
2. Keep `src/apsf/storage/run_repository.py` conditional unless real storage-boundary disagreement is shown.
3. Keep `src/apsf/viewer/api.py` strong only if the viewer-boundary ambiguity remains structurally central.
4. Resist adding more candidates unless they meet the same structural threshold as the current shortlist.

These are refinement cautions, not redesign triggers.

---

## Verification Focus For Compare Follow-up

When the compare shortlist is actually written, verification should focus on:

- whether compare is replacing hold rather than supplementing structural explanation
- whether the strong versus conditional distinction still reads clearly
- whether each routing reason names a structural cause
- whether the shortlist remains small and explainable
- whether `docs/compare` stays distinct from `shared`
- whether the compare shortlist remains traceable to row-execution evidence

The key check is:

Would a reader understand why this asset belongs in compare,
as opposed to hold, extraction, or simple later review?

If the answer is no, the routing reason is not strong enough yet.

---

## Final Recommendation

Proceed to compare routing execution with a conservative shortlist.

The recommended posture is:

- keep the candidate set small
- keep routing reasons structural
- preserve strong versus conditional temperature
- reject compare expansion driven by unresolved but non-structural uncertainty

If the shortlist starts growing through weak justifications,
the next action should be criteria tightening, not compare expansion.
