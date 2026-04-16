import type { OperatorAction, RunningExecutionState } from '../types'
import { CopyButton } from './badges'
import { formatElapsedMs } from '../utils/formatting'

interface OperatorActionCardProps {
  action: OperatorAction
  mode: 'manual' | 'executable'
  taxonomy: string
  runName: string
  comment: string
  isSaved: boolean
  savingActionId: string | null
  rerunComments: Record<string, string>
  savedCommentByAction: Record<string, string>
  executionNow: number
  isRunning: boolean
  runBusy: boolean
  canExecute: boolean
  runningState: RunningExecutionState | null
  saveRerunComment: (action: OperatorAction, taxonomy: string, runName: string) => Promise<void>
  executeAction: (action: OperatorAction, taxonomy: string, runName: string) => Promise<void>
  setRerunComments: React.Dispatch<React.SetStateAction<Record<string, string>>>
  setSavedCommentByAction: React.Dispatch<React.SetStateAction<Record<string, string>>>
}

export function OperatorActionCard({
  action,
  mode,
  taxonomy,
  runName,
  comment,
  isSaved,
  savingActionId,
  executionNow,
  isRunning,
  runBusy,
  canExecute,
  runningState,
  saveRerunComment,
  executeAction,
  setRerunComments,
  setSavedCommentByAction,
}: OperatorActionCardProps) {
  return (
    <div
      className={`rounded border p-3 ${mode === 'manual' ? 'border-zinc-700 bg-zinc-900/70' : 'border-zinc-800 bg-zinc-900/40'}`}
    >
      <div className="mb-2 flex items-start justify-between gap-3">
        <div>
          <div className="flex items-center gap-2">
            <div className="font-semibold">{action.label}</div>
            {action.primary && <span className="rounded bg-indigo-500/20 px-1.5 py-0.5 text-[10px] text-indigo-300">PRIMARY</span>}
            {mode === 'manual' && (
              <span className="rounded border border-zinc-600 bg-zinc-800 px-1.5 py-0.5 text-[10px] font-bold uppercase tracking-wide text-zinc-300">
                Manual
              </span>
            )}
            {isRunning && (
              <span className="rounded border border-amber-400/30 bg-amber-500/10 px-1.5 py-0.5 text-[10px] font-bold uppercase tracking-wide text-amber-100">
                Running {runningState ? formatElapsedMs(executionNow - runningState.startedAt) : ''}
              </span>
            )}
          </div>
          <div className="mt-1 text-xs text-zinc-500">{action.description}</div>
          {action.comment_artifact && <div className="mt-1 text-xs text-zinc-400">Comment target: <span className="font-mono text-indigo-300">{action.comment_artifact}</span></div>}
        </div>
        <CopyButton text={action.command} />
      </div>
      <div className="mb-3 whitespace-pre-wrap break-words rounded bg-black/30 p-2 font-mono text-xs">{action.command}</div>

      {action.execution_type === 'rerun' && action.comment_artifact && (
        <div className="mb-3 rounded border border-zinc-800 bg-black/20 p-3">
          <div className="mb-2 text-xs font-semibold text-zinc-300">Rerun Comment</div>
          <textarea
            value={comment}
            onChange={(e) => {
              const next = e.target.value
              setRerunComments((current) => ({ ...current, [action.id]: next }))
              if (setSavedCommentByAction && next.trim() !== comment.trim()) {
                setSavedCommentByAction((current) => {
                  const copy = { ...current }
                  delete copy[action.id]
                  return copy
                })
              }
            }}
            className="min-h-24 w-full rounded border border-zinc-700 bg-zinc-950 p-2 text-sm"
            placeholder={`Feedback to append to ${action.comment_artifact}`}
          />
          <div className="mt-2 flex items-center justify-between">
            <div className="text-xs text-zinc-500">{isSaved ? 'Saved to artifact.' : 'Save before rerun.'}</div>
            <button
              onClick={() => void saveRerunComment(action, taxonomy, runName)}
              disabled={savingActionId !== null || comment.trim() === '' || isSaved}
              className="rounded border border-indigo-500/30 bg-indigo-500/15 px-3 py-1.5 text-xs font-bold text-indigo-200 disabled:border-zinc-800 disabled:bg-zinc-900 disabled:text-zinc-500"
            >
              {savingActionId === action.id ? 'Saving...' : 'Save Comment'}
            </button>
          </div>
        </div>
      )}

      <button
        onClick={() => void executeAction(action, taxonomy, runName)}
        disabled={!canExecute || runBusy}
        className={`w-full rounded border px-3 py-2 text-xs font-bold ${
          mode === 'manual'
            ? 'border-zinc-800 bg-zinc-950/50 text-zinc-500'
            : isRunning
              ? 'animate-pulse border-red-400 bg-red-500/25 text-red-50'
              : 'border-zinc-700 bg-zinc-950 text-zinc-200 disabled:border-zinc-800 disabled:bg-zinc-900 disabled:text-zinc-500'
        }`}
      >
        {isRunning ? 'Running...' : action.execution_type === 'human' ? 'Human Guidance Only' : action.label}
      </button>
    </div>
  )
}
