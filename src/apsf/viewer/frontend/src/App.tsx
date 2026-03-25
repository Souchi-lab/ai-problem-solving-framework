import { useEffect, useRef, useState } from 'react'
import { Activity, Check, Clock, Copy, FileText, Search, Terminal } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

interface RunSummary {
  name: string
  taxonomy: string
  phase: string
  next_role: string
  child_count: number
  has_plan_review: boolean
  has_build_review: boolean
  has_review_review: boolean
  has_improve_review: boolean
  last_modified: number
  priority: 'Now' | 'Next' | 'Later' | 'Unranked'
  priority_reason?: string | null
}

interface ArtifactPreview {
  name: string
  exists: boolean
  size: number
  mtime: number
  preview: string
}

interface OperatorAction {
  id: string
  label: string
  command: string
  execution_type: 'act' | 'build' | 'rerun' | 'human'
  warning_level: 'none' | 'caution' | 'danger'
  enabled: boolean
  description: string
  primary: boolean
  comment_artifact?: string | null
  requires_comment?: boolean
}

interface ChildRunSummary {
  name: string
  child_name: string
  phase: string
  next_role: string
  operator_command: string
  primary_action_label: string
  has_children: boolean
}

interface RunDetail {
  name: string
  taxonomy: string
  phase: string
  next_role: string
  decision_reason: string
  artifacts: ArtifactPreview[]
  operator_command: string
  operator_actions?: OperatorAction[]
  children?: ChildRunSummary[]
  priority: 'Now' | 'Next' | 'Later' | 'Unranked'
  priority_reason?: string | null
}

interface MatrixRow {
  name: string
  taxonomy: string
  phase: string
  next_role: string
  priority: 'Now' | 'Next' | 'Later' | 'Unranked'
  priority_reason?: string | null
  plan_action?: OperatorAction | null
  build_action?: OperatorAction | null
  review_action?: OperatorAction | null
  rerun_action?: OperatorAction | null
}

interface ExecutionResult {
  action_id: string
  command: string
  status: 'SUCCESS' | 'PARTIAL' | 'FAILED' | 'HUMAN'
  exit_code: number
  stdout: string
  stderr: string
}

interface SaveCommentResult {
  action_id: string
  artifact_name: string
  artifact_path: string
  appended_at: string
}

interface ActionExecutionRecord {
  id: number
  taxonomy: string
  run_name: string
  action_id: string
  action_type: string
  command: string
  triggered_at: string
  finished_at?: string | null
  result_status: 'PENDING' | 'SUCCESS' | 'PARTIAL' | 'FAILED' | 'HUMAN'
  exit_code?: number | null
  stdout_summary?: string | null
  stderr_summary?: string | null
}

interface HistoricalExecutionLog {
  execution_id: number
  available: boolean
  stdout?: string | null
  stderr?: string | null
  stdout_summary?: string | null
  stderr_summary?: string | null
}

interface RerunCommentRecord {
  id: number
  taxonomy: string
  run_name: string
  action_id: string
  execution_id?: number | null
  comment_artifact: string
  comment_body: string
  created_at: string
}

interface RunHistory {
  latest_execution?: ActionExecutionRecord | null
  latest_rerun_comment?: RerunCommentRecord | null
}

interface CodexArtifactUpdate {
  artifact_name: string
  operation: 'propose'
}

interface CodexBridgeResult {
  status: 'completed' | 'review_required' | 'blocked'
  summary: string
  next_steps: string[]
  suggested_action_id?: string | null
  preset_id: 'finish-after-build' | 'review-and-close'
  role_mode: 'architect' | 'finisher'
  provider: string
  model: string
  artifact_updates: CodexArtifactUpdate[]
}

interface ModalConfig {
  title: string
  message: string
  onConfirm: () => void
}

const API_BASE = '/api'
const RUN_LIST_REFRESH_MS = 30000
const SELECTED_RUN_REFRESH_MS = 10000
const DEFAULT_PREVIEW_PHASES = new Set(['COMPLETE', 'TRANSCRIPT_RECOMMENDED'])
const TRANSCRIPT_ARTIFACT = 'transcript.md'
const RESULT_ARTIFACT = 'result.md'
const CODEX_PRESET_RULES = {
  'finish-after-build': {
    label: 'Finish After Build',
    description: 'Ask Codex to identify the minimum remaining work before review/close.',
    allowedPhases: new Set(['BUILD_NEEDED', 'REVIEW_NEEDED']),
  },
  'review-and-close': {
    label: 'Review And Close',
    description: 'Ask Codex to assess closure quality and close-out gaps.',
    allowedPhases: new Set(['REVIEW_NEEDED', 'IMPROVE_NEEDED', 'TRANSCRIPT_RECOMMENDED']),
  },
} as const

// Phase → artifact that should be written next (for readiness hint)
const PHASE_TO_ARTIFACT: Record<string, string> = {
  PLAN_NEEDED: 'plan.md',
  BUILD_NEEDED: 'build.md',
  REVIEW_NEEDED: 'review.md',
  IMPROVE_NEEDED: 'improve.md',
  RESULT_NEEDED: 'result.md',
  IMPROVE_PLAN_OPTIONAL: 'improve-plan.md',
  VERIFY_OPTIONAL: 'verify.md',
}

const formatDuration = (start?: string | null, end?: string | null) => {
  if (!start || !end) return null
  try {
    const d1 = new Date(start)
    const d2 = new Date(end)
    const diff = Math.floor((d2.getTime() - d1.getTime()) / 1000)
    if (diff < 0) return null
    if (diff < 60) return `${diff}s`
    return `${Math.floor(diff / 60)}m ${diff % 60}s`
  } catch (e) {
    return null
  }
}

const formatRelativeTime = (isoString?: string | null) => {
  if (!isoString) return '-'
  try {
    const date = new Date(isoString)
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffSec = Math.floor(diffMs / 1000)
    
    if (diffSec < 60) return 'Just now'
    if (diffSec < 3600) return `${Math.floor(diffSec / 60)}m ago`
    if (diffSec < 86400) return `${Math.floor(diffSec / 3600)}h ago`
    return date.toLocaleDateString()
  } catch (e) {
    return isoString
  }
}

