# APSF Viewer TODO

This file is the working backlog for continued APSF Viewer development.

Use this as the canonical follow-on list for viewer-specific work.
Run-specific details still live in each run's `build.md` / `review.md` / `result.md`, but viewer work that continues across runs should be summarized here.

---

## Current State

Delivered:

- read-only run viewer
- phase-aware primary command display
- bounded operator actions
- rerun comment workflow
- supporting artifact routing:
  - `plan_review.md`
  - `build_review.md`
  - `review_review.md`
  - `improve_review.md`
- backend-owned command execution
- `SUCCESS / PARTIAL / FAILED` result display
- polling-based run state auto-refresh

Known environment caveat:

- `cmd /c npx tsc -b` passes
- `vite build` is still environment-sensitive in this workspace because of the existing Tailwind native dependency / `spawn EPERM` issue

---

## Active Follow-ons

### Priority Triage

P1:
- state sync / stale render fixes
- responsive layout / compact layout
- scroll pressure / sticky primary actions

P2:
- sibling visibility while child is targeted
- primary command as direct action affordance
- stronger save feedback for rerun comments

P3:
- short-artifact / "silent 4 lines" guidance

### 1. Real Browser UI Smoke

Goal:
- record an actual browser click-through proof for the viewer operator workflow

Why:
- the current operator features are implemented and statically verified, but a true browser-side proof would reduce review friction

Possible scope:
- open viewer
- select a run
- save a rerun comment
- execute a rerun action against a safe test run
- confirm phase refresh in UI

---

### 2. Advanced Execution Options

Goal:
- expose selected CLI/build options in the viewer for heavier operations

Examples:
- `MaxTurns`
- `DryRun`
- `Skip*Scaffold`

Why:
- normal operation can be GUI-driven, but heavy build/debug cases still fall back to CLI

Recommended approach:
- keep default UI simple
- add an "Advanced" section per action rather than cluttering the main flow

---

### 3. Better Auto-Refresh Model

Goal:
- improve state freshness beyond simple polling

Current state:
- run list refreshes every 30s
- selected run detail refreshes every 10s

Follow-on options:
- manual refresh button
- smarter polling after command execution
- eventual websocket / server-sent events if justified later

---

## UI / UX Improvements

### 4. Visual Polish Pass

Related run:
- `2026-03-23-005_fw-improvement_viewer-ux-improvements`

Candidate topics:
- clearer operator hierarchy
- more legible rework badges
- artifact panel readability
- stronger distinction between guidance-only and executable actions
- mobile/compact layout improvements
- responsive 3-column collapse / preview maximize
- sticky or duplicated primary actions to reduce long-scroll friction
- stronger saved-state feedback on rerun comment save
- primary command action affordance near the displayed command

Note:
- keep workflow correctness ahead of cosmetics

Recommended source findings:
- screen size flexibility issue
- scroll endurance issue
- save feedback too subtle
- primary command is display-only

---

### 5. Action Safety UX

Goal:
- reduce accidental misuse without slowing normal operation

Ideas:
- stronger warning copy for rerun actions
- clearer "guidance only" styling
- explicit labels for:
  - `human-owned`
  - `writes supporting artifact`
  - `resets phase`

---

## Workflow / Data Improvements

### 6. Comment History and Audit Trail

Current state:
- comments are append-only in the supporting artifact

Possible follow-ons:
- show latest saved rerun comment in UI
- highlight the target artifact section after save
- lightweight local audit panel

Not needed yet:
- multi-user attribution
- edit/delete workflow
- database-backed history

---

### 7. Better Command Result Presentation

Current state:
- post-completion stdout/stderr capture only

Follow-ons:
- streaming output
- collapsible logs
- phase delta summary after command completion

---

### 8. Supporting Artifact Awareness

Goal:
- make artifact semantics easier to understand from the viewer

Ideas:
- show which artifact will receive a rerun comment before save
- show scaffold-vs-existing state
- show last modified time near rerun comment targets

---

## Longer-Term Ideas

### 9. Run-Creation / Setup Assistance

Potential future scope:
- start a new run from GUI
- prefill template files
- suggest next taxonomy / naming

This is explicitly later than operator workflow stabilization.

### 10. Phase Graph / Dependency View

Potential future scope:
- richer visualization of phase transitions and rework loops
- parent/child run relationships
- viewer-side transcript entry points

Useful, but not urgent.

### 11. Child Target Navigation Refinement

Potential future scope:
- keep focused child as active target
- still show sibling children in compressed form
- make child-to-child comparison faster without returning to parent

This is a better fit than hiding all siblings once a child is targeted.

### 12. Detector Guidance For Short Artifacts

Potential future scope:
- when phase detection treats a file as effectively empty, explain the reason in the viewer
- optionally surface a hint such as "file exists but is below readiness threshold"

Note:
- this is partly a viewer concern and partly an APSF core/phase-detector concern
- if the underlying 4-line rule changes, update viewer messaging accordingly

### 13. Reliability: Target / Tab Sync

Highest-priority reliability follow-on:
- investigate and eliminate cases where target tab, header, or persisted history briefly shows stale state after switching

This is not cosmetic. Treat as correctness / trust issue first.

---

## What Not To Do Yet

- database-backed viewer state
- arbitrary shell execution
- multi-user coordination
- background job queue/orchestrator
- full editor for all run artifacts
- heavy real-time infra

---

## Update Rule

When a viewer-related fw-improvement run closes:

1. keep the detailed record in that run's artifacts
2. update this file with any surviving follow-ons
3. remove or shrink items that were actually completed

---

## Run Mapping

Use the following run mapping as the default routing for known follow-ons:

- `2026-03-23-005_fw-improvement_viewer-ux-improvements`
  - responsive layout / compact layout
  - sticky actions / scroll relief
  - save feedback strengthening
  - primary command affordance

- `2026-03-23-007_fw-improvement_viewer-priority-layer`
  - run prioritization only
  - do not mix general UX polish into this run

- `2026-03-24-011_fw-improvement_viewer-codex-architect-bridge`
  - Codex invocation bridge only
  - do not mix viewer rendering work into this run

- new follow-on run recommended:
  - sibling visibility while child-targeted
  - target/tab/history sync reliability
  - short-artifact readiness hinting if treated as viewer work
