# Branch-First Implementation Pattern

## Purpose

This note records a reusable pattern for follow-ups where implementation is
intended, but the correct implementation path depends on what the codebase
inspection reveals.

This became clear in tasks like per-puzzle metadata, where multiple valid paths
existed and the right one could only be chosen after local inspection.

---

## Pattern

1. Define Branches Before Editing

- Write the realistic implementation branches up front
- Example:
  - Branch A: full implementation path available
  - Branch B: partial but still worthwhile implementation path
  - Branch C: implementation not justified, close as design-only

2. Inspect the Real System

- Check the actual code path, build shape, and architectural constraints
- Do not commit to a branch before this inspection

3. Select the Matching Branch

- Decide which branch matches the current architecture
- Treat this as a design decision, not an improvisation

4. Implement Only That Branch

- Make the smallest change required by the selected branch
- Do not drift into the other branches' scope

5. Record Why That Branch Was Correct

- In `result.md`, explain why the chosen branch matched the current structure
- Also explain what was intentionally left out of scope

---

## Why It Works

This pattern prevents two common failures:

- assuming the strongest implementation path is available before checking
- treating a narrower branch as a compromise instead of the correct fit

It keeps the run honest:

- branch space is visible early
- the chosen path is justified by inspection
- implementation remains bounded

---

## Good Use Cases

- metadata / SEO tasks
- sharing and page-generation tasks
- runtime-vs-static split decisions
- tasks where SSR / prerender / static generation may or may not exist

---

## Stable Baseline

The stable sequence is:

- branch first
- inspect second
- implement third
- justify in result

This is now a reusable follow-up pattern for conditional implementation tasks.
