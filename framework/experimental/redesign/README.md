# APSF Reconstruction Design Package

This directory contains a design-first package for APSF reconstruction.

It is intentionally limited to architectural framing and review, not migration
execution. The package is meant to support parallel comparison with the current
APSF while avoiding premature implementation commitment.

---

## Purpose

This package exists to define and review a reconstruction direction based on:

- `core` as stable responsibility boundaries and contracts
- `legacy` as the current APSF preserved as a readable reference
- `experimental` as a discardable redesign space
- viewer as an independent support layer rather than a canonical record authority

See also: [GUI Operation North Star](./gui-operation-north-star.md)

This note defines the longer-term operating target behind the current redesign
work: GUI-first, human-led operation where run type, required checks, and next
triggers can eventually be handled through guided interaction rather than
manual document assembly.

See also: [SoChi Public Site Improvement Report](./sochi-public-site-improvement-report.md)

This report acts as a parent source for selecting narrow SoChi BLOCKS
follow-ups. It should be used as a shortlist-and-cut document, not as a
single large execution package.

---

## Files

- `goal.md`
  Defines the design-run objective, constraints, and explicit non-goals.
- `plan.md`
  Defines the directory strategy, classification rules, shared policy,
  core prohibitions, and comparison policy.
- `review.md`
  Defines the architectural review gate:
  what would count as failure and what must remain true.
- `result.md`
  Records the current decision:
  Accept with Minor Revisions, with safe interpretation and next-step boundaries.

Follow-up trial documents now live under `followups/` so that narrow,
topic-specific packages do not crowd the reconstruction package root.

---

## What This Package Is Not

This package is not:

- a migration execution plan
- a file-move authorization
- a final adoption decision
- a viewer-led replacement of durable Markdown records

---

## Current Position

Current status:

- The direction is accepted with minor revisions.
- The design is strong enough for follow-up planning.
- The next run should still remain design-oriented.

---

## Safe Next Use

Use this package as the reference set for a follow-up planning run that produces:

- a representative asset classification table
- a repo-specific directory mapping proposal
- compare material under `docs/compare`
- implementation-planning acceptance criteria

Do not use this package by itself as authorization to begin migration.
