import { useEffect, useState } from 'react'
import type { ActionExecutionRecord, HistoricalExecutionLog } from '../../types'
import { buildExecutionLogText, hasExecutionLogContent } from '../../utils/formatting'
import { PhaseBadge, CopyButton } from '../../components/badges'

const API_BASE = '/api'

export function ExecutionLogModal({
  job,
  onClose,
}: {
  job: ActionExecutionRecord
  onClose: () => void
}) {
  const [detail, setDetail] = useState<HistoricalExecutionLog | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [loadError, setLoadError] = useState<string | null>(null)

  const load = async () => {
    setIsLoading(true)
    setLoadError(null)
    try {
      const resp = await fetch(`${API_BASE}/executions/${job.id}/log`)
      if (!resp.ok) {
        throw new Error(`Failed to load execution log (${resp.status})`)
      }
      const data = (await resp.json()) as HistoricalExecutionLog
      setDetail(data)
    } catch (error) {
      setLoadError(error instanceof Error ? error.message : 'Failed to load execution log')
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    let cancelled = false
    void (async () => {
      setIsLoading(true)
      setLoadError(null)
      try {
        const resp = await fetch(`${API_BASE}/executions/${job.id}/log`)
        if (!resp.ok) {
          throw new Error(`Failed to load execution log (${resp.status})`)
        }
        const data = (await resp.json()) as HistoricalExecutionLog
        if (!cancelled) setDetail(data)
      } catch (error) {
        if (!cancelled) {
          setLoadError(error instanceof Error ? error.message : 'Failed to load execution log')
        }
      } finally {
        if (!cancelled) setIsLoading(false)
      }
    })()
    return () => {
      cancelled = true
    }
  }, [job.id])

  const stdout = detail?.available ? detail.stdout : job.stdout_summary
  const stderr = detail?.available ? detail.stderr : job.stderr_summary
  const fullLog = buildExecutionLogText(stdout, stderr)
  const isSummaryOnly = detail ? !detail.available : false
  const hasVisibleContent = hasExecutionLogContent(stdout, stderr)

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4 backdrop-blur-sm" onClick={onClose}>
      <div className="max-h-[85vh] w-full max-w-5xl overflow-hidden rounded-2xl border border-zinc-800 bg-zinc-950 shadow-2xl shadow-black/60" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-start justify-between gap-4 border-b border-zinc-800 px-5 py-4">
          <div className="min-w-0">
            <div className="flex items-center gap-2">
              <div className="truncate font-mono text-sm font-bold text-white">{job.run_name}</div>
              <PhaseBadge phase={job.result_status} />
            </div>
            <div className="mt-1 flex flex-wrap items-center gap-x-2 gap-y-1 font-mono text-[10px] uppercase tracking-wider text-zinc-500">
              <span>{job.taxonomy}</span>
              <span className="opacity-30">|</span>
              <span>{job.action_id}</span>
              <span className="opacity-30">|</span>
              <span>{job.action_type || 'generic'}</span>
              {job.exit_code !== null && job.exit_code !== undefined && (
                <>
                  <span className="opacity-30">|</span>
                  <span>exit {job.exit_code}</span>
                </>
              )}
            </div>
          </div>
          <button onClick={onClose} className="rounded border border-zinc-700 px-3 py-1 text-xs text-zinc-300 hover:border-zinc-500 hover:text-white">
            Close
          </button>
        </div>

        <div className="space-y-4 overflow-y-auto p-5">
          <div className="rounded border border-zinc-800 bg-zinc-900/40 p-3">
            <div className="mb-2 flex items-center justify-between gap-3">
              <div className="text-[10px] font-bold uppercase tracking-[0.25em] text-zinc-500">Command</div>
              <CopyButton text={job.command} />
            </div>
            <pre className="overflow-x-auto whitespace-pre-wrap break-all rounded bg-black/40 p-3 font-mono text-xs text-zinc-300">{job.command}</pre>
          </div>

          {isLoading ? (
            <div className="rounded border border-zinc-800 bg-zinc-900/20 p-6 text-center text-sm text-zinc-500">
              Fetching full historical log...
            </div>
          ) : loadError ? (
            <div className="rounded border border-red-500/30 bg-red-500/10 p-6 text-center text-sm text-red-200">
              <div>{loadError}</div>
              <button
                onClick={() => void load()}
                className="mt-3 rounded border border-red-400/40 px-3 py-1.5 text-xs font-semibold text-red-100 hover:border-red-300 hover:bg-red-500/10"
              >
                Retry
              </button>
            </div>
          ) : hasVisibleContent ? (
            <>
              {isSummaryOnly && (
                <div className="rounded border border-amber-500/30 bg-amber-500/10 px-3 py-2 text-xs text-amber-200">
                  Summary only. Full historical log was not stored for this legacy execution record. Re-run the action to capture full output under the new persistence path.
                </div>
              )}

              <div className="flex flex-wrap items-center justify-end gap-2">
                {stdout && <CopyButton text={stdout} />}
                {stderr && <CopyButton text={stderr} />}
                {fullLog && <CopyButton text={fullLog} />}
              </div>

              {stdout && (
                <div className="rounded border border-zinc-800 bg-zinc-900/40 p-3">
                  <div className="mb-2 flex items-center justify-between gap-3">
                    <div className="text-[10px] font-bold uppercase tracking-[0.25em] text-zinc-500">Output</div>
                    <div className="text-[10px] text-zinc-600">{isSummaryOnly ? 'Persisted summary' : 'Full historical log'}</div>
                  </div>
                  <pre className="max-h-[28vh] overflow-auto whitespace-pre-wrap rounded bg-black/40 p-3 font-mono text-xs text-zinc-200">{stdout}</pre>
                </div>
              )}

              {stderr && (
                <div className="rounded border border-red-500/20 bg-red-500/5 p-3">
                  <div className="mb-2 flex items-center justify-between gap-3">
                    <div className="text-[10px] font-bold uppercase tracking-[0.25em] text-red-300">Error</div>
                    <div className="text-[10px] text-red-200/60">{isSummaryOnly ? 'Persisted summary' : 'Full historical log'}</div>
                  </div>
                  <pre className="max-h-[28vh] overflow-auto whitespace-pre-wrap rounded bg-red-950/30 p-3 font-mono text-xs text-red-100">{stderr}</pre>
                </div>
              )}
            </>
          ) : isSummaryOnly ? (
            <div className="rounded border border-amber-500/30 bg-amber-500/10 p-6 text-center text-sm text-amber-200">
              This is a legacy summary-only execution record, and no persisted summary text is available.
            </div>
          ) : (
            <div className="rounded border border-dashed border-zinc-800 bg-zinc-900/20 p-6 text-center text-sm text-zinc-500">
              No output was produced for this execution, or the persisted full log is empty.
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default ExecutionLogModal
