import type { RallyMessage } from '../../types'
import { extractSummaryLine } from '../../utils/formatting'

export function RallyConversationModal({
  runName,
  messages,
  loading,
  onClose,
  autoLoopRunning,
  stopPending,
  currentOwner,
  elapsedDisplay,
  specialistCodes,
}: {
  runName: string
  messages: RallyMessage[]
  loading: boolean
  onClose: () => void
  autoLoopRunning: boolean
  stopPending: boolean
  currentOwner: string
  elapsedDisplay: string | null
  specialistCodes: { planner: string; builder: string; critic: string }
}) {
  // Determine the active artifact from currentOwner so the running indicator
  // tracks the CURRENT PHASE, not merely the first missing artifact.
  // When a role reruns (e.g. build rerun creates build_rerun_*.md that is not
  // in the list), we fall back to the last artifact authored by that role.
  const activeArtifact = (() => {
    if (!autoLoopRunning) return null
    // Map currentOwner → speaker name used in messages
    const ownerSpeaker =
      currentOwner === 'Planner' ? 'Planner'
      : currentOwner === 'Builder' ? 'Builder'
      : currentOwner === 'Critic' ? 'Critic'
      : null
    if (ownerSpeaker) {
      // Prefer: first missing artifact for this owner
      const missing = messages.find((m) => m.speaker === ownerSpeaker && !m.exists)
      if (missing) return missing.artifact
      // Rerun fallback: all owner artifacts exist → highlight the last one
      const ownerMsgs = messages.filter((m) => m.speaker === ownerSpeaker)
      if (ownerMsgs.length > 0) return ownerMsgs[ownerMsgs.length - 1].artifact
    }
    // Final fallback
    return messages.find((m) => !m.exists)?.artifact ?? null
  })()

  // Specialist code for a given artifact name
  const codeForArtifact = (artifact: string) => {
    if (artifact === 'plan.md') return specialistCodes.planner
    if (artifact === 'build.md') return specialistCodes.builder
    if (artifact === 'review.md') return specialistCodes.critic
    return ''
  }

  // Current worker specialist code (always derived from currentOwner from run_state)
  const currentWorkerCode =
    currentOwner === 'Planner' ? specialistCodes.planner
    : currentOwner === 'Builder' ? specialistCodes.builder
    : currentOwner === 'Critic' ? specialistCodes.critic
    : ''

  // Session summary: first meaningful line from each existing artifact
  const sessionSummary = !autoLoopRunning
    ? messages
        .filter((m) => m.exists)
        .map((m) => ({ artifact: m.artifact, line: extractSummaryLine(m.content) }))
        .filter((s) => s.line !== '')
    : []

  return (
    <div className="fixed inset-0 z-[110] flex items-center justify-center bg-black/70 p-4 backdrop-blur-sm" onClick={onClose}>
      <div className="flex max-h-[88vh] w-full max-w-xl flex-col overflow-hidden rounded-2xl border border-zinc-800 bg-zinc-950 shadow-2xl shadow-black/60" onClick={(e) => e.stopPropagation()}>

        {/* ── Header ─────────────────────────────────────────────────── */}
        <div className="flex items-start justify-between gap-3 border-b border-zinc-800 px-5 py-4">
          <div className="min-w-0 flex-1">
            {/* Title + running/stopped badge */}
            <div className="flex items-center gap-2.5">
              <span className="text-base font-bold text-zinc-100">Rally</span>
              {autoLoopRunning ? (
                <span className="flex items-center gap-1.5 rounded border border-emerald-500/30 bg-emerald-500/10 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wide text-emerald-300">
                  <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-emerald-400" />
                  {stopPending ? 'Stop Pending' : 'Running'}
                </span>
              ) : (
                <span className="rounded border border-zinc-700 bg-zinc-900 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wide text-zinc-500">
                  Stopped
                </span>
              )}
            </div>
            {/* Run name */}
            <div className="mt-1 truncate font-mono text-[10px] text-zinc-500">{runName}</div>
            {/* Worker + specialist code + elapsed */}
            {(currentOwner || elapsedDisplay) && (
              <div className="mt-2 flex flex-wrap items-center gap-3 text-[10px]">
                {currentOwner && (
                  <span className="flex items-center gap-1.5 text-zinc-400">
                    <span className="text-zinc-600">Worker</span>
                    <span className="font-semibold text-zinc-200">{currentOwner}</span>
                    {currentWorkerCode && (
                      <span className="rounded border border-zinc-700 bg-zinc-900 px-1.5 py-0.5 font-mono text-zinc-300">{currentWorkerCode}</span>
                    )}
                  </span>
                )}
                {elapsedDisplay && (
                  <span className="flex items-center gap-1 text-zinc-400">
                    <span className="text-zinc-600">Elapsed</span>
                    <span className="font-mono font-semibold text-zinc-200">{elapsedDisplay}</span>
                  </span>
                )}
              </div>
            )}
          </div>
          <button onClick={onClose} className="flex-shrink-0 rounded border border-zinc-700 bg-zinc-900 px-3 py-1.5 text-xs font-semibold text-zinc-300 hover:border-zinc-500 hover:text-white">
            Close
          </button>
        </div>

        {/* ── Artifact timeline ───────────────────────────────────────── */}
        <div className="min-h-0 flex-1 overflow-y-auto px-4 py-4">
          {loading ? (
            <div className="rounded border border-zinc-800 bg-black/20 p-4 text-sm text-zinc-400">Loading rally...</div>
          ) : messages.length === 0 ? (
            <div className="rounded border border-zinc-800 bg-black/20 p-4 text-sm text-zinc-400">No artifacts yet.</div>
          ) : (
            <>
              <div className="space-y-0.5">
                {messages.map((msg, idx) => {
                  const isActive = msg.artifact === activeArtifact
                  const code = codeForArtifact(msg.artifact)
                  const speakerInitial =
                    msg.speaker === 'Builder' ? 'B'
                    : msg.speaker === 'Critic' ? 'C'
                    : msg.speaker === 'Judge' ? 'J'
                    : 'R'
                  const badgeClass =
                    msg.speaker === 'Builder'
                      ? 'border-cyan-500/40 bg-cyan-500/10 text-cyan-200'
                      : msg.speaker === 'Critic'
                        ? 'border-amber-500/40 bg-amber-500/10 text-amber-200'
                        : msg.speaker === 'Judge'
                          ? 'border-fuchsia-500/40 bg-fuchsia-500/10 text-fuchsia-200'
                          : 'border-emerald-500/40 bg-emerald-500/10 text-emerald-200'
                  return (
                    <div
                      key={`${msg.artifact}-${idx}`}
                      className={`flex items-center gap-2.5 rounded px-2.5 py-2 text-[11px] transition-colors ${
                        isActive ? 'bg-cyan-500/5 ring-1 ring-inset ring-cyan-500/20' : !msg.exists ? 'opacity-35' : ''
                      }`}
                    >
                      {/* Speaker badge */}
                      <span className={`flex-shrink-0 rounded border px-1.5 py-0.5 text-[9px] font-bold ${badgeClass}`}>{speakerInitial}</span>
                      {/* Artifact name */}
                      <span className="flex-1 font-mono text-zinc-300">{msg.artifact}</span>
                      {/* Specialist code */}
                      {code && (
                        <span className="flex-shrink-0 rounded border border-zinc-700 bg-zinc-900 px-1.5 py-0.5 font-mono text-[9px] text-zinc-500">{code}</span>
                      )}
                      {/* Status indicator */}
                      {isActive ? (
                        <span className="flex flex-shrink-0 items-end gap-[3px] pb-0.5">
                          {[0, 150, 300].map((delay) => (
                            <span
                              key={delay}
                              className="block h-1.5 w-1.5 animate-bounce rounded-full bg-cyan-400"
                              style={{ animationDelay: `${delay}ms` }}
                            />
                          ))}
                        </span>
                      ) : msg.exists ? (
                        <span className="flex-shrink-0 text-[10px] text-emerald-400">✓</span>
                      ) : (
                        <span className="flex-shrink-0 text-[10px] text-zinc-700">○</span>
                      )}
                    </div>
                  )
                })}
              </div>

              {/* ── Session summary (shown when stopped) ──────────────── */}
              {!autoLoopRunning && sessionSummary.length > 0 && (
                <div className="mt-5 rounded border border-zinc-800 bg-black/30 px-4 py-3">
                  <div className="mb-2.5 text-[9px] font-bold uppercase tracking-[0.2em] text-zinc-500">Session Summary</div>
                  <div className="space-y-2">
                    {sessionSummary.map(({ artifact, line }) => (
                      <div key={artifact} className="flex gap-2 text-[11px]">
                        <span className="flex-shrink-0 font-mono text-zinc-500">{artifact}</span>
                        <span className="text-zinc-600">—</span>
                        <span className="text-zinc-300">{line}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  )
}

export default RallyConversationModal
