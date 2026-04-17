import type { AgentOSInfo } from '../../types'
import { formatAgentOSTimestamp } from '../../utils/formatting'

interface RecoverySectionProps {
  agentOSData: AgentOSInfo
  selectedRecoveryCheckpointId: string | null
  setSelectedRecoveryCheckpointId: (id: string | null) => void
  selectedRecoverySnapshotId: string | null
  setSelectedRecoverySnapshotId: (id: string | null) => void
  selectedRecoveryApplyTraceId: string | null
  setSelectedRecoveryApplyTraceId: (id: string | null) => void
}

export function RecoverySection({
  agentOSData,
  selectedRecoveryCheckpointId,
  setSelectedRecoveryCheckpointId,
  selectedRecoverySnapshotId,
  setSelectedRecoverySnapshotId,
  selectedRecoveryApplyTraceId,
  setSelectedRecoveryApplyTraceId,
}: RecoverySectionProps) {
  return (
    <div className="rounded border border-cyan-500/20 bg-cyan-500/5 p-4">
      <div className="mb-1 text-[11px] font-bold uppercase tracking-[0.2em] text-cyan-300">Recovery</div>
      <div className="mb-4 text-[10px] text-zinc-500">
        Historical recovery candidates are shown below current truth. Selection is read-only and does not trigger restore.
      </div>

      <div className="grid gap-4 xl:grid-cols-3">
        <div className="rounded border border-zinc-800 bg-black/20 p-3">
          <div className="mb-2 text-[10px] font-bold uppercase tracking-[0.2em] text-zinc-400">Execution Checkpoints</div>
          {agentOSData.recovery_checkpoints.length > 0 ? (
            <div className="space-y-2">
              <div className="space-y-1">
                {agentOSData.recovery_checkpoints.map((checkpoint) => {
                  const selected = selectedRecoveryCheckpointId === checkpoint.checkpoint_id
                  return (
                    <button
                      key={checkpoint.checkpoint_id}
                      type="button"
                      onClick={() => setSelectedRecoveryCheckpointId(checkpoint.checkpoint_id)}
                      className={`w-full rounded border px-3 py-2 text-left text-[10px] transition-colors ${
                        selected
                          ? 'border-cyan-400/50 bg-cyan-500/10 text-cyan-100'
                          : 'border-zinc-800 bg-zinc-950/40 text-zinc-300 hover:border-zinc-700 hover:bg-zinc-900/50'
                      }`}
                    >
                      <div className="flex items-center justify-between gap-3">
                        <span className="font-mono font-semibold">{checkpoint.checkpoint_id}</span>
                        {selected && <span className="rounded bg-cyan-500/15 px-1.5 py-0.5 text-[9px] font-bold text-cyan-300">Selected Candidate</span>}
                      </div>
                      <div className="mt-1 flex flex-wrap gap-x-3 gap-y-1 text-[9px] text-zinc-500">
                        <span>Phase: {checkpoint.phase || '—'}</span>
                        <span>Status: {checkpoint.phase_status || '—'}</span>
                        <span>{formatAgentOSTimestamp(checkpoint.created_at)}</span>
                      </div>
                    </button>
                  )
                })}
              </div>
              {(() => {
                const selectedCheckpoint =
                  agentOSData.recovery_checkpoints.find((item) => item.checkpoint_id === selectedRecoveryCheckpointId) ?? null
                if (!selectedCheckpoint) {
                  return (
                    <div className="rounded border border-dashed border-zinc-800 p-3 text-center text-[10px] text-zinc-600">
                      Select a checkpoint to inspect metadata.
                    </div>
                  )
                }
                return (
                  <div className="rounded border border-cyan-500/15 bg-cyan-500/5 p-3 text-[10px]">
                    <div className="mb-2 text-[10px] font-bold uppercase tracking-[0.2em] text-cyan-300">Inspect</div>
                    <div className="grid gap-2">
                      <div><span className="text-zinc-500">Checkpoint ID:</span> <span className="font-mono text-zinc-200">{selectedCheckpoint.checkpoint_id}</span></div>
                      <div><span className="text-zinc-500">Phase:</span> <span className="text-zinc-200">{selectedCheckpoint.phase || '—'}</span></div>
                      <div><span className="text-zinc-500">Phase Status:</span> <span className="text-zinc-200">{selectedCheckpoint.phase_status || '—'}</span></div>
                      <div><span className="text-zinc-500">Created:</span> <span className="text-zinc-200">{formatAgentOSTimestamp(selectedCheckpoint.created_at)}</span></div>
                      <div><span className="text-zinc-500">Related Event:</span> <span className="font-mono text-zinc-300">{selectedCheckpoint.related_event_id || '—'}</span></div>
                      <div><span className="text-zinc-500">Summary:</span> <span className="text-zinc-300">{selectedCheckpoint.summary || 'No summary recorded.'}</span></div>
                    </div>
                  </div>
                )
              })()}
            </div>
          ) : (
            <div className="rounded border border-dashed border-zinc-800 p-3 text-center text-[10px] text-zinc-600">
              No execution checkpoints recorded yet.
            </div>
          )}
        </div>

        <div className="rounded border border-zinc-800 bg-black/20 p-3">
          <div className="mb-2 text-[10px] font-bold uppercase tracking-[0.2em] text-zinc-400">File Snapshots</div>
          {agentOSData.recovery_snapshots.length > 0 ? (
            <div className="space-y-2">
              <div className="space-y-1">
                {agentOSData.recovery_snapshots.map((snapshot) => {
                  const selected = selectedRecoverySnapshotId === snapshot.snapshot_id
                  return (
                    <button
                      key={snapshot.snapshot_id}
                      type="button"
                      onClick={() => setSelectedRecoverySnapshotId(snapshot.snapshot_id)}
                      className={`w-full rounded border px-3 py-2 text-left text-[10px] transition-colors ${
                        selected
                          ? 'border-cyan-400/50 bg-cyan-500/10 text-cyan-100'
                          : 'border-zinc-800 bg-zinc-950/40 text-zinc-300 hover:border-zinc-700 hover:bg-zinc-900/50'
                      }`}
                    >
                      <div className="flex items-center justify-between gap-3">
                        <span className="font-mono font-semibold">{snapshot.snapshot_id}</span>
                        {selected && <span className="rounded bg-cyan-500/15 px-1.5 py-0.5 text-[9px] font-bold text-cyan-300">Selected Candidate</span>}
                      </div>
                      <div className="mt-1 flex flex-wrap gap-x-3 gap-y-1 text-[9px] text-zinc-500">
                        <span>Phase: {snapshot.source_phase || '—'}</span>
                        <span>Files: {snapshot.file_count}</span>
                        <span>{formatAgentOSTimestamp(snapshot.captured_at)}</span>
                      </div>
                    </button>
                  )
                })}
              </div>
              {(() => {
                const selectedSnapshot =
                  agentOSData.recovery_snapshots.find((item) => item.snapshot_id === selectedRecoverySnapshotId) ?? null
                if (!selectedSnapshot) {
                  return (
                    <div className="rounded border border-dashed border-zinc-800 p-3 text-center text-[10px] text-zinc-600">
                      Select a snapshot to inspect metadata.
                    </div>
                  )
                }
                return (
                  <div className="rounded border border-cyan-500/15 bg-cyan-500/5 p-3 text-[10px]">
                    <div className="mb-2 text-[10px] font-bold uppercase tracking-[0.2em] text-cyan-300">Inspect</div>
                    <div className="grid gap-2">
                      <div><span className="text-zinc-500">Snapshot ID:</span> <span className="font-mono text-zinc-200">{selectedSnapshot.snapshot_id}</span></div>
                      <div><span className="text-zinc-500">Source Phase:</span> <span className="text-zinc-200">{selectedSnapshot.source_phase || '—'}</span></div>
                      <div><span className="text-zinc-500">Captured:</span> <span className="text-zinc-200">{formatAgentOSTimestamp(selectedSnapshot.captured_at)}</span></div>
                      <div><span className="text-zinc-500">File Count:</span> <span className="text-zinc-200">{selectedSnapshot.file_count}</span></div>
                      <div>
                        <div className="text-zinc-500">Target Paths</div>
                        <div className="mt-1 space-y-1">
                          {selectedSnapshot.target_paths.length > 0 ? selectedSnapshot.target_paths.slice(0, 5).map((path) => (
                            <div key={path} className="rounded bg-black/20 px-2 py-1 font-mono text-[9px] text-zinc-300">{path}</div>
                          )) : <div className="text-zinc-600">No target paths recorded.</div>}
                        </div>
                      </div>
                    </div>
                  </div>
                )
              })()}
            </div>
          ) : (
            <div className="rounded border border-dashed border-zinc-800 p-3 text-center text-[10px] text-zinc-600">
              No file snapshots recorded yet.
            </div>
          )}
        </div>

        <div className="rounded border border-zinc-800 bg-black/20 p-3">
          <div className="mb-2 text-[10px] font-bold uppercase tracking-[0.2em] text-zinc-400">Apply Trace</div>
          {agentOSData.recovery_apply_traces.length > 0 ? (
            <div className="space-y-2">
              <div className="space-y-1">
                {agentOSData.recovery_apply_traces.map((trace) => {
                  const selected = selectedRecoveryApplyTraceId === trace.event_id
                  const statusClasses =
                    trace.status === 'success'
                      ? 'border-emerald-500/30 bg-emerald-500/10 text-emerald-200'
                      : 'border-rose-500/30 bg-rose-500/10 text-rose-200'
                  return (
                    <button
                      key={trace.event_id}
                      type="button"
                      onClick={() => setSelectedRecoveryApplyTraceId(trace.event_id)}
                      className={`w-full rounded border px-3 py-2 text-left text-[10px] transition-colors ${
                        selected
                          ? 'border-cyan-400/50 bg-cyan-500/10 text-cyan-100'
                          : 'border-zinc-800 bg-zinc-950/40 text-zinc-300 hover:border-zinc-700 hover:bg-zinc-900/50'
                      }`}
                    >
                      <div className="flex items-center justify-between gap-3">
                        <span className="font-mono font-semibold">{trace.target_kind}:{trace.target_id}</span>
                        <span className={`rounded border px-1.5 py-0.5 text-[9px] font-bold uppercase ${statusClasses}`}>
                          {trace.status}
                        </span>
                      </div>
                      <div className="mt-1 flex flex-wrap gap-x-3 gap-y-1 text-[9px] text-zinc-500">
                        <span>{trace.event_type}</span>
                        <span>{formatAgentOSTimestamp(trace.timestamp)}</span>
                      </div>
                    </button>
                  )
                })}
              </div>
              {(() => {
                const selectedTrace =
                  agentOSData.recovery_apply_traces.find((item) => item.event_id === selectedRecoveryApplyTraceId) ?? null
                if (!selectedTrace) {
                  return (
                    <div className="rounded border border-dashed border-zinc-800 p-3 text-center text-[10px] text-zinc-600">
                      Select an apply trace to inspect outcome metadata.
                    </div>
                  )
                }
                return (
                  <div className="rounded border border-cyan-500/15 bg-cyan-500/5 p-3 text-[10px]">
                    <div className="mb-2 text-[10px] font-bold uppercase tracking-[0.2em] text-cyan-300">Inspect</div>
                    <div className="grid gap-2">
                      <div><span className="text-zinc-500">Target:</span> <span className="font-mono text-zinc-200">{selectedTrace.target_kind}:{selectedTrace.target_id}</span></div>
                      <div><span className="text-zinc-500">Status:</span> <span className="text-zinc-200">{selectedTrace.status}</span></div>
                      <div><span className="text-zinc-500">Event Type:</span> <span className="font-mono text-zinc-300">{selectedTrace.event_type}</span></div>
                      <div><span className="text-zinc-500">Timestamp:</span> <span className="text-zinc-200">{formatAgentOSTimestamp(selectedTrace.timestamp)}</span></div>
                      <div><span className="text-zinc-500">Reason:</span> <span className="text-zinc-300">{selectedTrace.reason || 'No reason recorded.'}</span></div>
                      <div><span className="text-zinc-500">Outcome:</span> <span className="text-zinc-300">{selectedTrace.outcome_summary || 'No outcome summary recorded.'}</span></div>
                    </div>
                  </div>
                )
              })()}
            </div>
          ) : (
            <div className="rounded border border-dashed border-zinc-800 p-3 text-center text-[10px] text-zinc-600">
              No apply trace recorded yet.
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
