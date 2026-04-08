# Backend + Viewer Reconstruction Memo

Date: 2026-04-08
Trigger: Start after `2026-04-04-001_investment-project_v0-1` is complete.
Related note: `framework/improvement-notes/2026-04-07_child-run-dependency-injection.md`

---

## Summary

Recent fixes improved the current APSF workflow, but they also exposed a broader structural problem:

- state transitions are split across CLI, wrapper scripts, Viewer actions, and repair logic
- `run_state.json`, `artifact_manifest.json`, and advisory detection do not always change together
- rerun / restore / partial build / manual save use different update paths
- parent run vs child run targeting is still too easy to get wrong

This should be handled as a reconstruction task, not as endless local patching.

---

## Why Reconstruct

The recent incidents were not isolated UI bugs. They came from responsibility drift across the stack.

Observed failures:

- `Judge and Return to Build` did not always move the run back to `BUILD_NEEDED`
- rerun wrappers could stop on stale human-owned blocker text
- `review.md` could save successfully while the phase still stayed `REVIEW_NEEDED`
- parent/child run targeting was easy to confuse in the Viewer
- Activity / Agent OS / Last Action needed repeated compensation logic in the frontend

These are all signs that the system is relying too much on "detect and repair later" instead of "update correctly at write time."

---

## Reconstruction Goal

Rebuild the workflow around one canonical transition model.

Target state:

- one backend transition service owns phase changes
- `run_state.json` is treated as the canonical live state
- artifact writes and phase transitions are synchronized by design
- rerun / restore / partial build / write-phase all go through the same transition layer
- Viewer renders canonical API state and stops doing local correction where possible
- wrapper scripts become thin transport/invocation layers

---

## Priority Topics

### 1. Transition ownership

Current ownership is split across:

- `apsf write-phase`
- `apsf act`
- rerun PowerShell scripts
- build/review wrappers
- Viewer-side action handlers
- `apsf next` style repair/re-evaluation paths

This should be collapsed into one service with explicit transition rules.

### 2. Manifest/state consistency

The system should guarantee that these move together:

- artifact file creation/removal
- `artifact_manifest.json`
- `run_state.json`
- phase owner / retry / handoff cleanup

No separate "repair" path should be needed for normal operation.

### 3. Parent/child run model

The system needs a cleaner model for:

- top-level run actions vs child run actions
- execution target selection
- activity/history scope
- child-run dependency visibility

This is where the related note below becomes important.

### 4. Viewer responsibility reduction

The Viewer currently compensates for backend ambiguity in several places.

Desired direction:

- API returns canonical resolved state
- UI does not infer or repair workflow state on its own
- labels and actions reflect actual workflow concepts rather than implementation vocabulary

### 5. CLI backend selection precedence

Current wrapper backend selection is too easy to override unintentionally.

Observed issue:

- Viewer config can be set to `codex-cli`
- but a run-local `execution-assignment.md` with `Tool / Method = claude` still forces the build wrapper toward Claude
- this makes global operator intent weaker than stale run-local planning text

Desired rule:

- if only one CLI backend is configured, use that backend
- if both backends are available, use the config-recommended backend by default
- only use run-local execution assignment as an override when it is intentionally and explicitly set for that run

Reconstruction implication:

- backend choice precedence should be defined canonically
- Viewer config, execution assignment, and wrapper backend hint must follow one explicit resolution order
- stale child-run planning text should not silently defeat current operator config

### 6. Codex adoption boundary by role

Codex is promising, but full replacement of Claude across all APSF roles is not yet risk-free.

Observed concerns:

- `build` is a strong fit for Codex because the task is code-heavy and tool-enabled
- `plan` and `review` are more artifact-format-sensitive, so bridge stability and write-path enforcement matter more
- existing APSF wrappers, tests, and operational assumptions are still more mature on the Claude path
- codex bridge support had to be extended incrementally (`PLAN_NEEDED` first, then `REVIEW_NEEDED`)

Working stance for reconstruction:

- treat backend/tool choice as a first-class workflow concern, not an ad-hoc per-script detail
- define which phases are safe for Codex by default and which phases still require extra guardrails
- keep it easy to route a specific phase back to Claude when Codex output stability is not yet sufficient

Practical current stance:

- Builder: Codex is a good default
- Critic: Codex is viable, but still needs bridge hardening and artifact validation confidence
- Planner: Claude remains the safer default until Codex plan bridge has more operational proof
- AI advisory / consultation: Codex is worth using, but still needs phase-aware fallback and stability review

Reconstruction implication:

- backend selection policy should be encoded centrally
- wrapper capability boundaries must be visible in one place
- phase-specific fallback policy should be explicit instead of being discovered by failure at runtime
- advisory/chat surfaces should also follow the same policy instead of being silently Claude-only

---

## Specific Follow-Up: Child Run Dependency Injection

`framework/improvement-notes/2026-04-07_child-run-dependency-injection.md` should be revisited during reconstruction, not treated as a separate cosmetic note.

Reason:

- child run dependency handling touches planner output, execution assignment, builder prompts, critic checks, and Viewer navigation
- it is tightly connected to the same parent/child targeting and transition ownership problems

Expected reconstruction outcome:

- child dependencies are represented explicitly in the canonical backend model
- builder/planner/critic prompts derive from that model instead of ad-hoc prompt composition
- Viewer can show dependency context without special-case patching

---

## Proposed Sequence

1. Inventory every current phase transition path and artifact write path.
2. Define the canonical transition model and state mutation rules.
3. Implement a backend transition service first.
4. Route CLI, wrappers, rerun actions, and Viewer actions through that service.
5. Remove repair-style logic that only exists to compensate for split ownership.
6. Revisit child-run dependency injection on top of the new model.
7. Define canonical CLI backend selection precedence across config and run-local assignment.
8. Define role/phase-specific Codex adoption policy and fallback rules.
9. Clean up Viewer UX and terminology after the backend model is stable.

---

## Non-Goal

Do not start with a pure UI rewrite.

The frontend should be cleaned up, but only after the transition/state model is made coherent enough that the Viewer can become thinner.

---

## Start Condition

Begin this work after `2026-04-04-001_investment-project_v0-1` is finished.
