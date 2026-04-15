import { useState } from 'react'
import { Check, Copy } from 'lucide-react'
import type { RunSummary, RunDetail, CodexBridgeResult } from '../../types'
import { parseSatisfiabilityReason } from '../../utils/formatting'

export const PhaseBadge = ({ phase }: { phase: string }) => {
  const colors: Record<string, string> = {
    PENDING: 'bg-zinc-500/10 text-zinc-200 border-zinc-500/40 glow-zinc pulse-slow',
    PARTIAL: 'bg-amber-500/10 text-amber-200 border-amber-500/50 glow-amber',
    FAILED: 'bg-red-500/10 text-red-200 border-red-500/50 glow-red',
    SUCCESS: 'bg-emerald-500/10 text-emerald-300 border-emerald-500/50 glow-emerald',
    HUMAN: 'bg-sky-500/10 text-sky-300 border-sky-500/50 glow-sky',
    PLAN_NEEDED: 'bg-blue-500/10 text-blue-300 border-blue-500/50',
    BUILD_NEEDED: 'bg-orange-500/10 text-orange-300 border-orange-500/50',
    REVIEW_NEEDED: 'bg-purple-500/10 text-purple-300 border-purple-500/50',
    IMPROVE_NEEDED: 'bg-pink-500/10 text-pink-300 border-pink-500/50',
    RESULT_NEEDED: 'bg-cyan-500/10 text-cyan-300 border-cyan-500/50',
    COMPLETE: 'bg-green-500/10 text-green-300 border-green-500/50 glow-emerald',
    TRANSCRIPT_RECOMMENDED: 'bg-yellow-500/10 text-yellow-300 border-yellow-500/50',
  }

  return (
    <span className={`px-2.5 py-0.5 text-[9px] font-bold tracking-tighter uppercase rounded border ${colors[phase] ?? 'bg-zinc-500/10 text-zinc-400 border-zinc-500/30'}`}>
      {phase}
    </span>
  )
}

export const AssignmentModeBadge = ({ mode }: { mode: string }) => {
  const colors: Record<string, string> = {
    explicit: 'border-emerald-500/30 bg-emerald-500/10 text-emerald-200',
    inferred: 'border-sky-500/30 bg-sky-500/10 text-sky-200',
    auto: 'border-cyan-500/30 bg-cyan-500/10 text-cyan-200',
    default: 'border-amber-500/30 bg-amber-500/10 text-amber-200',
    unset: 'border-zinc-600/40 bg-zinc-800/40 text-zinc-300',
    'wrapper-backed': 'border-violet-500/30 bg-violet-500/10 text-violet-200',
    unresolved: 'border-red-500/30 bg-red-500/10 text-red-200',
    human: 'border-fuchsia-500/30 bg-fuchsia-500/10 text-fuchsia-200',
    not_applicable: 'border-zinc-700/40 bg-zinc-900/40 text-zinc-500',
  }
  return (
    <span className={`rounded border px-1.5 py-0.5 text-[9px] font-bold uppercase tracking-wide ${colors[mode] ?? colors.not_applicable}`}>
      {mode}
    </span>
  )
}

export const ReworkBadge = ({ count }: { count: number }) => {
  if (count <= 0) return null
  return <span className="rounded border border-rose-500/40 bg-rose-500/15 px-1.5 py-0.5 text-[10px] font-bold text-rose-300">{count} REWORK</span>
}

export const CountBadge = ({ count }: { count: number }) => {
  if (count <= 0) return null
  return <span className="ml-1 rounded border border-emerald-500/40 bg-emerald-500/15 px-1.5 py-0.5 text-[10px] font-bold text-emerald-300">{count} CHILD</span>
}

export const PriorityBadge = ({ priority }: { priority: RunSummary['priority'] | RunDetail['priority'] }) => {
  if (priority === 'Unranked') return null
  const colors: Record<string, string> = {
    Now: 'border-red-500/50 bg-red-500/15 text-red-300',
    Next: 'border-amber-500/50 bg-amber-500/15 text-amber-300',
    Later: 'border-sky-500/50 bg-sky-500/15 text-sky-300',
  }
  return <span className={`rounded border px-1.5 py-0.5 text-[10px] font-bold ${colors[priority]}`}>{priority}</span>
}

export const CodexStatusBadge = ({ status }: { status: CodexBridgeResult['status'] }) => {
  const colors: Record<CodexBridgeResult['status'], string> = {
    completed: 'border-emerald-500/40 bg-emerald-500/15 text-emerald-300',
    review_required: 'border-amber-500/40 bg-amber-500/15 text-amber-300',
    blocked: 'border-red-500/40 bg-red-500/15 text-red-300',
  }

  return <span className={`rounded border px-2 py-0.5 text-[10px] font-bold uppercase ${colors[status]}`}>{status.replace('_', ' ')}</span>
}

