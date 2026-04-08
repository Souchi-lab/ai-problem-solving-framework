# Responsibility Matrix

---

## Purpose

This document defines the canonical boundary between APSF phases, roles, and artifacts.
It exists to prevent role drift such as Builder writing Critic/Judge artifacts, and to make
`review`, `self-check`, `improve`, and `result` easier to distinguish across workflow docs,
agent docs, templates, and CLI behavior.

This file is a design-level source of truth. Operational details may still live in
`workflow/*.md`, `agents/*.md`, and templates, but they should align with this matrix.

---

## Scope

This matrix defines:

- phase purpose and stop conditions
- role ownership and forbidden outputs
- artifact ownership and meaning
- the status of `self-check`
- a document update map for follow-up runs

This matrix does not define:

- model/provider selection policy
- CLI implementation details
- child-run topology

---

## Phase Matrix

| Phase | Purpose | Required Input | Required Output | Owner | Stops When | Must Not Do |
|---|---|---|---|---|---|---|
| Goal | State the problem, background, constraints, success criteria | run intent | `goal.md` | Human / Planner | goal is specific enough for planning | decide implementation details prematurely |
| Plan | Analyze problem, compare options, choose approach, define build policy | `goal.md` | `plan.md`, optional `handoff.md`, optional `plan_review.md` when re-planning is requested | Planner | build can proceed without unresolved blockers | produce final implementation artifact |
| Build | Produce the planned design/code/document and record implementation choices | `plan.md`, optional `handoff.md`, optional `build_review.md` when re-build is requested | built artifact(s), `build.md`, optional `handoff.md` | Builder | planned build outputs exist and build record is complete | write `review.md`, `improve.md`, `result.md` |
| Review | Independently assess build quality against goal and plan | `goal.md`, `build.md`, built artifact(s), optional `handoff.md` | `review.md`, optional `handoff.md` | Critic | risks/findings are recorded with severity | rewrite the build instead of reviewing it |
| Improve | Decide whether to iterate or accept, based on review | `review.md`, optional `improve_review.md` when re-improve is requested | `improve.md` or direct accept decision | Judge | next action is explicitly chosen | silently skip unresolved critical concerns |
| Result | Record final accepted outcome and reusable lessons | `improve.md`, accepted state of artifacts | `result.md` | Judge / Human | run is closed and reusable takeaways are captured | replace review history |
| Verify | Optional validation phase when runtime/test/proof is needed | build output + verification target | verification notes or updated `build.md`/run record | Assigned verifier | validation result is explicit | become a hidden substitute for Review |

---

## Role Matrix

| Role | Primary Responsibility | Creates | Reads | Must Not Create |
|---|---|---|---|---|
| Planner | clarify problem, choose approach, define build boundary | `goal.md` support, `plan.md`, optional initial `handoff.md` | goal, framework references, prior notes, optional `plan_review.md` | final build artifact, `review.md`, `improve.md`, `result.md` |
| JuniorBuilder | optional delegated pre-build support | scoped helper outputs only when explicitly assigned | plan/handoff | canonical build artifact unless explicitly delegated |
| Builder | execute the selected approach and document what was built | planned artifact(s), `build.md`, optional `handoff.md` when transfer context is needed | `plan.md`, optional `handoff.md`, referenced source docs | `review.md`, `improve.md`, `result.md` |
| Critic | independent review from a different model/persona/tooling path | `review.md`, optional `handoff.md` when downstream transfer context is needed | goal, build, built artifact(s), optional handoff | build artifact rewrite, `improve.md`, `result.md` |
| Judge | decide iterate vs accept and record final disposition | `improve.md`, `result.md` | review, build, goal, handoff | silent acceptance without explicit decision trail |
| Human | may serve as Planner, Critic, or Judge; owns final governance | any artifact when explicitly acting in that role | all relevant run context | bypass role boundaries without recording the role shift |

---

## Artifact Matrix

