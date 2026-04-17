import type { ActionExecutionRecord } from '../../types'
import { PhaseBadge, CopyButton } from '../badges'
import { prettifyActionId, summarizeExecutionIntent, summarizeExecutionOutcome } from '../../utils/formatting'

interface LastActionCardProps {
  latestRunExecution: ActionExecutionRecord | null
}

export function LastActionCard({ latestRunExecution }: LastActionCardProps) {
  return (
    <div className="rounded border border-zinc-800 bg-zinc-900/40 p-4">
      <div className="mb-2 flex items-center justify-between gap-2">
        <div>
          <div className="text-[11px] font-bold uppercase tracking-[0.2em] text-zinc-400">Last Action</div>
          <div className="mt-1 text-[10px] text-zinc-500">Latest Agent OS operator event.</div>
        </div>
        {latestRunExecution && <PhaseBadge phase={latestRunExecution.result_status} />}
      </div>
      {latestRunExecution ? (
        <div className="space-y-2 text-xs text-zinc-400">
          <div>
            <div className="text-[10px] uppercase tracking-wide text-zinc-500">What Ran</div>
            <div className="mt-0.5 font-semibold text-zinc-200">
              {summarizeExecutionIntent(
                latestRunExecution.action_id,
                latestRunExecution.command,
                latestRunExecution.action_type,
              )}
            </div>
            <div className="mt-1 font-mono text-[10px] text-zinc-500">
              {prettifyActionId(latestRunExecution.action_id)}
            </div>
          </div>
          <div>{latestRunExecution.triggered_at.slice(0, 19).replace('T', ' ')} UTC</div>
          <div className="rounded border border-zinc-800 bg-black/20 p-2">
            <div className="mb-1 flex items-start justify-between gap-2 text-[10px] text-zinc-500">
              <span>Command</span>
              <CopyButton text={latestRunExecution.command} />
            </div>
            <div className="line-clamp-3 break-words font-mono text-[10px] text-zinc-300">{latestRunExecution.command}</div>
          </div>
          <div>
            <div className="text-[10px] uppercase tracking-wide text-zinc-500">Outcome Summary</div>
            <div className="mt-0.5 text-zinc-300">
              {summarizeExecutionOutcome(latestRunExecution.stdout_summary, latestRunExecution.stderr_summary)}
            </div>
          </div>
        </div>
      ) : (
        <div className="text-xs text-zinc-500">No Agent OS operator execution captured yet.</div>
      )}
    </div>
  )
}