export const WorkflowProgress = ({
  phase,
  hasPlanReview,
  hasBuildReview,
  hasReviewReview,
  hasImproveReview,
  compact = false,
}: {
  phase: string
  hasPlanReview: boolean
  hasBuildReview: boolean
  hasReviewReview: boolean
  hasImproveReview: boolean
  compact?: boolean
}) => {
  const steps = ['GOAL', 'PLAN', 'BUILD', 'REVIEW', 'RESULT']
  const phaseMap: Record<string, number> = {
    PLAN_NEEDED: 0,
    BUILD_NEEDED: 1,
    REVIEW_NEEDED: 2,
    IMPROVE_NEEDED: 4,
    RESULT_NEEDED: 4,
    COMPLETE: 4,
    TRANSCRIPT_RECOMMENDED: 4,
  }

  const currentIdx = phaseMap[phase] ?? 0

  return (
    <div className={`transition-all duration-500 ease-in-out ${compact ? 'px-2 py-2 overflow-hidden' : 'px-2 pt-6 pb-14'}`}>
      <div className={`relative flex justify-between items-center w-full max-w-xl mx-auto transition-all duration-500 ${compact ? 'max-w-md' : 'max-w-xl'}`}>
        <div className="absolute top-1/2 left-0 w-full h-1 bg-zinc-800 -translate-y-1/2 -z-10 rounded-full" />
        <div
          className="absolute top-1/2 left-0 h-1 bg-gradient-to-r from-blue-500 to-indigo-500 transition-all duration-700 ease-in-out -translate-y-1/2 -z-10 rounded-full shadow-[0_0_15px_rgba(59,130,241,0.3)]"
          style={{ width: `${Math.min(currentIdx * 25, 100)}%` }}
        />
        {steps.map((step, idx) => {
          const isDone = idx < currentIdx
          const isCurrent = idx === currentIdx
          const hasRework =
            (step === 'PLAN' && hasPlanReview) ||
            (step === 'BUILD' && hasBuildReview) ||
            (step === 'REVIEW' && hasReviewReview) ||
            (step === 'RESULT' && hasImproveReview)

          return (
            <div key={step} className="flex flex-col items-center relative">
                <div
                  className={`rounded-full border-2 flex items-center justify-center transition-all duration-500 transform ${
                    compact ? 'w-5 h-5 text-[8px]' : 'w-10 h-10'
                  } ${
                    isDone
                      ? 'bg-indigo-600 border-indigo-400 text-white'
                      : isCurrent
                        ? 'bg-zinc-900 border-blue-500 text-blue-400 ring-4 ring-blue-500/20 scale-110'
                        : 'bg-zinc-950 border-zinc-700 text-zinc-700'
                  }`}
                >
                  {isDone ? (
                    <Check size={compact ? 10 : 18} />
                  ) : (
                    <span className={compact ? 'text-[8px] font-bold' : 'text-xs font-bold'}>{idx + 1}</span>
                  )}
                </div>
              <div className={`absolute top-full mt-2 w-24 flex flex-col items-center transition-all duration-300 ${compact ? 'opacity-0 scale-75 h-0' : 'opacity-100 scale-100'}`}>
                <span className={`text-[9px] font-black tracking-widest transition-colors duration-300 uppercase ${isCurrent ? 'text-blue-400' : isDone ? 'text-zinc-300' : 'text-zinc-600'}`}>
                  {step}
                </span>
                {hasRework && (
                  <div className="mt-1 px-1.5 py-0.5 bg-red-500/20 border border-red-500/30 rounded-full">
                    <span className="text-[7px] font-black text-red-500 uppercase">Rework</span>
                  </div>
                )}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

export function SatisfiabilityWarning({ reason }: { reason?: string | null }) {
  const parsed = parseSatisfiabilityReason(reason)
  if (!parsed.warning) return null

  const isUnsatisfied = parsed.warning.state === 'UNSATISFIED'
  const shell = isUnsatisfied
    ? 'border-amber-500/30 bg-amber-500/10 text-amber-100'
    : 'border-sky-500/30 bg-sky-500/10 text-sky-100'
  const label = isUnsatisfied ? 'Satisfiability Warning' : 'Exploratory Scope'
  const accent = isUnsatisfied ? 'text-amber-300' : 'text-sky-300'

  return (
    <div className={`mt-2 rounded border p-2.5 ${shell}`}>
      <div className={`text-[10px] font-bold uppercase tracking-[0.2em] ${accent}`}>
        {label}
      </div>
      <div className="mt-1 text-xs leading-relaxed">
        {parsed.warning.message || parsed.warning.state}
      </div>
    </div>
  )
}

export function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false)
  const onCopy = async () => {
    await navigator.clipboard.writeText(text)
    setCopied(true)
    setTimeout(() => setCopied(false), 1200)
  }
  return (
    <button onClick={() => void onCopy()} className="rounded p-1 text-zinc-400 hover:bg-white/5 hover:text-white">
      {copied ? <Check size={14} /> : <Copy size={14} />}
    </button>
  )
}
