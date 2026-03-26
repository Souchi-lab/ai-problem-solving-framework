# Plan

---

## Goal Readiness Check

This planning task is ready to proceed.

- The classification purpose is explicit:
  test the mapping rules against representative real assets.
- The output format is defined.
- Hotspots are already identified.
- The run remains design-oriented and does not authorize migration execution.

Decision:

- Proceed

---

## Problem Structure

This run solves one concrete planning problem through five linked sub-problems.

- Sub-problem 1:
  Select a representative set of existing assets.
- Sub-problem 2:
  Apply the mapping rules consistently to each example.
- Sub-problem 3:
  Distinguish routine cases from hotspot cases.
- Sub-problem 4:
  Record uncertainty honestly through outcome categories.
- Sub-problem 5:
  Extract compare-worthy cases without turning the run into compare authoring.

---

## Selected Approach

Approach:

Run a representative classification pass using a fixed row format and a fixed decision sequence.

Each selected asset should be evaluated in this order:

1. What is its primary responsibility?
2. What is the most plausible proposed destination?
3. How certain is that placement now?
4. Which outcome category reflects that certainty honestly?
5. What one-line rationale explains the choice?
6. What caution, if any, should remain attached?
7. Should this example feed later compare material?
8. If yes, why?

Reasoning:

- A fixed decision sequence keeps the run comparable across examples.
- A fixed row format makes later compare work easier.
- The purpose is not to maximize placements.
- It is to expose where the mapping rules are clear, weak, or premature.

---

## Planning Outputs

This run should produce:

- a concrete example classification table
- a hotspot caution list
- an updated hold list
- an updated extraction-candidate list
- a compare candidate list with routing reasons

Each classification row should contain:

- `asset`
- `proposed destination`
- `outcome category`
- `one-line rationale`
- `caution`

Optional additional fields may be added later, but these five are mandatory.
`compare routing reason` should also be recorded as a separate note or column
whenever an example is marked as compare-worthy.

---

## Representative Asset Selection Policy

This run should not try to classify the whole repo.
It should choose examples that stress the rules.

Select assets from at least these groups:

- stable-looking framework contracts
- clearly current operational framework materials
- mixed or ambiguous framework materials
- storage-related code
- orchestration-related code
- viewer-side materials

Recommended initial set:

- `framework/operating-model.md`
- `framework/responsibility-matrix.md`
- `framework/overview.md`
- `framework/planning-patterns.md`
- `framework/workflow/v0.1.md`
- `framework/templates/plan.md`
- `framework/templates/execution-assignment.md`
- `src/apsf/storage/run_repository.py`
- `src/apsf/storage/markdown_repository.py`
- `src/apsf/orchestration/phase_detector.py`
- `src/apsf/orchestration/next_instruction_builder.py`
- `src/apsf/viewer/api.py`

The representative set is good enough if it includes:

- at least one likely `core` case
- at least one likely `legacy` case
- at least one likely `viewer` case
- at least three ambiguous or mixed-responsibility cases

---

## Decision Procedure

Use the following procedure for each selected asset.

### Step 1: Identify primary responsibility

Ask:

- Is this mainly a stable contract?
- Is this mainly current operational shape?
- Is this mainly redesign experimentation?
- Is this mainly viewer support?
- Is this mainly comparison material?

Do not begin from current location.

### Step 2: Propose destination

Choose one provisional destination:

- `core`
- `legacy`
- `experimental`
- `viewer`
- `docs/compare`

If no destination is clean enough, still record the most plausible destination,
but expect the outcome category to capture uncertainty.

### Step 3: Choose outcome category

Use:

- `Immediate Placement`
  when the destination is strong and low-risk
- `Legacy-For-Now`
  when current operation dominates but later extraction is plausible
- `Extraction Candidate`
  when some stable part may later be separated from the current whole
- `Hold / Review Later`
  when forcing confidence would damage the design

### Step 4: Write one-line rationale

The rationale should explain the main responsibility basis in one line.

Good pattern:

- "Current file-based orchestration logic tied to present APSF flow, so `legacy`."
- "Mixed explanatory document with likely invariant concepts, so extraction candidate rather than direct `core`."

### Step 5: Record caution

Caution should name the unresolved risk, not restate the rationale.

