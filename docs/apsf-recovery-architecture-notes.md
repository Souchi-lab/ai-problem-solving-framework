# APSF Recovery Architecture Notes

---

## Summary

APSF の recovery 系は、current truth を保持したまま historical recovery record を別レイヤで扱う方向で固まった。

固定できた中核は次の 6 点。

1. execution checkpoint と file snapshot は別 artifact family
2. current truth は run root に残し、history は `recovery/` 配下に分離
3. restore / replay の前に read-only lookup と GUI surfacing を先に定義
4. file snapshot は text-first (`UTF-8`, run-relative POSIX path)
5. checkpoint / snapshot apply は explicit reason を要求する強操作
6. apply trace は `session_events.jsonl` に event として残し、GUI では read-only surfacing する

---

## Current Model

### Current Truth

- `run_state.json`
  - current execution state truth
- `artifact_manifest.json`
  - current artifact truth
- `session_events.jsonl`
  - append-only fact / trace log

### Recovery Record

- `recovery/checkpoints/<checkpoint_id>.json`
  - execution recoverability record
- `recovery/snapshots/<snapshot_id>/metadata.json`
  - file snapshot metadata
- `recovery/snapshots/<snapshot_id>/payload/<canonical_path>`
  - file snapshot payload

Recovery record は current truth の代替ではない。  
読み方は常に `current truth -> recovery candidate -> executed trace` の順にする。

---

## Execution Checkpoint

### Purpose

- file を戻すためではなく、execution state を再開候補として記録する

### Capture

- source
  - `run_state.json`
  - `session_events.jsonl`
- minimal schema
  - `checkpoint_id`
  - `run_id`
  - `phase`
  - `phase_status`
  - `current_owner`
  - `related_event_id`
  - `created_at`
  - `summary`

### Apply

- own-run only
- explicit reason required
- minimal mutation scope
  - `run_state.current_phase`
  - `run_state.phase_status`
  - `run_state.current_owner`
- must not mutate
  - `artifact_manifest.json`
  - file payload
  - `session_events.jsonl` directly

### Trace

- `checkpoint_apply_succeeded`
- `checkpoint_apply_failed`

Payload carries `checkpoint_id`, `apply_reason`, and minimal outcome/error.

---

## File Snapshot

### Purpose

- file identity/content state を restore 候補として記録する

### Capture

- text-first only
- canonical payload path
  - run-relative
  - POSIX separator `/`
  - no absolute path
  - no `.` / `..` canonical form
- canonical encoding
  - UTF-8
  - metadata `encoding: "utf-8"`
  - absent encoding is treated as UTF-8 fallback for backward compatibility

### Apply

- own-run only
- explicit reason required
- system artifact touching snapshot is blocked
- `recovery/` itself is read-only archive
- apply target is run root side only

### Trace

- `snapshot_apply_succeeded`
- `snapshot_apply_failed`

Payload carries `snapshot_id`, `apply_reason`, and `restored_paths` or `error`.

---

## GUI Reading Rule

Agent OS の Recovery 面は 3 層で読む。

1. current truth
2. recovery candidate
3. executed trace

### Recovery Candidate

- Execution Checkpoints
- File Snapshots

### Executed Trace

- Apply Trace
  - checkpoint apply success/failure
  - snapshot apply success/failure

GUI は apply を実行しない。  
selection は local read-only state に留める。

---

## Safety Rules

### Fixed

- foreign-run restore/apply is blocked
- system artifact touching snapshot restore is blocked
- mixed restore is blocked until atomicity is explicitly designed
- checkpoint/snapshot history must not overwrite the meaning of current root artifacts

### Operational Rules

- apply is always a considered operation, not silent convenience
- explicit reason is part of the safety boundary
- event append failure is warning-only and must not mask the original apply outcome

---

## What Exists Now

- dual checkpoint family spec
- storage layout spec
- restore read-only lookup spec
- Recovery GUI read-only surfacing
- snapshot capture
- snapshot apply
- execution checkpoint capture
- execution checkpoint apply
- checkpoint/snapshot apply trace in GUI

This is enough to treat recovery as a first-class APSF subsystem rather than an ad hoc restore utility.

---

## Deferred

- replay / resume engine
- checkpoint apply beyond minimal `run_state` restoration
- mixed restore/apply atomicity design
- binary snapshot payload support
- compression / deduplication
- GUI-triggered apply
- undo / rollback workflow
- trace filtering/pagination polish

---

## Next Runs

1. `checkpoint replay boundary spec`
   - define what replay can and cannot mean before any execution resume automation

2. `mixed restore atomicity spec`
   - decide when checkpoint + snapshot can be applied together and what failure semantics are acceptable

3. `recovery trace polish`
   - filter / sort / grouping for Apply Trace in Agent OS

4. `binary snapshot defer note or probe`
   - decide whether binary support stays out of scope or needs a constrained probe

---

## Handoff Notes

- If a future run touches `run_state.json`, `artifact_manifest.json`, or `session_events.jsonl`, it must preserve the distinction between current truth and recovery history.
- If a future run introduces replay, it should start from execution checkpoint semantics, not from file snapshot restore.
- If a future run introduces mixed restore, it must explicitly resolve partial-failure behavior before unblocking it.
