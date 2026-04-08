# Goal

---

## Objective

Add a lightweight current-mode cue to the SoChi BLOCKS viewer so that players
can more easily tell what kind of action they are currently focused on.

This follow-up should improve moment-to-moment clarity after
`operation-mode-split` without changing the underlying control model.

---

## Why This Follow-up

`operation-mode-split` made the viewer hints easier to read by separating:

- where to place
- how to rotate

The next natural question is whether a small current-state cue would further
reduce hesitation during actual play.

This is a refinement follow-up, not a rescue fix.

---

## In Scope

- Add a small viewer-side cue for the current action focus or state
- Keep the cue visually lightweight
- Align the cue with the already separated move/place vs rotate hint structure

---

## Out of Scope

- Full control-model redesign
- Input remapping
- New tutorial system
- Large HUD rewrite
- Broad animation or mode-system changes

---

## Success Criteria

1. The cue makes the current interaction state easier to infer at a glance.
2. The change remains small and local to the viewer UI.
3. The cue complements `operation-mode-split` rather than replacing it.
4. The implementation can be judged by short live inspection.
5. The work does not widen into a broader interaction redesign.

---

## Notes For Planner

The most important planning question is:

- what smallest cue is enough to help the player understand the current focus

Possible forms may include:

- a small "Now:" label
- a highlighted section in the hint block
- a state-dependent sublabel

The planner should prefer the smallest cue that improves clarity without making
the HUD feel busy.

---

## Non-Goals

- Solving every viewer clarity problem at once
- Rebuilding the whole sidebar
- Mixing this with copy/SEO/language tasks

---

## Desired Landing

At the end of this follow-up, the repo should have:

- a narrow design for a current-mode cue in the viewer
- a result stating whether the cue was worth adding after
  `operation-mode-split`
