# Representative Concrete Row Table

Status:

- Draft v0
- Conservative initial pass
- Hotspot outcomes may change after direct file-content review

---

## Table

| asset | proposed destination | outcome category | one-line rationale | caution | compare routing reason | rule confirm / rule stress note |
|---|---|---|---|---|---|---|
| `framework/operating-model.md` | `core` | `Immediate Placement` | stable operating contract material appears to fit `core` directly without obvious mixed-responsibility pressure | verify it is normative operating contract rather than historical explanation or redesign bridge text |  | confirm: baseline stable-contract routing works cleanly |
| `framework/responsibility-matrix.md` | `core` | `Immediate Placement` | responsibility boundary documentation is a strong candidate for `core` because it behaves like durable coordination contract | check whether any rows are still tied to current legacy execution shape rather than long-lived structure |  | confirm: strongest routine `core` case in the set |
| `framework/overview.md` | `core` | `Extraction Candidate` | overview material likely contains durable core explanation but may also bundle legacy framing and redesign context, so whole-file placement would be too blunt | do not treat summary breadth as proof of clean ownership; likely mixed explanatory layers inside one file | feed `docs/compare` if the file contrasts current APSF shape with redesigned structure or migration thinking | stress: tests extraction-source handling versus wholesale placement |
| `framework/planning-patterns.md` | `docs/compare` | `Review Later` | planning-pattern guidance may contain durable guidance, but if durable guidance and current operational advice still coexist in one asset it is more honest to treat it as compare-oriented evidence first | risk of over-classifying mixed guidance as durable doctrine before separating reusable guidance from current workflow advice | compare is justified because `core` remains plausible for extracted durable guidance, while the current whole asset still appears mixed enough to require old/new structural comparison | stress: boundary between durable guidance and current-operational advice is not yet closed |
| `framework/workflow/v0.1.md` | `legacy` | `Legacy-For-Now` | versioned workflow documentation reads as current-operational shape and is more honestly preserved in `legacy` than prematurely normalized | confirm it is not partly superseded by redesign package in a way that should instead make it compare material |  | confirm: baseline current-operational routing to `legacy` |
| `framework/templates/plan.md` | `legacy` | `Legacy-For-Now` | current template asset is operational scaffolding and fits `legacy` unless separately promoted as durable canonical contract | template may contain durable sections, but whole-file promotion to `core` would likely overstate present stability |  | confirm: routine template example should not automatically become `core` |
| `framework/templates/execution-assignment.md` | `legacy` | `Legacy-For-Now` | execution-assignment template looks operational and tied to current run mechanics, so `legacy` is safer than `core` | some structural fields may later deserve extraction into a stable contract template, but whole-file `core` is premature |  | confirm/stress: routine row, but useful check against overly permissive `Immediate Placement` |
| `src/apsf/storage/run_repository.py` | `legacy` | `Hold / Review Later` | storage code for run records should remain on hold first, because plausible durable storage responsibility may exist but current code-level coupling still looks too mixed for honest immediate placement | hotspot; do not route by path alone, and do not force extraction unless persistence boundary and storage contract are shown to be separable | compare should activate only if the hold is caused by a real old-versus-new storage-boundary disagreement rather than by simple unread or uninspected detail | stress: honest hold for mixed-responsibility storage hotspot with conditional compare only |
| `src/apsf/storage/markdown_repository.py` | `core` | `Extraction Candidate` | durable Markdown handling suggests a potentially stable responsibility, but the whole file may still mix storage mechanics and current implementation detail | hotspot; verify whether Markdown repository is truly durable-record authority or partly convenience wrapper for current file layout | compare is justified if the file mixes durable Markdown authority with legacy storage assumptions that need contrast | stress: tests durable-Markdown responsibility without collapsing into path-based routing |
| `src/apsf/orchestration/phase_detector.py` | `legacy` | `Legacy-For-Now` | orchestration logic often reflects current system flow more than durable contract, so `legacy` is the safer default unless a stable sub-responsibility is explicit | hotspot; avoid upgrading to `core` simply because the concept name sounds architectural | compare later only if the file directly exposes old/new phase-model differences worth documenting | confirm/stress: good test of conceptually important but still legacy-shaped logic |
| `src/apsf/orchestration/next_instruction_builder.py` | `legacy` | `Extraction Candidate` | next-step building logic likely contains valuable orchestration concepts, but current implementation may be overfit to present run flow and need later extraction | hotspot; strong risk of mixed policy, formatting, and sequencing assumptions in one place | compare may be useful if extraction pressure comes from redesigned instruction flow versus current orchestration flow | stress: likely overfit orchestration example rather than clean placement case |
| `src/apsf/viewer/api.py` | `viewer` | `Hold / Review Later` | viewer API path makes `viewer` the leading destination, but path routing alone is insufficient if durable-record authority or compare-support responsibility is still mixed into the same asset | hotspot; must not be treated as trivially viewer-owned until durable-record and comparison responsibilities are excluded or isolated | compare is justified when the unresolved question is not simple viewer ownership, but whether viewer-support logic is entangled with durable-record authority or compare-support responsibility | stress: strongest boundary test of the do not route by path alone rule |

---

## Draft Observations

- Routine-side `Immediate Placement` is currently limited to two rows, which stays consistent with the review gates.
- `Hold / Review Later` is currently limited to hotspot cases rather than being used as a general escape hatch.
- Compare routing is present, but not attached to every uncertain row.
- Destination vocabulary remains within `core / legacy / viewer / docs/compare`.
- `experimental` is not forced into use where the evidence does not support it.

---

## Rows To Recheck First

These rows are the most likely to change after direct content review.

- `framework/planning-patterns.md`
- `src/apsf/storage/run_repository.py`
- `src/apsf/viewer/api.py`
