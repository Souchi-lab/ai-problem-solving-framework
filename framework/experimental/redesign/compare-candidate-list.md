# Compare Candidate List

Source:

- derived mechanically from `representative-concrete-row-table.md`
- includes rows with a populated `compare routing reason`

---

## List

| asset | proposed destination | outcome category | compare routing reason | compare value |
|---|---|---|---|---|
| `framework/overview.md` | `core` | `Extraction Candidate` | feed `docs/compare` if the file contrasts current APSF shape with redesigned structure or migration thinking | helps explain extraction-source handling versus whole-document placement |
| `framework/planning-patterns.md` | `docs/compare` | `Review Later` | compare is justified because `core` remains plausible for extracted durable guidance, while the current whole asset still appears mixed enough to require old/new structural comparison | exposes durable-guidance-versus-operating-advice ambiguity directly |
| `src/apsf/storage/run_repository.py` | `legacy` | `Hold / Review Later` | compare should activate only if the hold is caused by a real old-versus-new storage-boundary disagreement rather than by simple unread or uninspected detail | useful only if hold persists after deeper storage-boundary review and proves to be structural rather than evidential |
| `src/apsf/storage/markdown_repository.py` | `core` | `Extraction Candidate` | compare is justified if the file mixes durable Markdown authority with legacy storage assumptions that need contrast | helps test durable-record authority versus legacy storage implementation |
| `src/apsf/orchestration/phase_detector.py` | `legacy` | `Legacy-For-Now` | compare later only if the file directly exposes old/new phase-model differences worth documenting | compare value depends on whether phase-model divergence becomes explicit |
| `src/apsf/orchestration/next_instruction_builder.py` | `legacy` | `Extraction Candidate` | compare may be useful if extraction pressure comes from redesigned instruction flow versus current orchestration flow | useful for showing orchestration overfit versus extracted instruction logic |
| `src/apsf/viewer/api.py` | `viewer` | `Hold / Review Later` | compare is justified when the unresolved question is not simple viewer ownership, but whether viewer-support logic is entangled with durable-record authority or compare-support responsibility | strongest concrete example for justified viewer-boundary comparison pressure |

---

## Current Read

- Compare candidates are concentrated in mixed-responsibility or hotspot examples.
- Compare routing is not universal, but it is already broad enough to justify later scrutiny.
- The strongest current compare candidates are:
  - `framework/planning-patterns.md`
  - `src/apsf/storage/markdown_repository.py`
  - `src/apsf/viewer/api.py`
- `framework/planning-patterns.md` currently looks like a justified compare candidate because the main ambiguity is structural, not merely editorial.
- `src/apsf/storage/run_repository.py` currently remains a conditional compare candidate and may drop out after deeper storage-boundary review if the issue turns out to be evidential rather than structural.
- `src/apsf/viewer/api.py` currently looks like a durable compare candidate because it directly tests the viewer-path versus durable-record-boundary rule.
