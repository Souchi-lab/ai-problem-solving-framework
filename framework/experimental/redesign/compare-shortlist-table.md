# Compare Shortlist Table

Status:

- Draft v0
- Small, defensible shortlist
- Derived from row-execution evidence and compare-followup routing rules

---

## Table

| asset | compare strength | proposed compare routing | one-line compare reason | caution | keep out of compare unless | note |
|---|---|---|---|---|---|---|
| `framework/planning-patterns.md` | `strong` | `docs/compare` | durable guidance and current operational advice may still coexist in one asset, so structural ambiguity is more informative than whole-file placement | do not send this to compare merely because it is guidance; send it only if durable versus operational mixing remains real | direct content review shows that durable guidance separates cleanly and the ambiguity materially disappears | justified compare overlap representative |
| `src/apsf/viewer/api.py` | `strong` | `docs/compare` | viewer path is only a starting clue; if durable-record authority or compare-support responsibility is entangled, path routing alone does not close the case | do not justify compare by path name alone; compare is justified only by real boundary stress | direct content review shows viewer responsibility is clean and record / compare-support entanglement is weak | strongest boundary-stress candidate |
| `src/apsf/storage/run_repository.py` | `conditional` | `docs/compare` only if structural disagreement is confirmed | compare is useful only if a real storage-boundary disagreement remains after review; until then, hold remains the more honest primary judgment | do not send this to compare because it is unread, complex, or mixed-looking; hold comes first | direct content review shows the uncertainty is merely evidential or implementation-local rather than structural | justified hold with conditional compare |

---

## Current Read

- Strong compare candidates:
  - `framework/planning-patterns.md`
  - `src/apsf/viewer/api.py`
- Conditional compare candidate:
  - `src/apsf/storage/run_repository.py`

The shortlist currently stays small and defensible.

---

## Intended Use

This shortlist is not compare prose.

It is a routing artifact that answers:

- which assets should go to `docs/compare`
- which assets should only go conditionally
- why compare is justified in structural terms

Use this as input to a later compare-routing result or compare authoring step,
not as migration authorization.