const PhaseBadge = ({ phase }: { phase: string }) => {
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
function splitArtifactLabel(name: string) {
  const dot = name.lastIndexOf('.')
  const base = dot > 0 ? name.slice(0, dot) : name
  const ext = dot > 0 ? name.slice(dot) : ''
  const pivot = base.indexOf('_')
  if (pivot === -1) {
    return { prefix: '', suffix: name }
  }
  return {
    prefix: base.slice(0, pivot),
    suffix: `${base.slice(pivot)}${ext}`,
  }
}

function parseSatisfiabilityReason(reason?: string | null) {
  if (!reason) return { primary: '', warning: null as null | { state: 'EXPLORATORY' | 'UNSATISFIED'; message: string } }

  const markerMatch = reason.match(/\[SATISFIABILITY:\s*(EXPLORATORY|UNSATISFIED)\]\s*([\s\S]*)/i)
  if (!markerMatch) {
    return { primary: reason, warning: null as null | { state: 'EXPLORATORY' | 'UNSATISFIED'; message: string } }
  }

  const markerStart = markerMatch.index ?? 0
  const primary = reason.slice(0, markerStart).trim()
  const state = markerMatch[1].toUpperCase() as 'EXPLORATORY' | 'UNSATISFIED'
  const message = markerMatch[2].trim()
  return {
    primary,
    warning: {
      state,
      message,
    },
  }
}

function SatisfiabilityWarning({ reason }: { reason?: string | null }) {
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

function CopyButton({ text }: { text: string }) {
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

function buildExecutionLogText(stdout?: string | null, stderr?: string | null) {
  const parts: string[] = []
  if (stdout?.trim()) {
    parts.push(`STDOUT\n${stdout.trim()}`)
  }
  if (stderr?.trim()) {
    parts.push(`STDERR\n${stderr.trim()}`)
  }
  return parts.join('\n\n')
}

function hasExecutionLogContent(stdout?: string | null, stderr?: string | null) {
  return Boolean(stdout?.trim() || stderr?.trim())
}


const ReworkBadge = ({ count }: { count: number }) => {
  if (count <= 0) return null
  return <span className="rounded border border-rose-500/40 bg-rose-500/15 px-1.5 py-0.5 text-[10px] font-bold text-rose-300">{count} REWORK</span>
}

const CountBadge = ({ count }: { count: number }) => {
  if (count <= 0) return null
  return <span className="ml-1 rounded border border-emerald-500/40 bg-emerald-500/15 px-1.5 py-0.5 text-[10px] font-bold text-emerald-300">{count} CHILD</span>
}

const PriorityBadge = ({ priority }: { priority: RunSummary['priority'] | RunDetail['priority'] }) => {
  if (priority === 'Unranked') return null
  const colors: Record<string, string> = {
    Now: 'border-red-500/50 bg-red-500/15 text-red-300',
    Next: 'border-amber-500/50 bg-amber-500/15 text-amber-300',
    Later: 'border-sky-500/50 bg-sky-500/15 text-sky-300',
  }
  return <span className={`rounded border px-1.5 py-0.5 text-[10px] font-bold ${colors[priority]}`}>{priority}</span>
}

const CodexStatusBadge = ({ status }: { status: CodexBridgeResult['status'] }) => {
  const colors: Record<CodexBridgeResult['status'], string> = {
    completed: 'border-emerald-500/40 bg-emerald-500/15 text-emerald-300',
    review_required: 'border-amber-500/40 bg-amber-500/15 text-amber-300',
    blocked: 'border-red-500/40 bg-red-500/15 text-red-300',
  }

  return <span className={`rounded border px-2 py-0.5 text-[10px] font-bold uppercase ${colors[status]}`}>{status.replace('_', ' ')}</span>
}

const WorkflowProgress = ({
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

function ConfirmModal({ config, onCancel }: { config: ModalConfig; onCancel: () => void }) {
  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/60 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="w-full max-w-md scale-in-center rounded-xl border border-zinc-800 bg-zinc-900 p-6 shadow-2xl">
        <h3 className="mb-2 text-lg font-bold text-zinc-100">{config.title}</h3>
        <p className="mb-6 whitespace-pre-wrap text-sm text-zinc-400">{config.message}</p>
        <div className="flex justify-end gap-3">
          <button
            onClick={onCancel}
            className="rounded-lg bg-zinc-800 px-4 py-2 text-sm font-semibold text-zinc-300 hover:bg-zinc-700 hover:text-white transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={config.onConfirm}
            className="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-semibold text-white hover:bg-emerald-500 shadow-lg shadow-emerald-500/20 transition-all active:scale-95"
            id="modal-confirm-button"
          >
            Execute
          </button>
        </div>
      </div>
    </div>
  )
}

function ExecutionLogModal({
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

export default function App() {
  const [runs, setRuns] = useState<RunSummary[]>([])
  const [matrixRows, setMatrixRows] = useState<MatrixRow[]>([])
  const [recentExecutions, setRecentExecutions] = useState<ActionExecutionRecord[]>([])
  const [workspaceTab, setWorkspaceTab] = useState<'detail' | 'management' | 'activity'>('detail')
  const [operatorFilter, setOperatorFilter] = useState<'active' | 'recent' | 'all'>('active')
  const [detail, setDetail] = useState<RunDetail | null>(null)
  const [selectedRun, setSelectedRun] = useState<string | null>(null)
  const [selectedTaxonomy, setSelectedTaxonomy] = useState<string | null>(null)
  const [targetRun, setTargetRun] = useState<string | null>(null)
  const [targetDetail, setTargetDetail] = useState<RunDetail | null>(null)
  const [selectedArtifact, setSelectedArtifact] = useState<string | null>(null)
  const [artifactContent, setArtifactContent] = useState<string>('')
  const [searchTerm, setSearchTerm] = useState('')
  const [jobsSearchTerm, setJobsSearchTerm] = useState('')
  const [executionResult, setExecutionResult] = useState<ExecutionResult | null>(null)
  const [selectedExecutionLog, setSelectedExecutionLog] = useState<ActionExecutionRecord | null>(null)
  const [saveCommentResult, setSaveCommentResult] = useState<SaveCommentResult | null>(null)
  const [history, setHistory] = useState<RunHistory | null>(null)
  const [codexResult, setCodexResult] = useState<CodexBridgeResult | null>(null)
  const [codexError, setCodexError] = useState<string | null>(null)
  const [codexLoadingPreset, setCodexLoadingPreset] = useState<CodexBridgeResult['preset_id'] | null>(null)
  const [codexTargetKey, setCodexTargetKey] = useState<string | null>(null)
  const [modalConfig, setModalConfig] = useState<ModalConfig | null>(null)
  const [executingRuns, setExecutingRuns] = useState<Record<string, string>>({})
  const [savingActionId, setSavingActionId] = useState<string | null>(null)
  const [rerunComments, setRerunComments] = useState<Record<string, string>>({})
  const [savedCommentByAction, setSavedCommentByAction] = useState<Record<string, string>>({})
  const [isLoadingRuns, setIsLoadingRuns] = useState(true)
  const [runsError, setRunsError] = useState<string | null>(null)
  const [headerCompact, setHeaderCompact] = useState(false)
  const detailRequestIdRef = useRef(0)
  const refreshRequestIdRef = useRef(0)
  const headerCompactRef = useRef(false)

  const fetchRuns = async () => {
    setRunsError(null)
    try {
      const resp = await fetch(`${API_BASE}/runs`)
      if (!resp.ok) throw new Error(`Failed to load runs (${resp.status})`)
      setRuns(await resp.json())
    } catch (error) {
      setRuns([])
      setRunsError(error instanceof Error ? error.message : 'Failed to load runs')
    } finally {
      setIsLoadingRuns(false)
    }
  }

  const loadRunDetail = async (taxonomy: string, runName: string) => {
    const resp = await fetch(`${API_BASE}/runs/${taxonomy}/${encodeURIComponent(runName)}`)
    return resp.json()
  }

  const loadHistory = async (taxonomy: string, runName: string): Promise<RunHistory> => {
    const resp = await fetch(`${API_BASE}/runs/${taxonomy}/${encodeURIComponent(runName)}/history`)
    return resp.json()
  }

  const loadOperatorMatrix = async (): Promise<MatrixRow[]> => {
    const resp = await fetch(`${API_BASE}/operator-matrix`)
    return resp.json()
  }

  const loadRecentExecutions = async (): Promise<ActionExecutionRecord[]> => {
    const resp = await fetch(`${API_BASE}/executions/recent?limit=12&top_level_only=true`)
    return resp.json()
  }

  const makeRunKey = (taxonomy: string, runName: string) => `${taxonomy}:${runName}`
  const isRunExecuting = (taxonomy: string, runName: string) => executingRuns[makeRunKey(taxonomy, runName)] !== undefined
  const executingActionForRun = (taxonomy: string, runName: string) => executingRuns[makeRunKey(taxonomy, runName)] ?? null
  const startRunExecution = (taxonomy: string, runName: string, actionId: string) => {
    const runKey = makeRunKey(taxonomy, runName)
    setExecutingRuns((current) => ({ ...current, [runKey]: actionId }))
  }
  const finishRunExecution = (taxonomy: string, runName: string) => {
    const runKey = makeRunKey(taxonomy, runName)
    setExecutingRuns((current) => {
      const next = { ...current }
      delete next[runKey]
      return next
    })
  }

  const handleWorkspaceScroll = (scrollTop: number) => {
    const nextCompact = headerCompactRef.current ? scrollTop > 16 : scrollTop > 160
    if (nextCompact !== headerCompactRef.current) {
      headerCompactRef.current = nextCompact
      setHeaderCompact(nextCompact)
    }
  }

  // Atomic: fetch parent detail + history in parallel, update all state together
  const fetchDetail = async (taxonomy: string, runName: string) => {
    const requestId = ++detailRequestIdRef.current
    setSelectedRun(runName)
    setSelectedTaxonomy(taxonomy)
    setTargetRun(runName)
    setWorkspaceTab('detail')
    setSelectedArtifact(null)
    setArtifactContent('')
    setCodexResult(null)
    setCodexError(null)
    const [data, historyData] = await Promise.all([
      loadRunDetail(taxonomy, runName),
      loadHistory(taxonomy, runName),
    ])
    if (detailRequestIdRef.current !== requestId) return
    setDetail(data)
    setTargetDetail(data)
    setHistory(historyData)
  }

  // Atomic: fetch target detail + history in parallel, update all state together
  const fetchTargetDetail = async (taxonomy: string, runName: string) => {
    const requestId = ++detailRequestIdRef.current
    setTargetRun(runName)
    setSelectedArtifact(null)
    setArtifactContent('')
    setCodexResult(null)
    setCodexError(null)
    const [data, historyData] = await Promise.all([
      loadRunDetail(taxonomy, runName),
      loadHistory(taxonomy, runName),
    ])
    if (detailRequestIdRef.current !== requestId) return
    setTargetRun(runName)
    setTargetDetail(data)
    setHistory(historyData)
  }

  const fetchArtifact = async (filename: string) => {
    if (!targetRun || !selectedTaxonomy) return
    setSelectedArtifact(filename)
    const resp = await fetch(`${API_BASE}/runs/${selectedTaxonomy}/${encodeURIComponent(targetRun)}/artifacts/${filename}`)
    const data = await resp.json()
    setArtifactContent(data.content ?? '')
  }

  useEffect(() => {
    void fetchRuns()
    void loadOperatorMatrix().then(setMatrixRows).catch(() => setMatrixRows([]))
    void loadRecentExecutions().then(setRecentExecutions).catch(() => setRecentExecutions([]))
    const runsTimer = setInterval(() => void fetchRuns(), RUN_LIST_REFRESH_MS)
    const matrixTimer = setInterval(() => {
      void loadOperatorMatrix().then(setMatrixRows).catch(() => {})
      void loadRecentExecutions().then(setRecentExecutions).catch(() => {})
    }, RUN_LIST_REFRESH_MS)
    return () => {
      clearInterval(runsTimer)
      clearInterval(matrixTimer)
    }
  }, [])

  // Atomic auto-refresh: all three fetches in parallel, single render pass
  useEffect(() => {
    if (!selectedRun || !selectedTaxonomy) return
    const detailTimer = setInterval(async () => {
      const requestId = ++refreshRequestIdRef.current
      const parentPromise = loadRunDetail(selectedTaxonomy, selectedRun)
      const histTarget = targetRun ?? selectedRun
      const historyPromise = loadHistory(selectedTaxonomy, histTarget)
      const targetPromise = targetRun ? loadRunDetail(selectedTaxonomy, targetRun) : parentPromise

      const [parentDetail, historyData, targetDetailData] = await Promise.all([
        parentPromise,
        historyPromise,
        targetPromise,
      ])
      if (refreshRequestIdRef.current !== requestId) return
      setDetail(parentDetail)
      setTargetDetail(targetDetailData)
      setHistory(historyData)
    }, SELECTED_RUN_REFRESH_MS)
    return () => clearInterval(detailTimer)
  }, [selectedRun, selectedTaxonomy, targetRun])

  const refreshRunContexts = async (taxonomy: string, runName: string) => {
    const refreshes: Promise<void>[] = []

    if (detail && selectedTaxonomy === taxonomy) {
      refreshes.push(
        loadRunDetail(taxonomy, detail.name).then((refreshedDetail) => {
          setDetail(refreshedDetail)
          if ((targetRun ?? detail.name) === detail.name) {
            setTargetDetail(refreshedDetail)
          }
        }),
      )
    }

    refreshes.push(
      Promise.all([loadRunDetail(taxonomy, runName), loadHistory(taxonomy, runName)]).then(([refreshedRun, refreshedHistory]) => {
        if (selectedTaxonomy === taxonomy && targetRun === runName) {
          setTargetDetail(refreshedRun)
          setHistory(refreshedHistory)
        }
      }),
    )

    await Promise.all(refreshes)
  }

  const saveRerunComment = async (action: OperatorAction, taxonomy: string, runName: string) => {
    const comment = (rerunComments[action.id] ?? '').trim()
    if (!comment) {
      setModalConfig({
        title: 'Comment Required',
        message: '差し戻しコメントを入力してください。',
        onConfirm: () => setModalConfig(null),
      })
      return
    }
    setSavingActionId(action.id)
    try {
      const resp = await fetch(`${API_BASE}/runs/${taxonomy}/${encodeURIComponent(runName)}/rerun-comment`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action_id: action.id, comment_text: comment }),
      })
      const data = await resp.json()
      if (!resp.ok) throw new Error(data.detail || 'Failed to save rerun comment')
      setSavedCommentByAction((current) => ({ ...current, [action.id]: comment }))
      setSaveCommentResult(data)
      await refreshRunContexts(taxonomy, runName)
      if (selectedTaxonomy === taxonomy && targetRun === runName && action.comment_artifact && selectedArtifact === action.comment_artifact) {
        await fetchArtifact(action.comment_artifact)
      }
    } catch (error) {
      setModalConfig({
        title: 'Error Saving Comment',
        message: error instanceof Error ? error.message : 'Failed to save rerun comment',
        onConfirm: () => setModalConfig(null),
      })
    } finally {
      setSavingActionId(null)
    }
  }

  const executeAction = async (action: OperatorAction, taxonomy: string, runName: string) => {
    if (!action.enabled || action.execution_type === 'human') return
    if (action.requires_comment) {
      const currentComment = (rerunComments[action.id] ?? '').trim()
      if (!currentComment || savedCommentByAction[action.id] !== currentComment) {
        setModalConfig({
          title: 'Comment Required',
          message: '先にコメントを保存してください。',
          onConfirm: () => setModalConfig(null),
        })
        return
      }
    }

    setModalConfig({
      title: 'Confirm Execution',
      message: `次のコマンドを実行します。\n\n${action.command}\n\n続行しますか？`,
      onConfirm: async () => {
        setModalConfig(null)
        startRunExecution(taxonomy, runName, action.id)
        setExecutionResult(null)
        try {
          const resp = await fetch(`${API_BASE}/runs/${taxonomy}/${encodeURIComponent(runName)}/commands/execute`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ action_id: action.id }),
          })
          const data = await resp.json()
          if (!resp.ok) throw new Error(data.detail || 'Failed to execute command')
          setExecutionResult(data)
          await Promise.all([
            fetchRuns(),
            loadOperatorMatrix().then(setMatrixRows).catch(() => {}),
            loadRecentExecutions().then(setRecentExecutions).catch(() => {}),
          ])
          await refreshRunContexts(taxonomy, runName)
        } catch (error) {
          setExecutionResult({
            action_id: action.id,
            command: action.command,
            status: 'FAILED',
            exit_code: -1,
            stdout: '',
            stderr: error instanceof Error ? error.message : 'Failed to execute command',
          })
        } finally {
          finishRunExecution(taxonomy, runName)
        }
      },
    })
  }

  const executeMatrixAction = async (row: MatrixRow, action: OperatorAction) => {
    if (!action.enabled || action.execution_type === 'human') return
    if (action.requires_comment) {
      await fetchDetail(row.taxonomy, row.name)
      setModalConfig({
        title: 'Open Rerun Workflow',
        message: 'Rerun actions still require a saved comment. The run detail has been opened so you can save the comment and execute the rerun safely.',
        onConfirm: () => setModalConfig(null),
      })
      return
    }

    setModalConfig({
      title: `Confirm ${action.label}`,
      message: `${row.name}\n\n${action.command}`,
      onConfirm: async () => {
        setModalConfig(null)
        startRunExecution(row.taxonomy, row.name, action.id)
        setExecutionResult(null)
        try {
          const resp = await fetch(`${API_BASE}/runs/${row.taxonomy}/${encodeURIComponent(row.name)}/commands/execute`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ action_id: action.id }),
          })
          const data = await resp.json()
          if (!resp.ok) throw new Error(data.detail || 'Failed to execute command')
          setExecutionResult(data)
          await Promise.all([
            fetchRuns(),
            loadOperatorMatrix().then(setMatrixRows).catch(() => {}),
            loadRecentExecutions().then(setRecentExecutions).catch(() => {}),
          ])
          if (selectedRun === row.name || targetRun === row.name) {
            const [refreshedDetail, historyData] = await Promise.all([
              loadRunDetail(row.taxonomy, row.name),
              loadHistory(row.taxonomy, row.name),
            ])
            setDetail(refreshedDetail)
            setTargetDetail(refreshedDetail)
            setHistory(historyData)
          }
        } catch (error) {
          setExecutionResult({
            action_id: action.id,
            command: action.command,
            status: 'FAILED',
            exit_code: -1,
            stdout: '',
            stderr: error instanceof Error ? error.message : 'Failed to execute command',
          })
        } finally {
          finishRunExecution(row.taxonomy, row.name)
        }
      },
    })
  }

  const invokeCodexPreset = async (
    presetId: CodexBridgeResult['preset_id'],
    taxonomy: string,
    runName: string,
  ) => {
    setCodexTargetKey(`${taxonomy}:${runName}`)
    setCodexLoadingPreset(presetId)
    setCodexError(null)
    setCodexResult(null)
    try {
      const resp = await fetch(`${API_BASE}/runs/${taxonomy}/${encodeURIComponent(runName)}/codex-bridge`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ preset_id: presetId }),
      })
      const data = await resp.json()
      if (!resp.ok) {
        if (typeof data.detail === 'string') throw new Error(data.detail)
        throw new Error(JSON.stringify(data.detail ?? data))
      }
      setCodexResult(data)
    } catch (error) {
      setCodexError(error instanceof Error ? error.message : 'Failed to invoke Codex bridge')
    } finally {
      setCodexLoadingPreset(null)
    }
  }

  const filteredRuns = runs.filter((run) => run.name.toLowerCase().includes(searchTerm.toLowerCase()))
  const detailActions = targetDetail?.operator_actions ?? []
  const executableActions = detailActions.filter((action) => action.execution_type !== 'human')
  const humanActions = detailActions.filter((action) => action.execution_type === 'human')
  const childRuns = detail?.children ?? []
  const matchingMatrixRows = matrixRows.filter((row) => row.name.toLowerCase().includes(searchTerm.toLowerCase()))
  const activePhases = new Set(['PLAN_NEEDED', 'BUILD_NEEDED', 'REVIEW_NEEDED', 'IMPROVE_NEEDED', 'RESULT_NEEDED'])
  const recentRunNames = new Set(recentExecutions.map((job) => job.run_name))
  const filteredRecentExecutions = recentExecutions.filter((job) =>
    job.run_name.toLowerCase().includes(jobsSearchTerm.toLowerCase()),
  )
  const operatorRows = matchingMatrixRows.filter((row) => {
    if (operatorFilter === 'all') return true
    if (operatorFilter === 'recent') return recentRunNames.has(row.name)
    return activePhases.has(row.phase)
  }).slice(0, 10)
  const activeTargetName = targetDetail?.name ?? detail?.name ?? ''
  const activeChildName = detail && activeTargetName !== detail.name ? activeTargetName : null
  const getCodexPresetsForPhase = (phase: string) =>
    (Object.entries(CODEX_PRESET_RULES) as Array<[CodexBridgeResult['preset_id'], (typeof CODEX_PRESET_RULES)[keyof typeof CODEX_PRESET_RULES]]>)
      .filter(([, rule]) => rule.allowedPhases.has(phase))
  const targetTabs = detail
    ? [
        { name: detail.name, label: 'Parent' },
        ...childRuns.map((child) => ({ name: child.name, label: child.child_name })),
      ]
    : []
  const targetReworkCount = [
    (targetDetail?.artifacts ?? detail?.artifacts ?? []).some((a) => a.name === 'plan_review.md' && a.exists),
    (targetDetail?.artifacts ?? detail?.artifacts ?? []).some((a) => a.name === 'build_review.md' && a.exists),
    (targetDetail?.artifacts ?? detail?.artifacts ?? []).some((a) => a.name === 'review_review.md' && a.exists),
    (targetDetail?.artifacts ?? detail?.artifacts ?? []).some((a) => a.name === 'improve_review.md' && a.exists),
  ].filter(Boolean).length

  useEffect(() => {
    if (!targetDetail || !selectedTaxonomy || !targetRun || selectedArtifact) return

    if (!DEFAULT_PREVIEW_PHASES.has(targetDetail.phase)) {
      return
    }

    const preferred = [TRANSCRIPT_ARTIFACT, RESULT_ARTIFACT].find((name) =>
      (targetDetail.artifacts ?? []).some((artifact) => artifact.name === name && artifact.exists),
    )

    if (!preferred) {
      return
    }

    void fetchArtifact(preferred)
  }, [targetDetail, selectedArtifact, selectedTaxonomy, targetRun])

  const renderOperatorAction = (
    action: OperatorAction,
    mode: 'manual' | 'executable',
    taxonomy: string,
    runName: string,
  ) => {
    const comment = rerunComments[action.id] ?? ''
    const isSaved = savedCommentByAction[action.id] === comment.trim() && comment.trim() !== ''
    const canExecute = action.execution_type !== 'human' && action.enabled && (!action.requires_comment || isSaved)
    const runningActionId = executingActionForRun(taxonomy, runName)
    const isRunning = runningActionId === action.id
    const runBusy = runningActionId !== null

    return (
      <div
        key={action.id}
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
                if (savedCommentByAction[action.id] && savedCommentByAction[action.id] !== next.trim()) {
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
          {isRunning ? 'Running...' : action.execution_type === 'human' ? 'Human Guidance Only' : 'Execute'}
        </button>
      </div>
    )
  }

  return (
    <div className="flex h-screen overflow-hidden bg-zinc-950 text-zinc-100">
      <aside className="w-72 min-w-[18rem] shrink-0 border-r border-zinc-800 p-4 overflow-y-auto xl:w-80">
        <div className="mb-4 flex items-center gap-2">
          <Activity size={20} className="text-indigo-400" />
          <h1 className="text-lg font-bold">APSF Viewer</h1>
        </div>
        <div className="relative mb-4">
          <Search size={16} className="absolute left-3 top-2.5 text-zinc-500" />
          <input
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full rounded border border-zinc-800 bg-zinc-900 py-2 pl-9 pr-3 text-sm"
            placeholder="Search runs..."
          />
        </div>
        <div className="space-y-2">
          {isLoadingRuns ? (
            Array.from({ length: 8 }).map((_, i) => (
              <div key={i} className="h-24 w-full animate-pulse rounded border border-zinc-800 bg-zinc-900/20" />
            ))
          ) : runsError ? (
            <div className="rounded border border-red-500/30 bg-red-500/10 p-4 text-sm text-red-200">
              <div className="font-semibold">Failed to load runs</div>
              <div className="mt-1 text-xs text-red-200/80">{runsError}</div>
              <button
                onClick={() => {
                  setIsLoadingRuns(true)
                  void fetchRuns()
                }}
                className="mt-3 rounded border border-red-400/40 bg-red-500/10 px-3 py-1.5 text-xs font-bold text-red-100"
              >
                Retry
              </button>
            </div>
          ) : filteredRuns.length === 0 ? (
            <div className="py-12 text-center text-xs text-zinc-600">No runs found.</div>
          ) : (
            filteredRuns.map((run) => (
              <button
                key={`${run.taxonomy}-${run.name}`}
                onClick={() => void fetchDetail(run.taxonomy, run.name)}
                className={`w-full rounded border p-3 text-left ${selectedRun === run.name ? 'border-indigo-500/40 bg-indigo-500/10' : 'border-zinc-800 bg-zinc-900/40 hover:bg-zinc-900'}`}
              >
                <div className="mb-2 text-xs text-zinc-500">{run.taxonomy}</div>
                <div className="mb-2 break-words text-sm font-medium">{run.name}</div>
                <div className="mb-2 text-[11px] text-zinc-500">Next: {run.next_role}</div>
                <div className="flex flex-wrap items-center gap-1">
                  <PhaseBadge phase={run.phase} />
                  <PriorityBadge priority={run.priority} />
                  <CountBadge count={run.child_count} />
                  <ReworkBadge count={[run.has_plan_review, run.has_build_review, run.has_review_review, run.has_improve_review].filter(Boolean).length} />
                </div>
              </button>
            ))
          )}
        </div>
      </aside>

      <main className="flex min-w-0 flex-1 flex-col overflow-hidden 2xl:flex-row">
        {!detail ? (
          <div className="flex flex-1 items-center justify-center text-zinc-500 font-medium">Select a run from the list to view details.</div>
        ) : (
          <>
            <section
              onScroll={(e) => handleWorkspaceScroll(e.currentTarget.scrollTop)}
              className={`min-h-0 min-w-0 border-b border-zinc-800 p-4 overflow-y-auto 2xl:border-b-0 ${workspaceTab === 'detail' ? 'xl:w-[28rem] xl:shrink-0 xl:border-r 2xl:w-[min(36rem,35vw)]' : 'flex-1'}`}
            >
              <div className={`sticky top-0 z-20 -mx-4 mb-4 border-b border-zinc-800 bg-zinc-950/95 px-4 backdrop-blur transition-all duration-300 ${headerCompact ? 'pb-2' : 'pb-4'}`}>
                {/* Stable Core: Badges and Title */}
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0 flex-1">
                    <div className="mb-2 flex flex-wrap items-center gap-2">
                      <PhaseBadge phase={targetDetail?.phase ?? detail.phase} />
                      <PriorityBadge priority={targetDetail?.priority ?? detail.priority} />
                      {headerCompact && targetDetail && targetDetail.name !== detail.name && (
                        <span className="flex items-center gap-1 rounded bg-indigo-500/25 border border-indigo-500/40 px-1.5 py-0.5 font-bold text-indigo-100 text-[10px]">
                          <Terminal size={10} />
                          CHILD
                        </span>
                      )}
                    </div>
                    <div className="flex flex-col min-w-0">
                      <span className={`mb-0.5 truncate leading-tight text-zinc-500 transition-all duration-300 ${headerCompact ? 'text-[10px]' : 'text-xs'}`} title={targetDetail?.name ?? detail.name}>
                        {(targetDetail?.name ?? detail.name).split('_')[0]}
                      </span>
                      <h2 className={`truncate font-bold leading-snug transition-all duration-300 ${headerCompact ? 'text-base' : 'text-lg'}`}>
                        {(targetDetail?.name ?? detail.name).split('_').slice(1).join('_') || (targetDetail?.name ?? detail.name)}
                      </h2>
                    </div>
                  </div>
                </div>

                {/* Always Visible but Compactable: Workflow Progress */}
                <WorkflowProgress
                  phase={targetDetail?.phase ?? detail.phase}
                  hasPlanReview={(targetDetail?.artifacts ?? detail.artifacts).some((a) => a.name === 'plan_review.md' && a.exists)}
                  hasBuildReview={(targetDetail?.artifacts ?? detail.artifacts).some((a) => a.name === 'build_review.md' && a.exists)}
                  hasReviewReview={(targetDetail?.artifacts ?? detail.artifacts).some((a) => a.name === 'review_review.md' && a.exists)}
                  hasImproveReview={(targetDetail?.artifacts ?? detail.artifacts).some((a) => a.name === 'improve_review.md' && a.exists)}
                  compact={headerCompact}
                />

                {/* Condensed Command View (Visible when compact) */}
                <div className={`mt-1 flex items-center justify-between rounded border border-indigo-500/20 bg-indigo-500/5 px-2 py-1 transition-all duration-500 ${headerCompact ? 'opacity-100 max-h-10' : 'opacity-0 max-h-0 overflow-hidden mt-0 border-none'}`}>
                   <div className="flex items-center gap-2 text-indigo-300 min-w-0">
                     <Terminal size={12} />
                     <span className="truncate font-mono text-[10px]">{targetDetail?.operator_command ?? ''}</span>
                   </div>
                   <CopyButton text={targetDetail?.operator_command ?? ''} />
                </div>

                {/* Collapsible Supplemental Section (Hidden when compact) */}
                <div className={`overflow-hidden transition-all duration-500 ease-in-out ${headerCompact ? 'max-h-0 opacity-0 pointer-events-none' : 'max-h-[600px] opacity-100'}`}>
                  <div className="mt-2 flex flex-wrap items-center gap-2 text-xs text-zinc-400">
                    <span>Next: {targetDetail?.next_role ?? detail.next_role}</span>
                    {targetDetail && targetDetail.name !== detail.name && (
                      <span className="flex items-center gap-1 rounded bg-indigo-500/25 border border-indigo-500/40 px-2 py-0.5 font-bold text-indigo-100 shadow-[0_0_10px_rgba(99,102,241,0.2)]">
                        <Terminal size={10} />
                        VIEWING CHILD
                      </span>
                    )}
                  </div>
                  {(() => {
                    const parsed = parseSatisfiabilityReason(targetDetail?.decision_reason ?? detail.decision_reason)
                    return parsed.primary ? (
                      <p className="mt-2 text-sm text-zinc-500 line-clamp-2">{parsed.primary}</p>
                    ) : null
                  })()}
                  <SatisfiabilityWarning reason={targetDetail?.decision_reason ?? detail.decision_reason} />
                  
                  {/* Full Command View */}
                  <div className="mt-3 rounded border border-indigo-500/30 bg-indigo-500/10 p-3">
                    <div className="mb-2 flex items-center justify-between">
                      <div className="flex items-center gap-2 text-indigo-300">
                        <Terminal size={14} />
                        <span className="text-xs font-bold uppercase">
                          Primary Command
                          {targetDetail && (
                            <span className="ml-2 rounded bg-zinc-800 px-1.5 py-0.5 text-[10px] text-zinc-300">
                              {targetDetail.name === detail.name ? 'PARENT' : targetDetail.name.split('/').slice(-1)[0]}
                            </span>
                          )}
                        </span>
                      </div>
                      <CopyButton text={targetDetail?.operator_command ?? ''} />
                    </div>
                    <div className="whitespace-pre-wrap break-words rounded bg-black/30 p-2 font-mono text-xs line-clamp-2">{targetDetail?.operator_command ?? ''}</div>
                  </div>

                  {targetTabs.length > 1 && (
                    <div className="mt-4 space-y-2 pb-1">
                      <div className="text-[11px] font-bold uppercase tracking-[0.2em] text-zinc-500">Current View</div>
                      <div className="flex flex-wrap gap-2">
                        {targetTabs.map((tab) => (
                          <button
                            key={tab.name}
                            onClick={() => void fetchTargetDetail(detail.taxonomy, tab.name)}
                            className={`rounded border px-3 py-1.5 text-xs font-bold ${
                              targetRun === tab.name
                                ? 'border-indigo-400 bg-indigo-500/20 text-indigo-100'
                                : 'border-zinc-700 bg-zinc-900 text-zinc-300'
                            }`}
                          >
                            {targetRun === tab.name ? `Viewing ${tab.label}` : `Open ${tab.label}`}
                          </button>
                        ))}
                      </div>
                    </div>
                  )}
                </div>

                {/* Fixed Tab Bar Region */}
                <div className="mt-2 flex items-center gap-2 border-t border-zinc-800/70 pt-2">
                  <button
                    onClick={() => setWorkspaceTab('detail')}
                    className={`rounded border px-3 py-1.5 text-xs font-bold transition-all duration-200 ${workspaceTab === 'detail' ? 'border-indigo-400 bg-indigo-500/20 text-indigo-100' : 'border-zinc-700 bg-zinc-900 text-zinc-300 hover:bg-zinc-800'}`}
                  >
                    Run Detail
                  </button>
                  <button
                    onClick={() => setWorkspaceTab('management')}
                    className={`rounded border px-3 py-1.5 text-xs font-bold transition-all duration-200 ${workspaceTab === 'management' ? 'border-indigo-400 bg-indigo-500/20 text-indigo-100' : 'border-zinc-700 bg-zinc-900 text-zinc-300 hover:bg-zinc-800'}`}
                  >
                    Run Management
                  </button>
                  <button
                    onClick={() => setWorkspaceTab('activity')}
                    className={`rounded border px-3 py-1.5 text-xs font-bold transition-all duration-200 ${workspaceTab === 'activity' ? 'border-indigo-400 bg-indigo-500/20 text-indigo-100' : 'border-zinc-700 bg-zinc-900 text-zinc-300 hover:bg-zinc-800'}`}
                  >
                    Activity
                  </button>
                </div>
              </div>

              {workspaceTab === 'detail' ? (
                <div className="space-y-4">
                  <div className="grid gap-4 xl:grid-cols-2">
                    <div className="rounded border border-zinc-800 bg-zinc-900/40 p-4">
                      <div className="mb-2 text-[11px] font-bold uppercase tracking-[0.2em] text-zinc-500">Current Target</div>
                      <div className="flex flex-col items-start gap-2">
                        <div className="flex flex-wrap items-center gap-2">
                          <PhaseBadge phase={targetDetail?.phase ?? detail.phase} />
                          <PriorityBadge priority={targetDetail?.priority ?? detail.priority} />
                        </div>
                        {targetReworkCount > 0 && <ReworkBadge count={targetReworkCount} />}
                      </div>
                      <div className="mt-3 text-sm font-semibold text-zinc-100">{targetDetail?.name ?? detail.name}</div>
                      <div className="mt-1 text-xs text-zinc-400">Next: {targetDetail?.next_role ?? detail.next_role}</div>
                      {(() => {
                        const parsed = parseSatisfiabilityReason(targetDetail?.decision_reason ?? detail.decision_reason)
                        return parsed.primary ? (
                          <p className="mt-3 text-sm text-zinc-400">{parsed.primary}</p>
                        ) : null
                      })()}
                      <SatisfiabilityWarning reason={targetDetail?.decision_reason ?? detail.decision_reason} />
                    </div>

                    <div className="rounded border border-zinc-800 bg-zinc-900/40 p-4">
                      <div className="mb-2 text-[11px] font-bold uppercase tracking-[0.2em] text-zinc-500">Run Topology</div>
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="rounded border border-emerald-500/30 bg-emerald-500/10 px-2 py-0.5 text-[10px] font-bold text-emerald-300">
                          {childRuns.length} child run{childRuns.length === 1 ? '' : 's'}
                        </span>
                        {activeChildName && (
                          <span className="rounded border border-indigo-500/30 bg-indigo-500/10 px-2 py-0.5 text-[10px] font-bold text-indigo-300">
                            viewing child
                          </span>
                        )}
                      </div>
                      {childRuns.length > 0 ? (
                        <div className="mt-3 space-y-2">
                          {childRuns.slice(0, 4).map((child) => (
                            <div key={child.name} className="flex items-center justify-between gap-3 rounded border border-zinc-800 bg-black/20 px-3 py-2">
                              <div className="min-w-0">
                                <div className="truncate text-xs font-semibold text-zinc-200">{child.child_name}</div>
                                <div className="truncate text-[11px] text-zinc-500">{child.phase} / {child.next_role}</div>
                              </div>
                              <button
                                onClick={() => void fetchTargetDetail(detail.taxonomy, child.name)}
                                className="rounded border border-zinc-700 bg-zinc-900 px-2 py-1 text-[10px] font-bold text-zinc-200"
                              >
                                Open
                              </button>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <div className="mt-3 text-xs text-zinc-500">No child runs for this target.</div>
                      )}
                    </div>
                  </div>

                  {history && (history.latest_execution || history.latest_rerun_comment) && (
                    <div className="rounded border border-emerald-500/20 bg-emerald-500/5 p-4">
                      <div className="mb-3 text-[11px] font-bold uppercase tracking-[0.2em] text-emerald-300">Latest Persisted Activity</div>
                      <div className="grid gap-3 xl:grid-cols-2">
                        {history.latest_execution ? (
                          <div className="rounded border border-zinc-800 bg-black/20 p-3">
                            <div className="mb-1 text-[10px] font-bold uppercase tracking-[0.2em] text-zinc-500">Execution</div>
                            <div className="flex items-center gap-2">
                              <span className="rounded bg-zinc-900 px-2 py-0.5 text-[10px] font-bold text-zinc-300">{history.latest_execution.action_id}</span>
                              <PhaseBadge phase={history.latest_execution.result_status} />
                            </div>
                            <div className="mt-2 text-xs text-zinc-400">{history.latest_execution.triggered_at}</div>
                          </div>
                        ) : (
                          <div className="rounded border border-zinc-800 bg-black/20 p-3 text-xs text-zinc-500">No execution history yet.</div>
                        )}

                        {history.latest_rerun_comment ? (
                          <div className="rounded border border-zinc-800 bg-black/20 p-3">
                            <div className="mb-1 text-[10px] font-bold uppercase tracking-[0.2em] text-zinc-500">Rerun Comment</div>
                            <div className="text-xs text-zinc-400">{history.latest_rerun_comment.comment_artifact}</div>
                            <div className="mt-2 line-clamp-3 whitespace-pre-wrap text-xs text-zinc-300">{history.latest_rerun_comment.comment_body}</div>
                          </div>
                        ) : (
                          <div className="rounded border border-zinc-800 bg-black/20 p-3 text-xs text-zinc-500">No rerun comment history yet.</div>
                        )}
                      </div>
                    </div>
                  )}

                  {executableActions.length > 0 && selectedTaxonomy && targetDetail && (
                    <div className="space-y-3">
                      <div className="text-[11px] font-bold uppercase tracking-[0.2em] text-zinc-500">Run Actions</div>
                      {executableActions.map((action) => renderOperatorAction(action, 'executable', selectedTaxonomy, targetDetail.name))}
                    </div>
                  )}

                  {humanActions.length > 0 && selectedTaxonomy && targetDetail && (
                    <div className="space-y-3">
                      <div className="pt-2 text-[11px] font-bold uppercase tracking-[0.2em] text-zinc-500">Run Manual Steps</div>
                      {humanActions.map((action) => renderOperatorAction(action, 'manual', selectedTaxonomy, targetDetail.name))}
                    </div>
                  )}
                </div>
              ) : workspaceTab === 'management' ? (
                <div className="space-y-4">
                  <div className="rounded border border-zinc-800 bg-zinc-900/40 p-4">
                    <div className="mb-3 flex items-center justify-between gap-3">
                      <div>
                        <div className="text-[11px] font-bold uppercase tracking-[0.2em] text-zinc-500">Execution Matrix</div>
                        <div className="mt-1 text-xs text-zinc-400">Operator shortcuts for top-level runs.</div>
                      </div>
                      <div className="flex items-center gap-2">
                        {(['active', 'recent', 'all'] as const).map((filter) => (
                          <button
                            key={filter}
                            onClick={() => setOperatorFilter(filter)}
                            className={`rounded border px-2.5 py-1 text-[10px] font-bold uppercase ${operatorFilter === filter ? 'border-indigo-400 bg-indigo-500/20 text-indigo-100' : 'border-zinc-700 bg-zinc-900 text-zinc-400'}`}
                          >
                            {filter}
                          </button>
                        ))}
                      </div>
                    </div>
                    <div className="space-y-3">
                      {operatorRows.map((row) => (
                        <div key={row.name} className="rounded border border-zinc-800 bg-black/20 p-3">
                          <div className="mb-2 flex items-center justify-between gap-2">
                            <div className="min-w-0">
                              <div className="truncate text-[11px] text-zinc-500">{row.taxonomy}</div>
                              <div className="truncate text-sm font-semibold text-zinc-100" title={row.name}>{row.name}</div>
                            </div>
                            <div className="flex items-center gap-1">
                              <PhaseBadge phase={row.phase} />
                              <PriorityBadge priority={row.priority} />
                            </div>
                          </div>
                          <div className="mb-3 flex items-center justify-between gap-3">
                            <div className="text-xs text-zinc-500">Open the run for full detail, or operate directly from this card.</div>
                            <button
                              onClick={() => void fetchDetail(row.taxonomy, row.name)}
                              className="rounded border border-zinc-700 bg-zinc-950 px-2.5 py-1 text-[10px] font-bold text-zinc-200"
                            >
                              Open Run Detail
                            </button>
                          </div>
                          <div className="grid grid-cols-4 gap-2">
                            {[
                              { label: 'Plan', action: row.plan_action },
                              { label: 'Build', action: row.build_action },
                              { label: 'Review', action: row.review_action },
                              { label: 'Rerun', action: row.rerun_action },
                            ].map(({ label, action }) => {
                              const typedAction = action as OperatorAction | null | undefined
                              const isRunning = executingActionForRun(row.taxonomy, row.name) === typedAction?.id
                              return (
                                <button
                                  key={`${row.name}-${label}`}
                                  onClick={() => typedAction && void executeMatrixAction(row, typedAction)}
                                  disabled={!typedAction || !typedAction.enabled || isRunExecuting(row.taxonomy, row.name)}
                                  className={`rounded border px-2 py-1.5 text-[11px] font-bold ${
                                    isRunning
                                      ? 'animate-pulse border-red-400 bg-red-500/25 text-red-50'
                                      : typedAction?.primary
                                        ? 'border-indigo-500/40 bg-indigo-500/15 text-indigo-200 disabled:border-zinc-800 disabled:bg-zinc-900 disabled:text-zinc-600'
                                        : 'border-zinc-700 bg-zinc-950 text-zinc-300 disabled:border-zinc-800 disabled:bg-zinc-900 disabled:text-zinc-600'
                                  }`}
                                >
                                  {isRunning ? 'Running...' : label}
                                </button>
                              )
                            })}
                          </div>

                          <div className="mt-3 rounded border border-cyan-500/20 bg-cyan-500/5 p-3">
                            <div className="mb-2 flex items-center justify-between gap-3">
                              <div className="text-[10px] font-bold uppercase tracking-[0.2em] text-cyan-300">Codex Advisory</div>
                              <div className="text-[10px] text-zinc-500">per run</div>
                            </div>

                            {getCodexPresetsForPhase(row.phase).length > 0 ? (
                              <div className="flex flex-wrap gap-2">
                                {getCodexPresetsForPhase(row.phase).map(([presetId, preset]) => (
                                  <button
                                    key={`${row.name}-${presetId}`}
                                    onClick={() => void invokeCodexPreset(presetId, row.taxonomy, row.name)}
                                    disabled={codexLoadingPreset !== null || isRunExecuting(row.taxonomy, row.name)}
                                    className="rounded border border-cyan-500/30 bg-zinc-950/80 px-3 py-1.5 text-left text-[11px] font-bold text-cyan-200 disabled:border-zinc-800 disabled:bg-zinc-900 disabled:text-zinc-500"
                                    title={preset.description}
                                  >
                                    {codexLoadingPreset === presetId && codexTargetKey === `${row.taxonomy}:${row.name}` ? 'Running...' : preset.label}
                                  </button>
                                ))}
                              </div>
                            ) : (
                              <div className="text-xs text-zinc-500">No advisory preset for this phase.</div>
                            )}

                            {codexTargetKey === `${row.taxonomy}:${row.name}` && codexError && (
                              <div className="mt-3 rounded border border-red-500/30 bg-red-500/10 p-3 text-xs text-red-200">
                                {codexError}
                              </div>
                            )}

                            {codexTargetKey === `${row.taxonomy}:${row.name}` && codexResult && (
                              <div className="mt-3 rounded border border-zinc-800 bg-zinc-950/70 p-3">
                                <div className="mb-2 flex items-center justify-between gap-3">
                                  <div className="text-xs font-semibold text-zinc-200">{CODEX_PRESET_RULES[codexResult.preset_id].label}</div>
                                  <CodexStatusBadge status={codexResult.status} />
                                </div>
                                <div className="text-sm text-zinc-200">{codexResult.summary}</div>
                                {codexResult.next_steps.length > 0 && (
                                  <ul className="mt-3 list-disc space-y-1 pl-5 text-xs text-zinc-300">
                                    {codexResult.next_steps.map((step, index) => (
                                      <li key={`${row.name}-${codexResult.preset_id}-${index}`}>{step}</li>
                                    ))}
                                  </ul>
                                )}
                              </div>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                </div>
              ) : (
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
                    <div className={`rounded border ${executionResult.status === 'FAILED' ? 'border-red-500/50 bg-red-500/5' : 'border-zinc-800 bg-zinc-900/40'} p-3 animate-in fade-in slide-in-from-bottom-2`}>
                      <div className="mb-2 flex items-center justify-between">
                        <div className={`text-xs font-bold ${executionResult.status === 'FAILED' ? 'text-red-400' : 'text-zinc-300'}`}>
                          {executionResult.status === 'FAILED' ? 'ERROR: ' : ''}Execution Result
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
                      
                      {executionResult.status === 'FAILED' && (
                        <div className="mb-2 rounded bg-red-500/20 px-2 py-1 text-[10px] font-bold text-red-200">
                          Operation failed. Check the logs below for details.
                        </div>
                      )}

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
              )}
            </section>

            {workspaceTab === 'detail' && (
            <section className="min-h-0 shrink-0 border-b border-zinc-800 p-4 overflow-y-auto xl:w-72 xl:border-b-0 xl:border-r 2xl:w-80">
              <div className="sticky top-0 z-10 -mx-4 mb-3 border-b border-zinc-800 bg-zinc-950/95 px-4 pb-3 backdrop-blur">
                <div className="mb-3 flex items-center justify-between">
                  <div className="text-xs font-bold uppercase text-zinc-500">Artifacts</div>
                  {targetDetail && (
                    <div className="rounded bg-zinc-900 px-2 py-1 text-[10px] font-bold text-zinc-400">
                      {targetDetail.name === detail.name ? 'PARENT' : targetDetail.name.split('/').slice(-1)[0]}
                    </div>
                  )}
                </div>

                {/* Readiness hint: shown when the expected artifact exists but phase still requires it */}
                {(() => {
                  const phase = targetDetail?.phase
                  const expectedArtifact = phase ? PHASE_TO_ARTIFACT[phase] : null
                  if (!expectedArtifact) return null
                  const artifact = (targetDetail?.artifacts ?? []).find((a) => a.name === expectedArtifact)
                  if (!artifact?.exists) return null
                  const reason = targetDetail?.decision_reason
                  if (!reason) return null
                  const parsed = parseSatisfiabilityReason(reason)
                  const label = splitArtifactLabel(expectedArtifact)
                  return (
                    <div className="rounded border border-amber-500/20 bg-amber-500/5 p-2.5">
                      <div className="mb-1 text-[10px] font-bold uppercase tracking-[0.2em] text-amber-400">Readiness Note</div>
                      {parsed.primary ? (
                        <div className="text-xs text-amber-200/70">{parsed.primary}</div>
                      ) : null}
                      <SatisfiabilityWarning reason={reason} />
                      <div className="mt-2 rounded border border-amber-500/15 bg-black/20 p-2">
                        <div className="text-[10px] uppercase tracking-wide text-amber-300/60">Focus Artifact</div>
                        <div className="mt-1 text-xs font-semibold text-amber-100">
                          <span className="text-amber-300/60">{label.prefix}</span>
                          <span>{label.suffix || expectedArtifact}</span>
                        </div>
                        <div className="mt-1 text-[10px] text-amber-300/60">
                          This file exists, but the current phase still suggests it may need stronger content before the run is ready.
                        </div>
                      </div>
                    </div>
                  )
                })()}
              </div>

              <div className="space-y-2">
                {(targetDetail?.artifacts ?? []).map((artifact) => (
                  (() => {
                    const label = splitArtifactLabel(artifact.name)
                    return (
                      <button
                        key={artifact.name}
                        disabled={!artifact.exists}
                        onClick={() => void fetchArtifact(artifact.name)}
                        className={`flex w-full items-center justify-between rounded border p-2 text-left ${selectedArtifact === artifact.name ? 'border-indigo-400/60 bg-indigo-500/20 text-indigo-50' : 'border-zinc-800 bg-zinc-900/30'} ${!artifact.exists ? 'opacity-40' : ''}`}
                      >
                        <div className="flex items-center gap-2 overflow-hidden">
                          <FileText size={14} />
                          <div className="min-w-0">
                            {label.prefix && (
                              <div className={`truncate text-[10px] uppercase tracking-wide text-zinc-500 ${selectedArtifact === artifact.name ? 'text-indigo-200/70' : ''}`} title={artifact.name}>
                                {label.prefix}
                              </div>
                            )}
                            <div className={`truncate text-xs ${selectedArtifact === artifact.name ? 'font-semibold' : ''}`} title={artifact.name}>
                              {label.suffix || artifact.name}
                            </div>
                          </div>
                        </div>
                      </button>
                    )
                  })()
                ))}
              </div>
            </section>
            )}

            <section className={`min-h-0 min-w-0 overflow-y-auto p-6 ${workspaceTab === 'detail' ? 'flex-1' : 'hidden lg:hidden'}`}>
              {selectedArtifact ? (
                <>
                  <div className="sticky top-0 z-10 -mx-6 mb-4 border-b border-zinc-800 bg-zinc-950/95 px-6 py-3 text-sm font-semibold backdrop-blur">
                    {selectedArtifact}
                  </div>
                  <div className="prose prose-invert prose-zinc max-w-none">
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>{artifactContent}</ReactMarkdown>
                  </div>
                </>
              ) : (
                <div className="flex h-full items-center justify-center text-zinc-500">Select an artifact to preview.</div>
              )}
            </section>
          </>
        )}
      </main>

      {modalConfig && <ConfirmModal config={modalConfig} onCancel={() => setModalConfig(null)} />}
      {selectedExecutionLog && <ExecutionLogModal job={selectedExecutionLog} onClose={() => setSelectedExecutionLog(null)} />}
    </div>
  )
}
