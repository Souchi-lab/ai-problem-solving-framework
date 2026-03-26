# Hotspot Caution List

Source:

- derived mechanically from `representative-concrete-row-table.md`
- includes rows whose caution is hotspot-sensitive or whose row is explicitly hotspot-level

---

## List

| asset | proposed destination | outcome category | caution | implication |
|---|---|---|---|---|
| `framework/overview.md` | `core` | `Extraction Candidate` | do not treat summary breadth as proof of clean ownership; likely mixed explanatory layers inside one file | treat as extraction-source evidence rather than wholesale placement proof |
| `framework/planning-patterns.md` | `docs/compare` | `Review Later` | risk of over-classifying mixed guidance as durable doctrine before separating reusable guidance from current workflow advice | keep this as a stress case for durable-guidance-versus-operating-advice separation |
| `src/apsf/storage/run_repository.py` | `legacy` | `Hold / Review Later` | hotspot; do not route by path alone, and do not force extraction unless persistence boundary and storage contract are shown to be separable | preserve hold honesty until storage boundary is clearer |
| `src/apsf/storage/markdown_repository.py` | `core` | `Extraction Candidate` | hotspot; verify whether Markdown repository is truly durable-record authority or partly convenience wrapper for current file layout | do not promote to `core` wholesale without checking for file-layout overfit |
| `src/apsf/orchestration/phase_detector.py` | `legacy` | `Legacy-For-Now` | hotspot; avoid upgrading to `core` simply because the concept name sounds architectural | keep conceptual importance separate from stable-contract proof |
| `src/apsf/orchestration/next_instruction_builder.py` | `legacy` | `Extraction Candidate` | hotspot; strong risk of mixed policy, formatting, and sequencing assumptions in one place | likely extraction-pressure case rather than clean placement |
| `src/apsf/viewer/api.py` | `viewer` | `Hold / Review Later` | hotspot; must not be treated as trivially viewer-owned until durable-record and comparison responsibilities are excluded or isolated | strongest viewer-boundary caution in the current draft |

---

## Priority Recheck

The highest-priority hotspot cautions remain:

- `framework/planning-patterns.md`
- `src/apsf/storage/run_repository.py`
- `src/apsf/viewer/api.py`

---

## Overlap Read

Current overlap interpretation:

- `framework/planning-patterns.md`
  - hotspot + compare candidate
  - currently a justified overlap because durable guidance and current operational advice appear to remain structurally mixed
- `src/apsf/storage/run_repository.py`
  - hotspot + hold + possible compare candidate
  - currently a justified overlap, but compare should remain conditional on real storage-boundary disagreement rather than mere unread detail
- `src/apsf/viewer/api.py`
  - hotspot + hold + compare candidate
  - currently the strongest justified overlap because it directly stresses path-versus-responsibility reasoning at the viewer / durable-record boundary
