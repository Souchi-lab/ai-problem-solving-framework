# Goal

---

## Objective

Add a lightweight "next recommendation" to the SoChi BLOCKS public site so that
users are guided toward one sensible next puzzle instead of needing to choose
again from a flat list.

This follow-up should improve continuity and reduce hesitation after the first
selection or first clear without introducing a full recommendation system.

---

## Why This Follow-up

Recent follow-ups improved:

- initial entry
- difficulty clarity
- viewer interaction clarity

The next natural friction point is:

- what should the player do next?

If the site can suggest one reasonable next puzzle, it becomes easier to keep
playing without thinking too much about selection.

---

## In Scope

- Add one narrow next-puzzle recommendation surface
- Prefer a deterministic recommendation rule over a complex ranking system
- Improve continuity after choosing or clearing a puzzle

---

## Out of Scope

- Full recommendation engine
- Personalized ranking
- Large puzzle-list redesign
- Analytics-heavy optimization
- Multi-step progression system

---

## Success Criteria

1. The site can show one reasonable next recommendation without needing a large
   new system.
2. The recommendation logic stays simple and explainable.
3. The UI change remains local and does not widen into a puzzle-list overhaul.
4. The result can be judged by whether "what next?" becomes easier to answer.
5. The follow-up remains about continuity, not gamification.

---

## Notes For Planner

The most important planning question is:

- where a single next recommendation helps the user most with the least UI cost

Likely candidate surfaces:

- after clear
- near the featured / first-puzzle area
- near the puzzle list

The planner should prefer:

- one recommendation
- one simple rule
- one small UI surface

---

## Non-Goals

- Solving all replay and retention issues at once
- Building a smart recommendation model
- Mixing this with SEO, language, or full KPI work

---

## Desired Landing

At the end of this follow-up, the repo should have:

- a narrow next-recommendation rule
- one small UI surface where it appears
- a result stating whether the recommendation improved continuity without
  widening scope
