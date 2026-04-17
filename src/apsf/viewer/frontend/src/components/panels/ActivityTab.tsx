import { Activity, Clock, Search, Terminal } from 'lucide-react'
import type { ActionExecutionRecord, ExecutionResult, SaveCommentResult } from '../../types'
import { PhaseBadge } from '../badges'
import {
  formatDuration,
  formatRelativeTime,
  buildExecutionLogText,
  hasExecutionLogContent,
} from '../../utils/formatting'
import { CopyButton } from '../badges'

interface ActivityTabProps {
  jobsSearchTerm: string
  setJobsSearchTerm: (value: string) => void
  recentExecutions: ActionExecutionRecord[]
  setSelectedExecutionLog: (job: ActionExecutionRecord | null) => void
  executionResult: ExecutionResult | null
  saveCommentResult: SaveCommentResult | null
}

export function ActivityTab({
  jobsSearchTerm,
  setJobsSearchTerm,
  recentExecutions,
  setSelectedExecutionLog,
  executionResult,
  saveCommentResult,
}: ActivityTabProps) {
  const filteredRecentExecutions = recentExecutions.filter((job) => job.run_name.toLowerCase().includes(jobsSearchTerm.toLowerCase()))
  return (
    <div className="space-y-4">
      <div className="rounded border border-zinc-800 bg-zinc-900/10 p-4">
        <div className="mb-4 border-b border-zinc-800 pb-3 flex items-center justify-between gap-3">
          <div>
            <div className="flex items-center gap-2">
              <Activity size={14} className="text-zinc-500 pulse-slow" />
              <div className="text-[10px] font-bold uppercase tracking-[0.3em] text-zinc-400">System Pulse</div>
            </div>
            <div className="mt-1 font-mono text-[9px] text-zinc-500 uppercase">Real-time execution telemetry</div>
          </div>
          <div className="relative w-full max-w-[200px]">
            <Search size={12} className="absolute left-3 top-2.5 text-zinc-600" />
            <input
              value={jobsSearchTerm}
              onChange={(e) => setJobsSearchTerm(e.target.value)}
              className="w-full rounded border border-zinc-800 bg-zinc-950/50 py-1.5 pl-8 pr-3 font-mono text-[9px] text-zinc-400 placeholder:text-zinc-700 focus:border-zinc-600 outline-none transition-colors"
              placeholder="SCAN IDENTIFIER..."
            />
          </div>
        </div>
        <div className="system-pulse-grid min-h-[400px] space-y-2 rounded border border-zinc-800/50 bg-black/20 p-2">
           {filteredRecentExecutions.length > 0 ? filteredRecentExecutions.map((job) => {
             const statusColorMap: Record<string, string> = {
               SUCCESS: 'bg-emerald-500 glow-emerald',
               FAILED: 'bg-red-500 glow-red',
               PENDING: 'bg-zinc-500 pulse-slow glow-zinc',
               PARTIAL: 'bg-amber-500 glow-amber',
               HUMAN: 'bg-sky-500 glow-sky',
             }
             const accentColor = statusColorMap[job.result_status] || 'bg-zinc-700'

             return (
               <div key={job.id} className="group relative overflow-hidden rounded border border-zinc-800/50 bg-zinc-950/40 transition-all hover:bg-zinc-900/60 hover:border-zinc-700 focus-within:border-zinc-600">
                 {/* Left accent bar */}
                 <div className={`absolute left-0 top-0 bottom-0 w-[4px] ${accentColor}`} />

                 <div className="p-3 pl-4">
                   <div className="flex items-start justify-between gap-4">
                     <div className="flex min-w-0 items-start gap-3">
                       <div className={`mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded border border-zinc-700 bg-black/60 text-zinc-400 group-hover:text-zinc-200 transition-colors`}>
                         {job.result_status === 'PENDING' ? <Activity size={14} className="pulse-slow" /> : <Terminal size={14} />}
                       </div>
                       <div className="min-w-0">
                         <div className="flex items-center gap-2">
                           <span className="truncate font-mono text-[11px] font-bold tracking-tight text-white">{job.run_name}</span>
                           <span className="shrink-0 rounded-sm border border-zinc-700 bg-zinc-900/80 px-1 py-0.5 font-mono text-[8px] uppercase tracking-tighter text-zinc-400">{job.taxonomy}</span>
                         </div>
                         <div className="mt-1 flex items-center gap-2 font-mono text-[9px] uppercase tracking-widest text-zinc-500">
                           <span className="text-zinc-400">{job.action_id}</span>
                           <span className="opacity-20">|</span>
                           <span className="text-zinc-500">{job.action_type || 'generic'}</span>
                         </div>
                       </div>
                     </div>
                      <div className="flex flex-col items-end gap-1.5">
                        <PhaseBadge phase={job.result_status} />
                        {job.finished_at && (
                          <div className="font-mono text-[9px] text-zinc-400 flex items-center gap-1">
                            <Clock size={10} className="text-zinc-500" />
                            {formatDuration(job.triggered_at, job.finished_at)}
                           </div>
                         )}
                        {hasExecutionLogContent(job.stdout_summary, job.stderr_summary) && (
                          <button
                            onClick={() => setSelectedExecutionLog(job)}
                            className="rounded border border-zinc-700 bg-black/40 px-2 py-1 font-mono text-[9px] uppercase tracking-[0.2em] text-zinc-300 hover:border-zinc-500 hover:text-white"
                          >
                            View Log
                          </button>
                        )}
                       </div>
                     </div>

                    {/* Metadata Footer */}
                     <div className="mt-3 space-y-2 border-t border-zinc-800/30 pt-2 transition-opacity group-hover:opacity-100 opacity-60">
                      <div className="flex items-center gap-2 font-mono text-[9px] text-zinc-400">
                        <div className="h-1 w-1 rounded-full bg-zinc-500"></div>
                        <span>T-MINUS {formatRelativeTime(job.triggered_at).toUpperCase()}</span>
                      </div>
                      <div className="relative rounded-sm bg-black/60 p-2 font-mono text-[10px] leading-relaxed text-zinc-300 break-all border border-zinc-700/50">
                        <span className="mr-2 text-brand font-bold">$</span>
                        {job.command}
                      </div>
                    </div>
                  </div>
                </div>
               )
             }) : (
               <div className="flex h-32 items-center justify-center rounded border border-dashed border-zinc-800 bg-black/20 p-4 text-center font-mono text-[10px] text-zinc-700 tracking-[0.2em] uppercase">
                 {jobsSearchTerm ? 'IDENTIFIER NOT FOUND IN SECTOR' : 'NO PULSE ACTIVITY DETECTED'}
               </div>
             )}
        </div>
      </div>

      {executionResult && (
        <div className={`rounded border ${
          executionResult.status === 'FAILED' && executionResult.exit_code === 1 && !executionResult.stdout
            ? 'border-yellow-500/40 bg-yellow-500/5'
            : executionResult.status === 'FAILED'
              ? 'border-red-500/50 bg-red-500/5'
              : 'border-zinc-800 bg-zinc-900/40'
        } p-3 animate-in fade-in slide-in-from-bottom-2`}>
          <div className="mb-2 flex items-center justify-between">
            <div className={`text-xs font-bold ${
              executionResult.status === 'FAILED' && executionResult.exit_code === 1 && !executionResult.stdout
                ? 'text-yellow-300'
                : executionResult.status === 'FAILED'
                  ? 'text-red-400'
                  : 'text-zinc-300'
            }`}>
              {executionResult.status === 'FAILED' && executionResult.exit_code === 1 && !executionResult.stdout
                ? 'BLOCKED: '
                : executionResult.status === 'FAILED'
                  ? 'ERROR: '
                  : ''}Execution Result
            </div>
            <div className="flex items-center gap-2">
              {hasExecutionLogContent(executionResult.stdout, executionResult.stderr) && (
                <CopyButton text={buildExecutionLogText(executionResult.stdout, executionResult.stderr)} />
              )}
              <PhaseBadge phase={executionResult.status} />
            </div>
          </div>
          <div className="mb-2 text-[10px] text-zinc-500">
            <span className="opacity-70">action:</span> {executionResult.action_id}
            <span className="mx-2">|</span>
            <span className="opacity-70">exit code:</span> <span className={executionResult.exit_code !== 0 ? 'text-red-400' : ''}>{executionResult.exit_code}</span>
          </div>

          {executionResult.status === 'FAILED' && executionResult.exit_code === 1 && !executionResult.stdout ? (
            <div className="mb-2 rounded bg-yellow-500/20 px-2 py-1 text-[10px] font-bold text-yellow-100">
              Operation was blocked before execution. Check the reason below.
            </div>
          ) : executionResult.status === 'FAILED' ? (
            <div className="mb-2 rounded bg-red-500/20 px-2 py-1 text-[10px] font-bold text-red-200">
              Operation failed. Check the logs below for details.
            </div>
          ) : executionResult.status === 'SUCCESS' ? (
            <div className="mb-2 rounded bg-emerald-500/15 px-2 py-1 text-[10px] font-bold text-emerald-100">
              Operation completed successfully.
            </div>
          ) : null}

          <div className="space-y-2">
            {executionResult.stdout && (
              <div>
                <div className="mb-1 flex items-center justify-between gap-2 text-[10px] font-bold uppercase tracking-wider text-zinc-600">
                  <span>Stdout</span>
                  <CopyButton text={executionResult.stdout} />
                </div>
                <pre className="max-h-40 overflow-auto rounded bg-black/40 p-2 text-xs whitespace-pre-wrap border border-zinc-800/50">
                  {executionResult.stdout}
                </pre>
              </div>
            )}
            {executionResult.stderr && (
              <div>
                <div className="mb-1 flex items-center justify-between gap-2 text-[10px] font-bold uppercase tracking-wider text-red-900/60">
                  <span>Stderr</span>
                  <CopyButton text={executionResult.stderr} />
                </div>
                <pre className="max-h-40 overflow-auto rounded bg-red-950/20 p-2 text-xs whitespace-pre-wrap border border-red-900/30 text-red-300">
                  {executionResult.stderr}
                </pre>
              </div>
            )}
            {!executionResult.stdout && !executionResult.stderr && (
              <div className="py-2 text-center text-[11px] text-zinc-500 italic">No output captured.</div>
            )}
          </div>
        </div>
      )}

      {saveCommentResult && (
        <div className="rounded border border-indigo-500/30 bg-indigo-500/10 p-3 text-xs">
          <div className="font-semibold text-indigo-300">Comment Saved</div>
          <div className="mt-1">{saveCommentResult.artifact_name}</div>
          <div className="mt-1 break-all font-mono text-zinc-400">{saveCommentResult.artifact_path}</div>
        </div>
      )}
    </div>
  )
}
