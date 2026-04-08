# Goal

---

## Objective

Add per-puzzle page metadata for SoChi BLOCKS so that each puzzle page can
present a more specific title, description, and share preview context.

This follow-up should improve shareability and search/readability for individual
puzzle pages without turning into a full SEO overhaul.

---

## Why This Follow-up

The public-site improvement report identified puzzle-page metadata as a
high-value improvement because SoChi BLOCKS already has puzzle-specific URLs,
but the page-level metadata does not yet fully reflect puzzle identity.

That means:

- shared links may look generic
- puzzle pages may be less legible in search or preview contexts
- the URL structure has more value than the page metadata is currently using

---

## In Scope

- Investigate how puzzle pages are currently rendered and shared
- Identify the smallest place to inject per-puzzle title/description/OGP context
- Define a narrow implementation target for puzzle-specific metadata

---

## Out of Scope

- Full SEO strategy redesign
- Full structured-data implementation
- Full SSR / prerender architecture redesign
- Broad content rewrite across the whole site
- KPI or analytics work

---

## Success Criteria

1. It becomes clear whether per-puzzle metadata can be added with a narrow
   implementation path.
2. The follow-up identifies the smallest realistic metadata surface to improve.
3. The task remains puzzle-page focused and does not widen into a full SEO
   project.
4. The outcome can be judged by whether puzzle identity becomes more visible in
   page metadata and sharing context.
5. The result clearly states what was improved and what still remains out of
   scope.

---

## Notes For Planner

The most important planning question is:

- where the puzzle-specific metadata can be introduced with the least structural
  disruption

Possible surfaces may include:

- HTML template metadata
- runtime title/description update
- share-page generation
- puzzle-specific static page generation

The planner should prefer the smallest path that meaningfully improves puzzle
identity in metadata.

---

## Non-Goals

- Solving all SEO concerns at once
- Reworking the entire routing system
- Mixing this task with language/i18n redesign
- General site copy cleanup

---

## Desired Landing

At the end of this follow-up, the repo should have:

- a narrow understanding of the current puzzle-page metadata path
- a bounded implementation direction for per-puzzle metadata
- a result that says whether this can be improved cheaply or needs a broader
  structural follow-up