| Artifact | Meaning | Canonical Writer | Used By | Notes |
|---|---|---|---|---|
| `goal.md` | problem framing and success criteria | Planner / Human | all later phases | defines what success means |
| `plan.md` | selected approach and execution policy | Planner | Builder, Critic, Judge | must include build boundary |
| `plan_review.md` | optional structured revision note for re-planning | Human / Critic / reviewer requesting re-plan | Planner, Human | official supporting artifact for plan iteration; does not replace `plan.md` |
| `build_review.md` | optional structured revision note for re-build | Human / Critic / reviewer requesting re-build | Builder, Human | official supporting artifact for build iteration; does not replace `build.md` |
| `review_review.md` | optional structured revision note for re-review | Human / Critic / reviewer requesting re-review | Critic, Human | official supporting artifact for review iteration; does not replace `review.md` |
| `improve_review.md` | optional structured revision note for re-improve | Human / Judge / reviewer requesting re-improve | Judge, Human | official supporting artifact for improve iteration; does not replace `improve.md` |
| `handoff.md` | conditional transfer note between roles | current role handing off | next role | use when canonical artifacts do not fully carry transfer context |
| `build.md` | record of what Builder produced, decisions, deviations, open issues | Builder | Critic, Judge | mandatory when Build occurs |
| `review.md` | independent evaluation of build quality and risks | Critic | Judge | findings-first artifact |
| `improve.md` | explicit accept / iterate decision and required changes | Judge | next iteration or Result | bridge between review and closure |
| `result.md` | final accepted outcome and reusable lessons | Judge / Human | future runs | closes the run |
| `force_audit.json` | per-run audit trail for `--force` overrides | tooling / command path invoking the override | Human, Builder, future tooling / GUI | canonical record of override fact and reason-presence; not a phase artifact |
| `transcript.md` | optional compiled record of the full run | Human / tooling | future reference | convenience artifact, not canonical decision source |

---

## `self-check` Definition

`self-check` is not a first-class APSF phase.

It is a Builder-internal quality step performed before handing work to Critic. It may be
captured in one of these ways:

- summarized inside `build.md`
- recorded in a builder-local note such as `self-check.md` when a run explicitly asks for it

Rules:

- `self-check` never replaces `review.md`
- `self-check` is not independent review
- `self-check` does not authorize Builder to write Critic/Judge artifacts
- if `self-check.md` exists, it is supporting evidence, not the canonical review record

Operational interpretation:

- Build phase may include self-check activity
- Review phase begins only when Critic starts independent assessment

---

## Boundary Rules

1. One phase has one canonical primary output.
2. One role may write multiple artifacts only when they belong to that role's phase boundary.
3. Builder stops at build outputs plus optional build-side handoff when transfer context is needed.
4. Critic reviews; Critic does not silently fix.
5. Judge decides; Judge does not erase review history.
6. `handoff.md` carries context, but never replaces `plan.md`, `build.md`, or `review.md`.
7. Optional artifacts must be explicitly marked optional in the governing template or run plan.
8. `plan_review.md` may request a revised plan, but it does not become the canonical plan artifact.
9. `build_review.md` may request a revised build, but it does not become the canonical build artifact.
10. `review_review.md` may request a revised review, but it does not become the canonical review artifact.
11. `improve_review.md` may request a revised Judge decision, but it does not become the canonical improve artifact.

---

## Run-021 Failure Pattern This Matrix Prevents

Observed failure pattern:

- Builder wrote `review.md`, `improve.md`, and `result.md`
- `self-check` and `review` became indistinguishable in practice
- role separation described in framework docs was not enforced by the run record

This matrix resolves that by making the following explicit:

- `self-check` is internal to Build, not a phase-level substitute for Review
- `review.md` belongs to Critic
- `improve.md` and `result.md` belong to Judge / Human governance
- `build.md` must carry the canonical build record, and `handoff.md` may add only the transfer context that canonical files do not already carry

---

## Follow-up Update Map

This run establishes the canonical boundary doc. Follow-up runs should align the rest of the framework to it.

### Highest Priority

- `framework/workflow/v0.1.md`
  - align phase descriptions with this matrix
  - explicitly state that `self-check` is builder-internal, not a canonical phase
- `framework/workflow/v0.2.md`
  - align optional `verify` semantics and role boundaries
- `framework/agents/builder.md`
  - reinforce build stop conditions and forbidden outputs
- `framework/agents/critic.md`
  - reinforce independent review and non-fixing boundary
- `framework/agents/judge.md`
  - reinforce accept/iterate governance role

### Next Priority

- `framework/templates/plan.md`
  - keep `Build / Execute Policy` as the place where run-specific stop conditions are stated
- `framework/templates/build.md`
  - make self-check summary expectations explicit when useful
- `framework/templates/handoff.md`
  - make next-role review targets explicit

### CLI / Guard Follow-up

- `apsf act`
  - warn when the acting role attempts to write a forbidden phase artifact
- `apsf write-phase`
  - require or infer role-consistent destination files
- `execution-assignment.md` generation
  - make next-role and forbidden outputs clearer at run start

---

## Decision Summary

The APSF model should be interpreted as:

- phases define purpose and stop conditions
- roles define who may write which canonical artifacts
- artifacts define the durable record
- `self-check` is supporting build activity, not a replacement for independent review

When these three axes disagree, future framework work should align them back to this matrix.
