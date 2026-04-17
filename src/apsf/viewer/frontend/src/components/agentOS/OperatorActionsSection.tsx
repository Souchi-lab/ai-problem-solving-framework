import type { ActionExecutionRecord, AgentOSActionFeedback } from '../../types'
import { PhaseBadge, CopyButton } from '../badges'

interface OperatorActionsSectionProps {
  selectedTaxonomy: string
  targetRun: string
  agentOSFeedback: AgentOSActionFeedback | null
  selectedRecoveryCheckpointId: string | null
  selectedRecoverySnapshotId: string | null
  latestRunExecution: ActionExecutionRecord | null
  recentAgentOSExecutions: ActionExecutionRecord[]
  executingActionForRun: (taxonomy: string, runName: string) => string | null
  executeAgentOSAction: (
    actionId: 'act' | 'capture-snapshot' | 'capture-checkpoint' | 'apply-snapshot' | 'apply-checkpoint',
    taxonomy: string,
    runName: string,
  ) => void
}

export function OperatorActionsSection({
  selectedTaxonomy,
  targetRun,
  agentOSFeedback,
  selectedRecoveryCheckpointId,
  selectedRecoverySnapshotId,
  latestRunExecution,
  recentAgentOSExecutions,
  executingActionForRun,
  executeAgentOSAction,
}: OperatorActionsSectionProps) {
  return (
    <div className="rounded border border-fuchsia-500/20 bg-fuchsia-500/5 p-4">
      <div className="mb-1 text-[11px] font-bold uppercase tracking-[0.2em] text-fuchsia-300">Operator Actions</div>
      <div className="mb-4 text-[10px] text-zinc-500">
        Minimal GUI operator surface. Apply actions require a selected recovery candidate, an explicit reason, and confirmation.
      </div>

      {agentOSFeedback && (
        <div
          className={`mb-4 rounded border px-3 py-2 text-xs ${
            agentOSFeedback.kind === 'running'
              ? 'border-amber-500/30 bg-amber-500/10 text-amber-100'
              : agentOSFeedback.kind === 'success'
                ? 'border-emerald-500/30 bg-emerald-500/10 text-emerald-100'
                : agentOSFeedback.kind === 'blocked'
                  ? 'border-yellow-500/30 bg-yellow-500/10 text-yellow-100'
                  : 'border-red-500/30 bg-red-500/10 text-red-200'
          }`}
        >
          <div className="flex items-center justify-between gap-3">
            <div className="font-semibold uppercase tracking-wide">{agentOSFeedback.title}</div>
            {agentOSFeedback.actionId && (
              <div className="font-mono text-[10px] opacity-80">{agentOSFeedback.actionId}</div>
            )}
          </div>
          <div className="mt-1 whitespace-pre-wrap text-[11px] opacity-90">{agentOSFeedback.detail}</div>
        </div>
      )}

      <div className="mb-4 grid gap-3 xl:grid-cols-5">
        {[
          {
            id: 'capture-snapshot' as const,
            label: 'Capture Snapshot',
            description: 'Capture existing canonical artifacts as a recovery snapshot.',
            blockedReason: '',
          },
          {
            id: 'capture-checkpoint' as const,
            label: 'Capture Checkpoint',
            description: 'Capture current execution state into recovery/checkpoints/.',
            blockedReason: '',
          },
          {
            id: 'apply-snapshot' as const,
            label: 'Apply Snapshot',
            description: selectedRecoverySnapshotId
              ? `Strong action. Selected snapshot: ${selectedRecoverySnapshotId}`
              : 'Strong action. Select a snapshot candidate first.',
            blockedReason: selectedRecoverySnapshotId ? '' : 'Blocked until a snapshot candidate is selected.',
          },
          {
            id: 'apply-checkpoint' as const,
            label: 'Apply Checkpoint',
            description: selectedRecoveryCheckpointId
              ? `Strong action. Selected checkpoint: ${selectedRecoveryCheckpointId}`
              : 'Strong action. Select a checkpoint candidate first.',
            blockedReason: selectedRecoveryCheckpointId ? '' : 'Blocked until a checkpoint candidate is selected.',
          },
        ].map((action) => {
          const runningActionId = executingActionForRun(selectedTaxonomy, targetRun)
          const isRunning = runningActionId === action.id
          const runBusy = runningActionId !== null
          const isStrongAction = action.id === 'apply-snapshot' || action.id === 'apply-checkpoint'
          const isBlocked = Boolean(action.blockedReason)
          const toneClass = isStrongAction ? 'border-red-500/25 bg-red-500/5' : 'border-zinc-800 bg-zinc-900/30'
          return (
            <div key={action.id} className={`rounded border p-3 ${toneClass}`}>
              <div className="mb-2 flex items-center justify-between gap-2">
                <div className="text-sm font-semibold text-zinc-100">{action.label}</div>
                <div className="flex items-center gap-1.5">
                  {isStrongAction && (
                    <span className="rounded border border-red-400/30 bg-red-500/10 px-1.5 py-0.5 text-[9px] font-bold uppercase text-red-200">
                      Strong
                    </span>
                  )}
                  {isRunning ? (
                    <span className="rounded border border-amber-400/30 bg-amber-500/10 px-1.5 py-0.5 text-[9px] font-bold uppercase text-amber-100">
                      Running
                    </span>
                  ) : isBlocked ? (
                    <span className="rounded border border-yellow-400/30 bg-yellow-500/10 px-1.5 py-0.5 text-[9px] font-bold uppercase text-yellow-100">
                      Blocked
                    </span>
                  ) : (
                    <span className="rounded border border-emerald-400/30 bg-emerald-500/10 px-1.5 py-0.5 text-[9px] font-bold uppercase text-emerald-100">
                      Ready
                    </span>
                  )}
                </div>
              </div>
              <div className="mb-3 min-h-12 text-[11px] text-zinc-400">{action.description}</div>
              {isBlocked && (
                <div className="mb-3 rounded border border-yellow-500/20 bg-yellow-500/5 px-2 py-1 text-[10px] text-yellow-100">
                  {action.blockedReason}
                </div>
              )}
              <button
                type="button"
                onClick={() => executeAgentOSAction(action.id, selectedTaxonomy, targetRun)}
                disabled={runBusy}
                className={`w-full rounded border px-3 py-2 text-xs font-bold transition-colors disabled:border-zinc-800 disabled:bg-zinc-900 disabled:text-zinc-600 ${
                  isStrongAction
                    ? 'border-red-500/30 bg-red-500/15 text-red-100 hover:bg-red-500/20'
                    : 'border-fuchsia-400/30 bg-fuchsia-500/15 text-fuchsia-100 hover:bg-fuchsia-500/20'
                }`}
              >
                {isRunning ? 'Running...' : action.label}
              </button>
            </div>
          )
        })}
      </div>

      <div className="grid gap-3 xl:grid-cols-3">
        <div className="rounded border border-zinc-800 bg-black/20 p-3 text-[10px]">
          <div className="mb-2 text-[10px] font-bold uppercase tracking-[0.2em] text-zinc-500">Current Selection</div>
          <div className="space-y-1 text-zinc-400">
            <div>Checkpoint: <span className="font-mono text-zinc-200">{selectedRecoveryCheckpointId || '(none)'}</span></div>
            <div>Snapshot: <span className="font-mono text-zinc-200">{selectedRecoverySnapshotId || '(none)'}</span></div>
          </div>
        </div>
        <div className="rounded border border-zinc-800 bg-black/20 p-3 text-[10px]">
          <div className="mb-2 text-[10px] font-bold uppercase tracking-[0.2em] text-zinc-500">Latest Summary</div>
          {latestRunExecution ? (
            <div className="space-y-2 text-zinc-400">
              <div className="flex items-center justify-between gap-2">
                <span className="font-mono text-zinc-200">{latestRunExecution.action_id}</span>
                <PhaseBadge phase={latestRunExecution.result_status} />
              </div>
              <div>{latestRunExecution.triggered_at.slice(0, 19).replace('T', ' ')} UTC</div>
              <div className="rounded bg-black/30 px-2 py-1 font-mono text-[9px] text-zinc-300">
                <div className="mb-1 flex items-start justify-between gap-2">
                  <span className="text-zinc-500">Command</span>
                  <CopyButton text={latestRunExecution.command} />
                </div>
                <div>{latestRunExecution.command}</div>
              </div>
              {latestRunExecution.stdout_summary && (
                <div className="rounded border border-zinc-800/60 bg-zinc-950/40 px-2 py-1 text-[9px] text-zinc-300">
                  <div className="mb-1 flex items-start justify-between gap-2">
                    <span className="text-zinc-500">Stdout</span>
                    <CopyButton text={latestRunExecution.stdout_summary} />
                  </div>
                  {latestRunExecution.stdout_summary}
                </div>
              )}
              {latestRunExecution.stderr_summary && (
                <div className="rounded border border-red-500/20 bg-red-950/20 px-2 py-1 text-[9px] text-red-200">
                  <div className="mb-1 flex items-start justify-between gap-2">
                    <span className="text-red-300/80">Stderr</span>
                    <CopyButton text={latestRunExecution.stderr_summary} />
                  </div>
                  {latestRunExecution.stderr_summary}
                </div>
              )}
            </div>
          ) : (
            <div className="text-zinc-500">No execution captured yet.</div>
          )}
        </div>
        <div className="rounded border border-zinc-800 bg-black/20 p-3 text-[10px]">
          <div className="mb-2 text-[10px] font-bold uppercase tracking-[0.2em] text-zinc-500">Recent History</div>
          {recentAgentOSExecutions.length > 0 ? (
            <div className="space-y-2">
              {recentAgentOSExecutions.map((job) => {
                const tone =
                  job.result_status === 'SUCCESS'
                    ? 'border-emerald-500/20 bg-emerald-500/5'
                    : job.result_status === 'FAILED' && (job.exit_code ?? 0) === 1 && !(job.stdout_summary ?? '').trim()
                      ? 'border-yellow-500/20 bg-yellow-500/5'
                      : job.result_status === 'FAILED'
                        ? 'border-red-500/20 bg-red-500/5'
                        : job.result_status === 'PENDING'
                          ? 'border-amber-500/20 bg-amber-500/5'
                          : 'border-zinc-800 bg-zinc-950/30'
                return (
                  <div key={job.id} className={`rounded border px-2 py-2 ${tone}`}>
                    <div className="flex items-center justify-between gap-2">
                      <span className="font-mono text-zinc-200">{job.action_id}</span>
                      <PhaseBadge phase={job.result_status} />
                    </div>
                    <div className="mt-1 text-zinc-500">{job.triggered_at.slice(0, 19).replace('T', ' ')} UTC</div>
                    <div className="mt-1 rounded bg-black/20 px-2 py-1 font-mono text-[9px] text-zinc-300">
                      {job.command}
                    </div>
                    {(job.stdout_summary || job.stderr_summary) && (
                      <div className="mt-1 text-[9px] text-zinc-400">
                        {(job.stderr_summary || job.stdout_summary || '').split('\n')[0]}
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          ) : (
            <div className="text-zinc-500">No recent Agent OS operator history yet.</div>
          )}
        </div>
      </div>

      <div className="mt-3 rounded border border-zinc-800 bg-black/20 p-3 text-[10px] text-zinc-400">
        <div className="mb-2 text-[10px] font-bold uppercase tracking-[0.2em] text-zinc-500">Safety Boundary</div>
        <div>`act` and capture actions are low-risk button actions.</div>
        <div className="mt-1">`apply snapshot` and `apply checkpoint` stay blocked until a candidate is selected, then require reason and confirmation in the modal.</div>
        <div className="mt-1">History is read-only and mirrors the latest few Agent OS operator executions already stored in the viewer log.</div>
      </div>
    </div>
  )
}