Good examples:

- "May contain extractable contract language."
- "Too coupled to current file topology to treat as `core`."
- "Needs compare note if later split is proposed."

### Step 6: Decide compare routing

Mark an example for later compare use when:

- two destinations are both plausible
- rationale depends on tradeoff rather than clean placement
- future extraction is likely
- the example is useful for old-versus-new explanation

Also record the reason it should feed compare material.

---

## Hotspot Handling Policy

Hotspot assets must not be processed with the same confidence level as routine examples.

Hotspots:

- `framework/overview.md`
- `framework/planning-patterns.md`
- `src/apsf/storage/*`
- `src/apsf/orchestration/*`
- `src/apsf/viewer/api.py`

For hotspots:

- default to caution rather than confidence
- prefer `Legacy-For-Now`, `Extraction Candidate`, or `Hold`
- avoid direct `Immediate Placement` unless the rationale is unusually strong
- if the example needs a special-case explanation, question the rule first

Additional viewer caution:

Do not assume that `src/apsf/viewer/api.py` belongs cleanly to `viewer`
only because of its path. Review whether it also carries durable-record,
routing, or comparison assumptions that make the placement less trivial.

---

## Hold Policy

`Hold / Review Later` is not a failure state.
It is the correct outcome when the current evidence is insufficient for a clean placement.

Use `Hold` when:

- the asset mixes two or more responsibilities too tightly
- proposed destination depends on assumptions not yet validated
- compare value is high precisely because placement is unresolved
- a forced decision would likely become an exception later

Do not use `Hold` lazily.
Use it when it preserves architectural honesty.

---

## Shared Protection Policy

During classification, no example should be sent to `shared` unless it clearly fits
minimal common vocabulary or naming responsibility.

For this run, the default posture is:

- classify into `core / legacy / experimental / viewer / docs/compare`
- treat `shared` as opt-in, not as fallback

If `shared` feels attractive because it avoids a difficult placement,
that is a warning sign, not a solution.

---

## Compare Candidate Policy

An asset should be marked as compare-worthy when its classification helps explain:

- why old structure and new candidate structure differ
- why a case is not cleanly settled
- why a hold or extraction-candidate result exists

Do not generate compare prose in this run.
Only mark compare candidates and the reason they should later appear in `docs/compare`.

If compare candidates multiply because placement is weak across the board,
the mapping rules should be questioned before compare output expands.

---

## Implementation Readiness

This run is not implementation-ready by design.
It is classification-ready if all of the following are true.

- the representative set is strong enough to test the rules
- the decision procedure is consistent across examples
- hotspot handling is stricter than routine handling
- `Hold` is allowed as a legitimate result
- compare routing is captured without becoming compare authoring

---

## Build / Execute Policy

This run authorizes only classification design outputs.

Allowed:

- classification rows
- cautions
- hold entries
- extraction-candidate entries
- compare-routing notes

Not allowed:

- file moves
- import changes
- package renames
- CLI changes
- viewer changes
- migration sequencing

---

## Execution Plan

- Step 1:
  Confirm the representative asset set and record a short selection reason for each example.
- Step 2:
  Separate routine assets from hotspot assets.
- Step 3:
  Classify routine assets first using the fixed row format.
- Step 4:
  Classify hotspot assets more cautiously using the same row format.
- Step 5:
  Record hold and extraction-candidate cases explicitly.
- Step 6:
  Mark compare-worthy examples and their routing reasons.

---

## Assumptions & Open Questions

Assumptions:

- representative examples are enough to validate the mapping rules at this stage
- durable Markdown remains canonical
- viewer remains a support layer
- not every ambiguous case needs resolution in this run

Open questions:

- whether `storage/*` contains stable contracts worth later extraction
- whether some orchestration files should be split conceptually before placement is finalized
- whether `planning-patterns` should later split across stable guidance and current operating advice
- whether some compare-worthy cases should eventually become standing examples in `docs/compare`

---

## What This Run Decides

- the concrete classification method
- representative example outcomes
- hotspot cautions
- hold and extraction-candidate updates
- compare-routing candidates and reasons

---

## What This Run Does Not Decide

- full repo classification
- final migration map
- actual file movement
- import path changes
- final compare document contents
- implementation authorization
