# Plan

---

## Follow-up Context

- Parent series: SoChi BLOCKS public-site improvement follow-ups
- Previous result: mobile-tray and operation-mode improvements confirmed the
  pattern of narrow investigation before fix
- New trigger: puzzle-specific URLs exist but page metadata does not reflect
  puzzle identity, weakening shareability and search legibility
- Scope limit: puzzle-page metadata only, no full SEO overhaul or routing
  redesign

---

## Run Metadata

- Pattern: P-01 Feature Implementation (conditional — see branching below)
- Goal: identify the smallest path to per-puzzle title / description / OGP and
  implement it, or define the boundary and hand off to a structural follow-up
- Output focus: investigation → implementation or bounded design, result confirms
  which path was taken

---

## Goal Readiness Check

- The puzzle URL structure already exists
- Current page metadata likely does not change per puzzle (to be confirmed)
- React SPA context means `<title>` and client-side meta are achievable cheaply,
  but OGP for crawlers may require prerender or SSR
- The run can still close narrowly if the investigation reveals a cheap path for
  at least one meaningful surface

Decision: Proceed — with a conditional branch (see below)

---

## Problem Structure

### Surface 1 — Page title (`<title>`)

- For in-browser tab and some search contexts
- In a React SPA: achievable with `document.title` in `useEffect` or a head
  management library (e.g. React Helmet)
- Does not require SSR or prerender

### Surface 2 — Meta description (`<meta name="description">`)

- For search snippet context
- In a React SPA: same as Surface 1, but search crawlers may or may not execute
  JS to see client-side updates

### Surface 3 — OGP tags (`og:title`, `og:description`, `og:image`)

- For social share previews (Twitter/X, LINE, etc.)
- Social crawlers typically do not execute JavaScript
- Requires either SSR, prerender, or a static metadata route to be reliable

### Key Distinction

| Surface | Client-side only | SSR / prerender needed |
|---|---|---|
| `<title>` (tab) | ✅ works | not required |
| `<meta description>` (JS-aware crawlers) | partial | preferred |
| OGP (social crawlers) | ❌ unreliable | required |

This distinction determines which branch the implementation takes.

---

## Conditional Branch

### Branch A — Cheap path exists (primary target)

If the app already has prerender, SSR, or a static metadata mechanism:

- Add per-puzzle metadata to that existing surface
- Implement title + description + OGP in one pass
- This is a standard P-01 implementation

### Branch B — Only client-side is feasible now

If no prerender / SSR exists:

- Implement `<title>` + client-side meta update only (Surface 1 + 2)
- Record the OGP gap clearly
- This is a partial P-01: meaningful for users, limited for social crawlers

### Branch C — SSR / prerender is required and not present

If OGP is the main value and client-side is insufficient:

- Do not implement; define the structural requirement and hand off
- This run becomes P-06: output is a bounded design + next follow-up trigger
- Implementation is deferred to a structural follow-up

---

## Investigation Steps (before implementation)

1. Check the current `<title>` on a puzzle page — is it generic or per-puzzle?
2. Check whether any `<meta>` or OGP tags exist per puzzle
3. Identify how the app sets `<title>` today (static HTML, useEffect, Helmet, etc.)
4. Check whether a prerender or SSR mechanism exists in the build config

The branch is selected after these four checks.

---

## Execution Plan

- [ ] Step 1: Investigate current puzzle-page metadata (title, meta, OGP)
- [ ] Step 2: Identify the current head-management mechanism
- [ ] Step 3: Check for prerender / SSR capability
- [ ] Step 4: Select branch (A / B / C) based on findings
- [ ] Step 5 (Branch A or B): Implement the minimum metadata change
- [ ] Step 5 (Branch C): Write the structural requirement and close as design-only
- [ ] Step 6: Verify metadata in browser and (if applicable) OGP preview tool
- [ ] Step 7: Write result.md with branch taken, what changed, and what remains

---

## Implementation Readiness

- [ ] Current `<title>` behavior confirmed before writing code
- [ ] Head-management mechanism identified (not assumed)
- [ ] Branch selected before any code change
- [ ] If Branch A or B: change is contained to one component or hook
- [ ] If Branch C: no code written; output is design document only

---

## Scope Policy

Allowed:
- per-puzzle `<title>` update
- per-puzzle `<meta name="description">` update
- per-puzzle OGP tags (if prerender / SSR already exists)
- one head-management component or hook

Not allowed:
- full SEO strategy work
- routing restructure
- introduction of SSR / prerender as a new architecture (this follow-up)
- i18n or language-toggle integration
- KPI or analytics setup

---

## Deliverables

- branch determination record (A / B / C) with rationale
- implementation (Branch A or B) or design handoff (Branch C)
- result.md confirming what changed and what remains

---

## Review Policy

Review can be skipped if:
- the implementation stays in Branch A or B
- the change is one component or hook
- the branch determination is clear

Restore review if the investigation reveals unexpected structural complexity.

---

## Result Evaluation Frame

result.md should answer:

1. Which branch was taken, and why?
2. What is now visible in the page metadata per puzzle?
3. What is still missing (OGP for social crawlers, if Branch B)?
4. Did the change stay local to one component or hook?
