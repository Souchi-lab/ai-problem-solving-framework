# SoChi BLOCKS Public Site Improvement Report

## Purpose

This note is a source report for selecting narrow follow-ups on the SoChi BLOCKS
public site.

It is not intended to be executed as one large change.
Use it as a parent document, then cut small follow-ups from the shortlist.

## Priority Shortlist

Recommended early follow-up candidates:

1. Top-page primary CTA
2. How-to page relief
3. Single-language display / language toggle
4. Operation mode split
5. Empty-state copy
6. Per-puzzle meta / OGP
7. Basic KPI instrumentation

---

# Executive Summary

The public site already has a strong core proposition: a browser-playable 3D
pentomino-style puzzle with a short introduction, clear difficulty ladder, and
lightweight entry into play.

At the same time, the site still has large improvement headroom in the areas
that most directly affect growth and repeat use:

- start-play friction
- language UX / i18n
- operation clarity for first-time users
- accessibility baseline
- SEO for JS-heavy pages
- measurement and regression prevention

The five highest-value themes are:

1. Redesign the shortest path into play
2. Fix JP/EN mixed-display UX
3. Separate movement and rotation more clearly
4. Establish an accessibility baseline for the 3D viewer
5. Make measurement / Lighthouse / CI part of normal workflow

---

# Current State Summary

## Main Pages

- Top page
  - concept
  - 3-step how-to
  - difficulty ladder
  - puzzle list
  - about / story
- How-to-play page
  - short goal explanation
  - 3-step replay of the basics
- Viewer pages
  - puzzle-specific pages via `viewer.html?puzzle_id=...`

## Assumed User Flow

The intended flow appears to be:

`top -> how-to or difficulty selection -> viewer -> clear -> next puzzle`

This supports first-time onboarding and repeat play, but the first-click path is
still heavier than necessary.

## Technical Observations

- The current operation model combines piece selection, rotation, placement, and
  confirm
- Progress UI exists, but the empty state is weak
- JP and EN often appear together on the same page
- Puzzle identity is URL-based, which is good for sharing, but page-specific
  metadata needs to catch up

---

# Problem List

## High-Priority Problems

### 1. First-view CTA does not cleanly match "start playing now"

The current top-page flow still risks pushing users into reading before playing.
That weakens first-start conversion.

Recommended response:

- make the primary CTA start a first puzzle directly
- keep how-to as a secondary support path

### 2. JP/EN mixed display increases cognitive load

Showing both languages together makes pages visually heavier and less scannable.
It also creates avoidable confusion for assistive technologies.

Recommended response:

- move to single-language display by default
- use a clear language toggle
- later align URLs and `hreflang`

### 3. Rotation vs movement is not clear enough

If the same symbols or key ideas appear to mean different things depending on
mode, first-time users cannot predict the result of an action.

Recommended response:

- visually split rotate vs move
- show current mode explicitly
- consider stronger key/UI separation

### 4. Accessibility baseline is not yet established

A 3D / canvas-heavy interface can easily become unusable for keyboard-only and
assistive-technology users if the baseline is not designed explicitly.

Recommended response:

- improve focus visibility and focus flow
- add labels and accessible names where needed
- introduce reduced-motion support
- provide lightweight textual state or alternate explanatory output

### 5. Measurement and regression prevention are weak

Without event tracking and recurring audits, improvements are difficult to
prioritize and harder to defend.

Recommended response:

- define a minimal KPI event set
- add Lighthouse checks
- add CI / E2E where practical

## Medium-Priority Problems

### 6. Video expectation and destination may not match

If the UI promises video guidance but routes to a text page, users can feel a
mismatch.

### 7. Puzzle list discoverability can improve

Filtering, sorting, and "recommended next" guidance appear underdeveloped.

### 8. Progress empty state is weak

An empty progress display can look broken instead of simply "not started yet."

### 9. Per-puzzle SEO and sharing are underpowered

Puzzle pages need page-specific title, description, and OGP support to convert
shared links and search impressions effectively.

---

# Improvement Directions

## Functional Improvements

- One-click first puzzle start
- Undo / Redo / Reset
- staged hints
- clear-post next recommendation
- share buttons and link affordances

## UI / UX Improvements

- persistent on-screen control guide
- explicit mode display for move / rotate
- clearer difficulty cards

## Accessibility Improvements

- WCAG 2.2 baseline
- keyboard reachability
- visible focus states
- reduced-motion option
- textual / alternate state hints for the 3D board

## Performance Improvements

- Lighthouse / PSI baseline and recurring checks
- reduce unnecessary rendering work
- add lower-load rendering modes where helpful
- code-split viewer-heavy JS from lightweight pages

## SEO Improvements

- Search Essentials baseline
- JS-SEO-aware page structure
- puzzle-specific title / description / OGP
- static explanatory content on puzzle pages
- localized URL strategy with `hreflang`

## Content Improvements

- FAQ for common first-time confusion
- clearer explanation of educational / cognitive value

## Workflow Improvements

- CI via GitHub Actions
- E2E via Playwright
- Lighthouse in the normal review loop

---

# Rough Estimates

These are intentionally coarse and should be treated as planning guidance only.

| Item | Difficulty | Person-days | Priority |
|---|---:|---:|---:|
| Top-page first-puzzle CTA | Low | 1.0 | High |
| Single-language display cleanup | Medium | 3.0 | High |
| `hreflang` / localized URL alignment | Medium | 2.5 | High |
| Move / rotate mode split | Medium | 4.0 | High |
| Onboarding improvement | Medium | 3.0 | High |
| Undo / Redo / Reset | Medium | 3.0 | High |
| Hint system | High | 5.0 | Medium |
| Clear-post next recommendation | Low | 1.5 | Medium |
| Per-puzzle meta / OGP | Medium | 2.5 | High |
| Static share / SEO summary on puzzle pages | Medium | 2.0 | Medium |
| Accessibility baseline | High | 6.0 | High |
| Performance optimization | High | 6.0 | Medium |
| KPI instrumentation | Medium | 2.0 | High |
| CI + E2E | Medium | 4.0 | High |
| Lighthouse automation | Medium | 2.0 | Medium |
| FAQ / helper content | Low | 2.0 | Medium |

---

# KPI Proposal

## Product KPIs

- top-page to viewer start rate
- how-to page to viewer rate
- first-clear rate on Easy
- median first-clear time
- retry / reset / undo usage rate
- share rate after clear

## Quality KPIs

- Lighthouse Performance
- Lighthouse Accessibility
- Lighthouse SEO
- Core Web Vitals where measurable
- count of accessibility-critical defects

## SEO KPIs

- indexed page count
- search impressions / CTR
- OGP / share-card correctness rate

---

# Execution Guidance

Recommended order:

1. establish baseline measurement
2. fix top-page start-play path
3. reduce mixed-language display
4. clarify viewer controls and beginner guidance
5. add accessibility baseline
6. improve puzzle-page metadata / sharing
7. address performance
8. add CI / E2E / Lighthouse automation

---

# Follow-up Usage

Use this report as a parent source.

Good follow-up examples:

- `top-page-cta`
- `how-to-page-relief`
- `language-toggle`
- `empty-state-copy`
- `operation-mode-split`
- `per-puzzle-meta-ogp`
- `basic-kpi-instrumentation`

The report should stay broad.
Execution should happen through narrow follow-ups only.
