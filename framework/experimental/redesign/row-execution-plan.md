# Plan

---

## Run Metadata

- Run:
  representative concrete row execution
- Goal:
  turn the classification rules into concrete evidence
- Output focus:
  representative concrete row table
- Non-goal reminder:
  this run does not decide migration readiness

---

## Goal Readiness Check

- Goal statement is concrete
- Output shape is fixed
- Success criteria are row-based and inspectable
- Non-goals and cautions are explicit
- No blocker is currently required for planning

Decision:

- Proceed

---

## Execution Intent

This run is not a migration judgment run.

It is an evidence run that tests whether the classification package's fixed
decision sequence can be applied to representative real assets without
collapsing into ad hoc judgment.

The evaluation target is not row count.
It is whether the run can produce:

- rows that confirm the rules
- rows that stress the rules
- honest hotspot handling
- explicit caution and hold usage where needed

---

## Selected Approach

Approach:

Use a fixed representative asset set, then execute a fixed row construction
method against each example.

Reasoning:

- changing the asset set during row writing would turn this into exploration
  rather than evidence generation
- a fixed asset set makes the output more reviewable
- a fixed method makes the resulting rows comparable
- the purpose is to expose where the rules are strong, weak, or premature

---

## Representative Asset Selection Policy

### Selection Objectives

The representative set should satisfy all of the following.

1. Include assets that likely fall cleanly into routine classification
2. Include hotspot assets
3. Include assets likely to require compare routing
4. Include assets likely to justify `Hold / Review Later`
5. Include assets that test the viewer versus durable Markdown authority boundary

### Selection Rules

- avoid duplicate assets that test the same rule in the same way
- prefer boundary visibility over row count
- if compare candidates multiply quickly, question the rules before adding more examples
- include at least one routine example and at least one hotspot example in each major area

---

## Final Representative Asset Set

| asset | selection reason | hotspot? | expected pressure on rules |
|---|---|---:|---|
| `framework/operating-model.md` | baseline stable contract example | No | confirm |
| `framework/responsibility-matrix.md` | strongest current core-like contract candidate | No | confirm |
| `framework/overview.md` | tests extraction-source handling versus wholesale placement | Yes | compare / caution |
| `framework/planning-patterns.md` | tests reusable guidance versus current-operating advice | Yes | compare |
| `framework/workflow/v0.1.md` | baseline current-operational framework example | No | confirm |
| `framework/templates/plan.md` | baseline current template example | No | confirm |
| `framework/templates/execution-assignment.md` | tests current operational procedure boundary | No | confirm / caution |
| `src/apsf/storage/run_repository.py` | tests storage placement and extraction risk | Yes | hold / extraction risk |
| `src/apsf/storage/markdown_repository.py` | tests durable Markdown handling responsibility | Yes | compare / extraction |
| `src/apsf/orchestration/phase_detector.py` | tests orchestration between operational logic and stable concept boundary | Yes | confirm / stress |
| `src/apsf/orchestration/next_instruction_builder.py` | tests orchestration logic that may overfit current flow | Yes | stress |
| `src/apsf/viewer/api.py` | tests viewer path-only reasoning against mixed responsibility risk | Yes | compare / caution |

---

## Row Construction Method

Each asset should be processed using the fixed decision sequence below.

### Step 1: Identify primary responsibility

Ask:

- Is this mainly stable contract?
- Is this mainly current operational shape?
- Is this mainly redesign experimentation?
- Is this mainly viewer support?
- Is this mainly comparison material?

### Step 2: Propose destination

Choose one proposed destination:

- `core`
- `legacy`
- `experimental`
- `viewer`
- `docs/compare`

### Step 3: Choose outcome category

Choose the category that best reflects current confidence and structural honesty.

### Step 4: Write one-line rationale

The rationale should explain why the proposed destination and outcome category
make sense in one line.

### Step 5: Write caution

