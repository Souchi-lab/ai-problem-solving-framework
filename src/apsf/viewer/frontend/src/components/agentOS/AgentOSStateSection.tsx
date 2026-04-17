import type { AgentOSInfo } from '../../types'
import { getArtifactDisplayMeta } from '../../utils/artifacts'

interface AgentOSStateSectionProps {
  agentOSData: AgentOSInfo
  openArtifactReferenceModal: (preferredArtifact?: string) => void
}

export function AgentOSStateSection({ agentOSData, openArtifactReferenceModal }: AgentOSStateSectionProps) {
  const failingGateResults = agentOSData.gate_results?.filter((gate) => !gate.passed) ?? []
  return (
    <>
      {!agentOSData.run_state && agentOSData.gate_results.length === 0 && !agentOSData.artifact_manifest && (
        <div className="rounded border border-dashed border-zinc-700 bg-zinc-900/30 p-5 text-center">
          <div className="text-xs font-semibold text-zinc-400">Agent OS state not initialized</div>
          <div className="mt-1 text-[11px] text-zinc-600">This run pre-dates the state-first workflow, or <code className="font-mono">apsf act</code> has not been called yet.</div>
          <div className="mt-2 text-[10px] text-zinc-700">Expected: <code className="font-mono">run_state.json</code> / <code className="font-mono">artifact_manifest.json</code></div>
        </div>
      )}

      {agentOSData.run_state ? (
        <div className="rounded border border-zinc-800 bg-zinc-900/40 p-4">
          <div className="mb-3 text-[11px] font-bold uppercase tracking-[0.2em] text-zinc-500">Run State</div>
          <div className="grid grid-cols-2 gap-x-4 gap-y-2 text-xs">
            <div>
              <div className="text-[10px] text-zinc-600 uppercase tracking-wide">Phase</div>
              <div className="mt-0.5 font-semibold text-zinc-100">{agentOSData.run_state.current_phase}</div>
            </div>
            <div>
              <div className="text-[10px] text-zinc-600 uppercase tracking-wide">Status</div>
              <div className={`mt-0.5 font-semibold ${agentOSData.run_state.phase_status === 'failed' ? 'text-red-300' : agentOSData.run_state.phase_status === 'in_progress' ? 'text-amber-300' : 'text-emerald-300'}`}>
                {agentOSData.run_state.phase_status}
              </div>
            </div>
            <div>
              <div className="text-[10px] text-zinc-600 uppercase tracking-wide">Owner</div>
              <div className="mt-0.5 text-zinc-200">{agentOSData.run_state.current_owner || '—'}</div>
            </div>
            <div>
              <div className="text-[10px] text-zinc-600 uppercase tracking-wide">Retry Count</div>
              <div className={`mt-0.5 ${agentOSData.run_state.retry_count > 0 ? 'text-amber-300' : 'text-zinc-400'}`}>
                {agentOSData.run_state.retry_count}
              </div>
            </div>
            {agentOSData.run_state.active_handoff_id && (
              <div className="col-span-2">
                <div className="text-[10px] text-zinc-600 uppercase tracking-wide">Active Handoff</div>
                <div className="mt-0.5 font-mono text-[10px] text-zinc-400">{agentOSData.run_state.active_handoff_id}</div>
              </div>
            )}
            {agentOSData.run_state.last_error && (
              <div className="col-span-2">
                <div className="text-[10px] text-zinc-600 uppercase tracking-wide">Last Error</div>
                <div className="mt-0.5 rounded bg-red-950/30 px-2 py-1 font-mono text-[10px] text-red-300">{agentOSData.run_state.last_error}</div>
              </div>
            )}
            {agentOSData.run_state.gate_failures.length > 0 && (
              <div className="col-span-2">
                <div className="text-[10px] text-zinc-600 uppercase tracking-wide">Gate Failures</div>
                <div className="mt-1 space-y-1">
                  {agentOSData.run_state.gate_failures.map((f, i) => (
                    <div key={i} className="rounded bg-red-950/20 px-2 py-1 text-[10px] text-red-300">{f}</div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      ) : agentOSData.gate_results.length > 0 || agentOSData.artifact_manifest ? (
        <div className="rounded border border-dashed border-zinc-800 p-3 text-center text-[11px] text-zinc-600">run_state.json not yet created</div>
      ) : null}

      {failingGateResults.length > 0 && (
        <div className="rounded border border-zinc-800 bg-zinc-900/40 p-4">
          <div className="mb-3 text-[11px] font-bold uppercase tracking-[0.2em] text-zinc-500">Gate Results</div>
          <div className="space-y-2">
            {failingGateResults.map((g, i) => (
              <div key={i} className="flex items-start gap-3 rounded border border-red-500/20 bg-red-500/5 px-3 py-2 text-xs">
                <div className="mt-0.5 h-2 w-2 shrink-0 rounded-full bg-red-400" />
                <div className="min-w-0">
                  <div className="font-semibold text-red-200">{g.gate_type}</div>
                  {g.reason && <div className="mt-0.5 text-[10px] text-zinc-400">{g.reason}</div>}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {agentOSData.artifact_manifest && agentOSData.artifact_manifest.length > 0 && (
        <div className="rounded border border-zinc-800 bg-zinc-900/40 p-4">
          <div className="mb-3 text-[11px] font-bold uppercase tracking-[0.2em] text-zinc-500">Artifact Manifest</div>
          <div className="overflow-x-auto">
            <table className="w-full text-[10px]">
              <thead>
                <tr className="border-b border-zinc-800 text-left text-zinc-600">
                  <th className="pb-1.5 pr-3 font-semibold uppercase tracking-wide">Artifact</th>
                  <th className="pb-1.5 pr-3 font-semibold uppercase tracking-wide">Written By</th>
                  <th className="pb-1.5 pr-3 font-semibold uppercase tracking-wide">Status</th>
                  <th className="pb-1.5 pr-3 font-semibold uppercase tracking-wide">Rev</th>
                  <th className="pb-1.5 font-semibold uppercase tracking-wide">Updated</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-800/50">
                {agentOSData.artifact_manifest.map((e) => (
                  <tr key={e.artifact_name} className="text-zinc-300">
                    <td className="py-1.5 pr-3">
                      <button
                        type="button"
                        onClick={() => openArtifactReferenceModal(e.artifact_name)}
                        className="text-left"
                      >
                        <div className="font-semibold text-zinc-100 hover:text-white">{getArtifactDisplayMeta(e.artifact_name).title}</div>
                        <div className="font-mono text-[10px] text-zinc-500">{e.artifact_name}</div>
                      </button>
                    </td>
                    <td className="py-1.5 pr-3 text-zinc-400">{e.written_by || '—'}</td>
                    <td className="py-1.5 pr-3">
                      <span className={`rounded px-1.5 py-0.5 font-semibold ${e.status === 'generated' ? 'bg-blue-500/15 text-blue-300' : 'bg-zinc-700/50 text-zinc-400'}`}>
                        {e.status}
                      </span>
                    </td>
                    <td className="py-1.5 pr-3 text-zinc-500">r{e.revision}</td>
                    <td className="py-1.5 font-mono text-zinc-500">{e.updated_at.slice(0, 16).replace('T', ' ')}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {agentOSData.force_audit && agentOSData.force_audit.length > 0 && (
        <div className="rounded border border-amber-500/20 bg-amber-500/5 p-4">
          <div className="mb-3 text-[11px] font-bold uppercase tracking-[0.2em] text-amber-400">Force Audit</div>
          <div className="space-y-2">
            {agentOSData.force_audit.map((e, i) => (
              <div key={i} className="rounded border border-amber-500/15 bg-black/20 px-3 py-2 text-[10px]">
                <div className="flex items-center gap-2">
                  <span className="font-semibold text-amber-200">{e.override_kind}</span>
                  <span className="text-zinc-500">|</span>
                  <span className="font-mono text-zinc-300">{e.target_file}</span>
                  <span className="text-zinc-500">|</span>
                  <span className="text-zinc-400">{e.command}</span>
                  {!e.had_reason && (
                    <span className="rounded bg-red-500/20 px-1.5 py-0.5 font-bold text-red-300">no reason</span>
                  )}
                </div>
                {e.reason && <div className="mt-1 text-zinc-400">Reason: {e.reason}</div>}
                <div className="mt-1 font-mono text-zinc-600">{e.timestamp.slice(0, 19).replace('T', ' ')} UTC</div>
              </div>
            ))}
          </div>
        </div>
      )}
    </>
  )
}
