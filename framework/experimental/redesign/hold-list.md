# Hold List

Source:

- derived mechanically from `representative-concrete-row-table.md`
- includes rows whose outcome category is `Hold / Review Later`

---

## List

| asset | proposed destination | one-line rationale | caution | compare routing reason |
|---|---|---|---|---|
| `src/apsf/storage/run_repository.py` | `legacy` | storage code for run records should remain on hold first, because plausible durable storage responsibility may exist but current code-level coupling still looks too mixed for honest immediate placement | hotspot; do not route by path alone, and do not force extraction unless persistence boundary and storage contract are shown to be separable | compare should activate only if the hold is caused by a real old-versus-new storage-boundary disagreement rather than by simple unread or uninspected detail |
| `src/apsf/viewer/api.py` | `viewer` | viewer API path makes `viewer` the leading destination, but path routing alone is insufficient if durable-record authority or compare-support responsibility is still mixed into the same asset | hotspot; must not be treated as trivially viewer-owned until durable-record and comparison responsibilities are excluded or isolated | compare is justified when the unresolved question is not simple viewer ownership, but whether viewer-support logic is entangled with durable-record authority or compare-support responsibility |

---

## Current Read

- `Hold / Review Later` is currently limited to hotspot rows.
- No routine asset is currently using `Hold / Review Later`.
- At this stage, hold usage looks structurally honest rather than evasive.
- `src/apsf/storage/run_repository.py` currently looks like a justified hold rather than a weak `Legacy-For-Now`, because the main unresolved issue is storage-boundary separation.
- `src/apsf/viewer/api.py` currently looks like a justified hold because the viewer-boundary question still materially includes durable-record and compare-support entanglement.