The caution should capture unresolved boundary risk, mixed responsibility,
or reasons to avoid premature confidence.

### Step 6: Decide compare routing

If the example is compare-worthy, record:

- that it should later feed `docs/compare`
- why it should feed `docs/compare`

### Step 7: Mark confirm or stress

Record whether the row mainly:

- confirms that a rule works as expected
- stresses a rule boundary and exposes weakness or ambiguity

---

## Mandatory Row Fields

Each row must contain:

- `asset`
- `proposed destination`
- `outcome category`
- `one-line rationale`
- `caution`

When applicable, also record:

- `compare routing reason`
- `rule confirm / rule stress note`

No `confidence` column should be introduced.
Confidence should be expressed through:

- outcome category
- caution
- compare routing reason

---

## Outcome Category Use Policy

### Immediate Placement

Use only when:

- responsibility is clear
- the destination is low-risk
- hotspot caution is not central

### Legacy-For-Now

Use when:

- current operational shape dominates
- immediate movement would be less honest than current preservation
- later extraction remains plausible

### Extraction Candidate

Use when:

- the asset likely contains a more stable sub-responsibility
- moving the whole asset would be less honest than marking future extraction possibility

### Hold / Review Later

Use when:

- the evidence is insufficient for clean placement
- the asset mixes responsibilities too tightly
- forcing confidence would create future exceptions

`Hold / Review Later` is a valid design result, not a failure.

---

## Hotspot Handling Policy

Hotspots must be treated more cautiously than routine assets.

For each hotspot row, explicitly check:

- whether proposed destination really follows responsibility rather than path
- whether viewer / durable Markdown / storage / orchestration boundaries are being crossed
- whether compare routing reason is needed
- whether `Hold / Review Later` should be used instead of weak confidence

Hotspots must not be given `Immediate Placement` unless the rationale is unusually strong.

Additional viewer caution:

`src/apsf/viewer/api.py` must not be treated as trivially `viewer`-owned
merely because of path. It may also carry durable-record, routing, or comparison assumptions.

---

## Compare Handling Policy

`compare routing reason` should be recorded only when:

- more than one destination is materially plausible
- the case explains an old-versus-new structural difference
- the row is useful as evidence of a stressed rule boundary
- the case would later help explain why a hold or extraction-candidate result occurred

Do not increase compare volume just because a row is slightly uncertain.

If compare-worthy rows increase quickly, treat that as a signal that the rules
need revision before compare output expands.

---

## Deliverables

This run should produce:

- representative concrete row table
- hotspot caution list
- updated hold list
- updated extraction-candidate list
- compare candidate list

---

## Review Checklist

- each row contains the mandatory fields
- compare-worthy rows include compare routing reason
- each row is tagged as rule confirm or rule stress when useful
- hotspots are not processed at routine temperature
- `Hold / Review Later` is used where justified
- `shared` fallback does not appear
- viewer and durable Markdown authority do not become mixed
- the run still reads as design evidence, not migration readiness evaluation

---

## Planned Output Shape

The main output should be the concrete row table.

After the table, include the following support lists:

1. hotspot caution list
2. hold list
3. extraction-candidate list
4. compare candidate list

---

## Assumptions & Open Questions

Assumptions:

- the selected assets are sufficient to stress the rules meaningfully
- not every ambiguous case requires immediate settlement
- the row method is strong enough to expose weak rules without expanding scope

Open questions:

- whether some storage files will consistently trend toward extraction-candidate outcomes
- whether orchestration examples reveal one mixed class or several distinct classes
- whether overview-style materials consistently behave as extraction sources
- whether viewer-facing routing logic produces more compare pressure than expected

---

## What This Run Decides

- the representative concrete row set
- row-level destination proposals
- row-level outcome categories
- row-level rationale and caution structure
- compare-routing candidate evidence

---

## What This Run Does Not Decide

- final migration map
- file move order
- import rewrites
- compare document completion
- implementation authorization
- migration readiness
