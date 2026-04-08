# Plan

---

## Follow-up Context

- Parent series: SoChi BLOCKS public-site improvement follow-ups
- Previous result: `operation-mode-split` identified a mobile tray empty-space
  issue during validation and recorded it as scope-out observation
- New trigger: tray area below the horizontal scroll bar is visually unbalanced
  on mobile layouts
- Scope limit: tray-zone layout only, no broader mobile or responsive redesign

---

## Run Metadata

- Pattern: P-02 Bug Fix
- Goal: identify source of tray empty space and remove it with the smallest
  local CSS change
- Output focus: narrow diagnosis + targeted fix + before/after visual check

---

## Goal Readiness Check

- The problem is visually specific: excessive empty space below the tray scroll bar
- The expected state is clear: no dead space without making the tray cramped
- The likely fix is small (padding / min-height / media query adjustment)
- This can be judged by before/after inspection on a mobile viewport

Decision: Proceed

---

## Problem Structure

The empty space has one of three sources. Only one of them requires a fix
for this follow-up.

### Hypothesis A — Tray component height

The tray component itself has a fixed or min-height that is larger than needed
on mobile. The space below the scroll bar is unused height inside the component.

Fix if true: reduce or remove the fixed height on the tray component for mobile.

### Hypothesis B — Parent container padding / gap

The container wrapping the tray has padding-bottom, gap, or margin-bottom that
adds visual space below the tray area on narrow viewports.

Fix if true: reduce or remove the excess spacing in the parent container's
mobile styles.

### Hypothesis C — Mobile-only media query behavior

A media query applies a height, min-height, or padding specifically at mobile
breakpoints that creates the gap.

Fix if true: adjust or remove the relevant media-query rule.

---

## Selected Approach

1. Inspect the tray component and its parent container in the SoChi BLOCKS
   viewer source.
2. Identify which hypothesis (A, B, or C) is the source.
3. Apply the smallest change that removes the gap.
4. Verify on a mobile viewport (or simulated mobile in devtools).

Do not touch:
- desktop layout
- piece tray interaction logic
- any spacing outside the tray zone
- operation-mode hint area (already addressed)

---

## Execution Plan

- [ ] Step 1: Identify the tray component and its parent in the viewer source
- [ ] Step 2: Check which of A / B / C is producing the gap
- [ ] Step 3: Apply the targeted CSS fix (one rule or one block)
- [ ] Step 4: Visual check on mobile viewport — gap gone, tray not cramped
- [ ] Step 5: Write result.md with before/after and scope confirmation

---

## Implementation Readiness

- [ ] Reproduction confirmed: mobile viewport shows obvious gap below tray scroll
- [ ] Source identified before writing the fix (do not guess and patch)
- [ ] Fix is one CSS change — if more than two rules need changing, stop and
  re-diagnose
- [ ] Desktop layout unaffected after change

---

## Scope Policy

Allowed:
- tray component height / min-height on mobile
- parent container padding / gap on mobile
- one media-query rule adjustment

Not allowed:
- desktop layout changes
- interaction or scroll behavior changes
- viewer-wide spacing cleanup
- animations or transitions

---

## Deliverables

- diagnosis record (which hypothesis was correct)
- one targeted CSS fix
- result.md confirming visual improvement and scope

---

## Review Policy

Review can be skipped.

The fix is a single CSS adjustment with a clear visual before/after.
If the investigation finds the source to be more complex than one hypothesis,
restore review before proceeding.

---

## Result Evaluation Frame

result.md should answer:

1. Which of A / B / C was the actual source?
2. Did the fix remove the gap without making the tray feel cramped?
3. Did the change stay within one CSS rule or block?
4. Is the desktop layout unchanged?
