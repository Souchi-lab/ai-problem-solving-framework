# Review

---

## Review Verdict

Accept with Minor Revisions.

The current compare-writing goal and plan are strong enough to support a first
prose-writing step for `docs/compare` without reopening compare discovery.
The main remaining risk is not structural weakness in the plan, but scope drift
once prose begins.

---

## Goal / Plan Alignment

The goal and plan are well aligned.

- The goal limits the task to compare-writing entry scope.
- The plan preserves that limit and defines writing as conversion of routing evidence into prose.
- The plan does not reopen routing judgment.
- The subject hierarchy remains stable:
  primary subjects first, conditional subject second.

This means the package remains a writing-scope plan, not a new compare-routing pass.

---

## Structural Strengths

### 1. Scope control is explicit

The plan clearly states that compare prose should be based on already-routed evidence
and should not turn into:

- rule refinement
- migration judgment
- new candidate discovery

This is the most important strength of the package.

### 2. Primary versus conditional subject discipline is clear

The plan keeps:

- `framework/planning-patterns.md`
- `src/apsf/viewer/api.py`

as primary subjects, while preserving:

- `src/apsf/storage/run_repository.py`

as conditional only.

This protects the prose from becoming diffuse or overbalanced.

### 3. Structural explanation types are constrained

The plan allows compare prose to explain:

- structural ambiguity
- structural difference
- boundary stress
- extraction-versus-whole-placement tension

That is narrow enough to keep the prose explanatory rather than solutioning.

### 4. Exclusion discipline is explicit

The plan excludes:

- implementation instruction
- migration sequencing
- rule refinement proposals
- unread-state speculation

This gives the writing pass a clean boundary.

---

## Issues

### Major Issues

No Major structural issue currently blocks forward progress.

### Minor Issues

1. Prose-writing could still drift into implicit rule refinement if explanation wording becomes too solution-oriented.
2. The conditional subject could gain too much narrative weight unless its subordinate role is maintained deliberately.
3. Structural explanation language should remain disciplined so ambiguity does not become a vague discussion bucket.

---

## Scope Control

Current assessment:

- Accept

Reason:

The plan keeps compare prose inside the shortlist and does not authorize broader compare exploration.

Risk to watch:

- prose may smuggle in later design recommendations under explanatory language

---

## Primary Subject Discipline

Current assessment:

- Accept

Reason:

The primary pair remains stable and the conditional case is still explicitly subordinate.

Risk to watch:

- `src/apsf/storage/run_repository.py` may become overexplained if uncertainty is mistaken for centrality

---

## Exclusion Discipline

Current assessment:

- Accept with Minor Revisions

Reason:

The exclusions are correctly stated, but writing execution will need to keep them active rather than merely declared.

Risk to watch:

- compare prose could begin to absorb rule-refinement hints or migration language by tone

---

## Writing Readiness

Current assessment:

- Accept with Minor Revisions

Reason:

The package is ready for a first compare prose pass, provided the prose stays:

- shortlist-bound
- structurally explanatory
- non-refinement-oriented

Risk to watch:

- prose may become too abstract unless each paragraph stays tied to a routed asset and its compare reason

---

## Verification Focus For Compare Writing

When prose writing begins, verification should focus on:

- whether each paragraph maps back to an already-routed asset
- whether primary subjects remain the prose center
- whether the conditional subject stays conditional
- whether explanation language remains structural rather than prescriptive
- whether any paragraph starts behaving like rule refinement or migration argument

The key question is:

Does this prose explain why compare is needed,
or is it starting to argue what the redesign should do next?

If it is doing the latter, the writing scope has drifted.

---

## Final Recommendation

Proceed to the first `docs/compare` prose-writing pass.

Recommended posture:

- keep the subject set narrow
- write from routed evidence only
- preserve the primary / conditional distinction
- reject any prose move that turns explanation into design prescription
