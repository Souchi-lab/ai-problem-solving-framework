# Cross-Repo Follow-up Pattern

## Purpose

This note records a reusable pattern for follow-ups whose design work happens in
APSF, but whose implementation happens in a different product repository.

This pattern emerged repeatedly in SoChi BLOCKS follow-ups and is now stable
enough to treat as a standard operating shape.

---

## Pattern

### 1. Close the specification in APSF

Use APSF to:

- narrow the problem
- define non-goals
- select the smallest viable approach
- write build-level implementation guidance

At this stage, APSF is used as the place to make the task legible and bounded.

### 2. Implement in the product repo

Move to the implementation repo and:

- locate the actual target file or component
- make the smallest code change that matches the APSF build
- verify with local checks, build, or direct inspection

At this stage, the product repo is used as the place where the change becomes
real.

### 3. Return measured result to APSF

Write the result back with:

- what changed
- whether the scope widened
- what was observed in actual use
- what remains outside scope
- what next trigger now exists

At this stage, APSF becomes the durable record of what the experiment actually
proved.

---

## Why This Pattern Works

This split keeps design and implementation in the repositories where they are
most natural:

- APSF is good at narrowing, framing, and handoff
- the product repo is good at local implementation and concrete verification

It also avoids two common failures:

- trying to do product implementation while the task is still ambiguous
- trying to keep execution history only in transient chat or commit messages

---

## P-Type Reading

This pattern often crosses repo boundaries while also crossing task type
boundaries:

- APSF side: often closer to `P-06 Design-only`
- product repo side: often closer to `P-01 Feature Implementation`

The important point is that the overall follow-up remains one coherent thread
even if the repositories and P-types differ.

---

## Good Use Cases

This pattern is especially good for:

- viewer UI clarification
- copy / layout / hint adjustments
- small interaction improvements
- implementation-targeted experiments that need clean scoping first

It is less useful when:

- the change is entirely inside APSF
- the implementation repo is not yet known
- the task is too large to hand off as one narrow build

---

## Minimum Artifact Shape

On the APSF side:

- `goal.md`
- `plan.md`
- `build.md`
- `result.md`

On the product side:

- local code diff
- local verification
- short implementation result

---

## Stable Baseline

The stable operating pattern is:

- APSF defines the narrow task
- the product repo executes it
- APSF records what happened

This is now a reusable follow-up shape, not a one-off workaround.
