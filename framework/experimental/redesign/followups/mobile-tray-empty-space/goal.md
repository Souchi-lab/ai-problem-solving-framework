# Goal

---

## Objective

Reduce the visually awkward empty space below the horizontal piece-selection
area on mobile layouts in SoChi BLOCKS.

This follow-up should improve density and visual balance around the tray area
without redesigning the whole mobile viewer layout.

---

## Why This Follow-up

During validation of `operation-mode-split`, one additional mobile-only issue
was observed:

- the area below the horizontal piece-selection scroll bar feels emptier than it
  should

This does not block play, but it weakens the polish of the mobile play screen
and stands out once the higher-priority control-hint issue is improved.

---

## In Scope

- Investigate the mobile tray area below the horizontal scroll section
- Identify whether the gap comes from tray height, parent spacing, or mobile-only
  layout rules
- Reduce the empty space with the smallest layout change that preserves
  usability

---

## Out of Scope

- Full mobile HUD redesign
- Piece tray interaction redesign
- Desktop layout tuning
- New animations or transitions
- Unrelated viewer spacing cleanup outside the tray zone

---

## Success Criteria

1. The mobile tray area no longer shows obviously excessive empty space below
   the horizontal scroll section.
2. The change stays local to tray-related layout rules.
3. Tray usability does not get worse on touch devices.
4. The fix can be judged visually with a short before/after check.
5. The work remains a small UI adjustment, not a broad responsive redesign.

---

## Notes For Planner

The most important planning question is:

- where the empty space is actually coming from

The planner should distinguish between:

- tray component height
- parent container padding / gap / min-height
- mobile-only media-query behavior

Prefer the smallest change that removes the visual dead space without making
the tray feel cramped.

---

## Non-Goals

- Solving every mobile spacing issue at once
- Reworking the whole sidebar / tray composition
- Mixing this task with operation-mode, language, or SEO improvements

---

## Desired Landing

At the end of this follow-up, the repo should have:

- a narrow explanation of the source of the tray empty space
- a small mobile-layout fix targeted at that source
- a short result stating whether the visual balance improved without widening
  scope
