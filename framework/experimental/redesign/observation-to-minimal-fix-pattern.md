# Observation-to-Minimal-Fix Pattern

## Purpose

This note records a reusable small-fix pattern that worked well in recent SoChi
BLOCKS follow-ups.

It is meant for narrow UI or layout issues that are visible in product
validation but should not be fixed by guesswork.

---

## Pattern

1. Observe

- Notice the issue during normal product validation
- Do not patch immediately if the cause is not yet clear

2. Cut a Narrow Follow-up

- Give the issue its own small follow-up
- Keep the scope local and explicit

3. State Competing Hypotheses

- Define likely cause buckets before editing
- Example: A / B / C
  - component itself
  - parent layout / spacing
  - media-query or mode-specific rule

4. Confirm the Actual Cause

- Inspect the real implementation
- Decide which hypothesis is actually true

5. Apply the Smallest Fix at the Source

- Change the rule that causes the issue
- Avoid broad redesign if the local cause is enough

6. Verify and Return the Result

- Check build or local behavior
- Record what was true, what changed, and what stayed out of scope

---

## Why It Works

This pattern prevents two common failures:

- patching by intuition before the cause is known
- widening a small issue into a larger redesign

It also creates a clean record:

- observation
- hypothesis
- confirmed cause
- minimal fix
- result

---

## Good Use Cases

- small layout gaps
- spacing imbalance
- hint / label clarity issues
- mobile-only visual glitches
- local UI polish tasks

---

## Stable Baseline

The stable operating sequence is:

- observe
- cut
- hypothesize
- confirm
- minimally fix
- record

This is now a reusable follow-up pattern, not a one-off tactic.
