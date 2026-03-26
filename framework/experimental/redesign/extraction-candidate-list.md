# Extraction-Candidate List

Source:

- derived mechanically from `representative-concrete-row-table.md`
- includes rows whose outcome category is `Extraction Candidate`

---

## List

| asset | proposed destination | one-line rationale | caution | compare routing reason |
|---|---|---|---|---|
| `framework/overview.md` | `core` | overview material likely contains durable core explanation but may also bundle legacy framing and redesign context, so whole-file placement would be too blunt | do not treat summary breadth as proof of clean ownership; likely mixed explanatory layers inside one file | feed `docs/compare` if the file contrasts current APSF shape with redesigned structure or migration thinking |
| `src/apsf/storage/markdown_repository.py` | `core` | durable Markdown handling suggests a potentially stable responsibility, but the whole file may still mix storage mechanics and current implementation detail | hotspot; verify whether Markdown repository is truly durable-record authority or partly convenience wrapper for current file layout | compare is justified if the file mixes durable Markdown authority with legacy storage assumptions that need contrast |
| `src/apsf/orchestration/next_instruction_builder.py` | `legacy` | next-step building logic likely contains valuable orchestration concepts, but current implementation may be overfit to present run flow and need later extraction | hotspot; strong risk of mixed policy, formatting, and sequencing assumptions in one place | compare may be useful if extraction pressure comes from redesigned instruction flow versus current orchestration flow |

---

## Current Read

- Extraction candidates are present in both framework-doc and source-code areas.
- Two of the three current extraction candidates are hotspot code examples.
- The list currently suggests that extraction pressure is real but still selective.
- `framework/overview.md` currently looks like a justified extraction-source case rather than a direct `core` placement.
- `src/apsf/storage/markdown_repository.py` currently remains compare-worthy, but may drop out of compare later if durable-record responsibility becomes cleaner on direct review.
