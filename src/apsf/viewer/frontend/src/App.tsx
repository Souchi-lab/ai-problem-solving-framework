import { useCallback, useEffect, useRef, useState } from 'react'
import { Activity, ChevronLeft, ChevronRight, Clock, FileText, Pin, Search, Settings, Terminal } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import type {
  RunSummary,
  OperatorAction,
  RunDetail,
  MatrixRow,
  ExecutionResult,
  SaveCommentResult,
  ActionExecutionRecord,
  RunHistory,
  ViewerConfig,
  CodexBridgeResult,
  ModalConfig,
  AgentOSActionFeedback,
  RunningExecutionState,
  AutoLoopStatus,
  RallyMessage,
  SpecialistCandidatesData,
  AgentOSInfo,
  CreateSpecialistResult,
} from './types'
import {
  formatDuration,
  formatRelativeTime,
  formatElapsedMs,
  parseSatisfiabilityReason,
  buildExecutionLogText,
  hasExecutionLogContent,
  formatAgentOSTimestamp,
  prettifyActionId,
  summarizeExecutionIntent,
  summarizeExecutionOutcome,
  loadStoredStringArray,
} from './utils/formatting'
import {
  getArtifactDisplayMeta,
} from './utils/artifacts'
import {
  parseSpecialistCodes,
  mergeCreatedSpecialistCandidate,
} from './utils/specialist'
import {
  PhaseBadge,
  AssignmentModeBadge,
  ReworkBadge,
  CountBadge,
  PriorityBadge,
  CodexStatusBadge,
  WorkflowProgress,
  SatisfiabilityWarning,
  CopyButton,
} from './components/badges'
import {
  ConfirmModal,
  SpecialistSelectionModal,
  AutoLoopLaunchModal,
  RallyConversationModal,
  CreateSpecialistModal,
  ViewerConfigModal,
  ExecutionLogModal,
  ArtifactReferenceModal,
} from './components/modals'
import {
  apiLoadRunDetail,
  apiLoadHistory,
  apiLoadOperatorMatrix,
  apiLoadRecentExecutions,
  apiLoadAgentOS,
  apiLoadSpecialistCandidates,
} from './api/runsApi'
import { apiLoadViewerConfig, apiUpdateViewerConfig } from './api/configApi'

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


const TAXONOMY_SECTION_ORDER = ['work', 'fw-improvement', 'sochi-blocks', 'legacy'] as const
const TAXONOMY_SECTION_LABELS: Record<string, string> = {
  work: 'Work',
  'fw-improvement': 'FW Improvement',
  'sochi-blocks': 'SoChi Blocks',
  legacy: 'Legacy',
}
const TAXONOMY_PIN_STORAGE_KEY = 'apsf.viewer.sidebar.pinnedTaxonomies'
const TAXONOMY_OPEN_STORAGE_KEY = 'apsf.viewer.sidebar.openTaxonomies'

export default function App() {
  const [runs, setRuns] = useState<RunSummary[]>([])
  const [matrixRows, setMatrixRows] = useState<MatrixRow[]>([])
  const [recentExecutions, setRecentExecutions] = useState<ActionExecutionRecord[]>([])
  const [workspaceTab, setWorkspaceTab] = useState<'detail' | 'management' | 'activity' | 'agent-os'>('agent-os')
  const [operatorFilter, setOperatorFilter] = useState<'active' | 'recent' | 'all'>('active')
  const [humanBlockerFilter, setHumanBlockerFilter] = useState<'all' | 'blocked'>('all')
  const [pinnedTaxonomies, setPinnedTaxonomies] = useState<string[]>(() => loadStoredStringArray(TAXONOMY_PIN_STORAGE_KEY, ['work']))
  const [openTaxonomies, setOpenTaxonomies] = useState<string[]>(() => loadStoredStringArray(TAXONOMY_OPEN_STORAGE_KEY, ['work', 'fw-improvement', 'sochi-blocks']))
  const [detail, setDetail] = useState<RunDetail | null>(null)
  const [selectedRun, setSelectedRun] = useState<string | null>(null)
  const [selectedTaxonomy, setSelectedTaxonomy] = useState<string | null>(null)
  const [targetRun, setTargetRun] = useState<string | null>(null)
  const [targetDetail, setTargetDetail] = useState<RunDetail | null>(null)
  const [selectedArtifact, setSelectedArtifact] = useState<string | null>(null)
  const [artifactContent, setArtifactContent] = useState<string>('')
  const [artifactModalOpen, setArtifactModalOpen] = useState(false)
  const [searchTerm, setSearchTerm] = useState('')
  const [jobsSearchTerm, setJobsSearchTerm] = useState('')
  const [executionResult, setExecutionResult] = useState<ExecutionResult | null>(null)
  const [selectedExecutionLog, setSelectedExecutionLog] = useState<ActionExecutionRecord | null>(null)
  const [saveCommentResult, setSaveCommentResult] = useState<SaveCommentResult | null>(null)
  const [phaseContextActionId, setPhaseContextActionId] = useState<string>('')
  const [history, setHistory] = useState<RunHistory | null>(null)
  const [historyRun, setHistoryRun] = useState<string | null>(null)
  const [viewerConfig, setViewerConfig] = useState<ViewerConfig | null>(null)
  const [viewerConfigSavingKey, setViewerConfigSavingKey] = useState<string | null>(null)
  const [viewerConfigModalOpen, setViewerConfigModalOpen] = useState(false)
  const [codexResult, setCodexResult] = useState<CodexBridgeResult | null>(null)
  const [codexError, setCodexError] = useState<string | null>(null)
  const [codexLoadingPreset, setCodexLoadingPreset] = useState<CodexBridgeResult['preset_id'] | null>(null)
  const [codexTargetKey, setCodexTargetKey] = useState<string | null>(null)
  const [modalConfig, setModalConfig] = useState<ModalConfig | null>(null)
  const [executingRuns, setExecutingRuns] = useState<Record<string, RunningExecutionState>>({})
  const [executionNow, setExecutionNow] = useState(() => Date.now())
  const [savingActionId, setSavingActionId] = useState<string | null>(null)
  const [rerunComments, setRerunComments] = useState<Record<string, string>>({})
  const [savedCommentByAction, setSavedCommentByAction] = useState<Record<string, string>>({})
  const [judgeChatOpen, setJudgeChatOpen] = useState(false)
  const [judgeChatMessages, setJudgeChatMessages] = useState<Array<{ role: 'user' | 'assistant'; content: string }>>([])
  const [judgeChatInput, setJudgeChatInput] = useState('')
  const [judgeChatLoading, setJudgeChatLoading] = useState(false)
  const [specialistCandidates, setSpecialistCandidates] = useState<SpecialistCandidatesData | null>(null)
  const [specialistModalOpen, setSpecialistModalOpen] = useState(false)
  const [createSpecialistModalOpen, setCreateSpecialistModalOpen] = useState(false)
  const [createdSpecialistResult, setCreatedSpecialistResult] = useState<CreateSpecialistResult | null>(null)
  const [specialistModalSelectedCode, setSpecialistModalSelectedCode] = useState<string | null>(null)
  const [agentOSData, setAgentOSData] = useState<AgentOSInfo | null>(null)
  const [agentOSLoading, setAgentOSLoading] = useState(false)
  const [selectedRecoveryCheckpointId, setSelectedRecoveryCheckpointId] = useState<string | null>(null)
  const [selectedRecoverySnapshotId, setSelectedRecoverySnapshotId] = useState<string | null>(null)
  const [selectedRecoveryApplyTraceId, setSelectedRecoveryApplyTraceId] = useState<string | null>(null)
  const [agentOSFeedback, setAgentOSFeedback] = useState<AgentOSActionFeedback | null>(null)
  const [autoLoopStatus, setAutoLoopStatus] = useState<AutoLoopStatus | null>(null)
  const [autoLoopLoading, setAutoLoopLoading] = useState(false)
  const [autoLoopMutating, setAutoLoopMutating] = useState<'start' | 'stop' | 'cancel' | null>(null)
  const [autoLoopLaunchModalOpen, setAutoLoopLaunchModalOpen] = useState(false)
  const [rallyModalOpen, setRallyModalOpen] = useState(false)
  const [rallyMessages, setRallyMessages] = useState<RallyMessage[]>([])
  const [rallyLoading, setRallyLoading] = useState(false)
  const [rallySpecialistCodes, setRallySpecialistCodes] = useState<{ planner: string; builder: string; critic: string }>({ planner: '', builder: '', critic: '' })
  const [isLoadingRuns, setIsLoadingRuns] = useState(true)
  const [runsError, setRunsError] = useState<string | null>(null)
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [currentViewOpen, setCurrentViewOpen] = useState(false)
  const detailRequestIdRef = useRef(0)
  const refreshRequestIdRef = useRef(0)
  const currentActiveDetail = targetDetail ?? detail
  const activeDetailPhase = currentActiveDetail?.phase ?? null
  const specialistPhaseOverride =
    currentActiveDetail?.phase === 'IMPROVE_NEEDED' && currentActiveDetail?.judge_recommendation?.suggested_return_phase
      ? currentActiveDetail.judge_recommendation.suggested_return_phase
      : null

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

  const loadRunDetail = apiLoadRunDetail
  const loadHistory = apiLoadHistory
  const loadOperatorMatrix = apiLoadOperatorMatrix
  const loadViewerConfig = apiLoadViewerConfig
  const loadRecentExecutions = apiLoadRecentExecutions

  const updateViewerConfig = async (patch: Partial<Pick<ViewerConfig, 'execution_mode' | 'cli_tool_mode' | 'build_max_turns' | 'run_detail_refresh_ms'>>) => {
    const savingKey = patch.execution_mode ? `execution:${patch.execution_mode}` : patch.cli_tool_mode ? `cli:${patch.cli_tool_mode}` : patch.build_max_turns !== undefined ? 'build_max_turns' : 'run_detail_refresh_ms'
    setViewerConfigSavingKey(savingKey)
    try {
      const data = await apiUpdateViewerConfig(patch)
      setViewerConfig(data)
      const [rows, recent] = await Promise.all([
        loadOperatorMatrix().catch(() => []),
        loadRecentExecutions().catch(() => []),
      ])
      setMatrixRows(rows)
      setRecentExecutions(recent)
      if (selectedRun && selectedTaxonomy) {
        const requestId = ++detailRequestIdRef.current
        const parentPromise = loadRunDetail(selectedTaxonomy, selectedRun)
        const historyTarget = targetRun ?? selectedRun
        const historyPromise = loadHistory(selectedTaxonomy, historyTarget)
        const targetPromise = targetRun ? loadRunDetail(selectedTaxonomy, targetRun) : parentPromise
        const [parentData, historyData, targetData] = await Promise.all([parentPromise, historyPromise, targetPromise])
        if (detailRequestIdRef.current === requestId) {
          setDetail(parentData)
          setHistory(historyData)
          setHistoryRun(historyTarget)
          setTargetDetail(targetRun ? targetData : null)
        }
      }
    } catch (error) {
      setModalConfig({
        title: 'Viewer Config Update Failed',
        message: error instanceof Error ? error.message : 'Failed to update viewer config.',
        confirmLabel: 'Close',
        cancelLabel: 'Dismiss',
        onConfirm: () => setModalConfig(null),
      })
    } finally {
      setViewerConfigSavingKey(null)
    }
  }

  const loadAgentOS = useCallback(apiLoadAgentOS, [])

  const refreshAgentOS = useCallback(async (taxonomy: string, runName: string) => {
    setAgentOSLoading(true)
    try {
      const data = await loadAgentOS(taxonomy, runName)
      setAgentOSData(data)
    } catch {
      setAgentOSData(null)
    } finally {
      setAgentOSLoading(false)
    }
  }, [loadAgentOS])

  const openAgentOSWorkspace = (taxonomy?: string | null, runName?: string | null) => {
    setWorkspaceTab('agent-os')
    if (taxonomy && runName) {
    void refreshAgentOS(taxonomy, runName)
    void loadSpecialistCandidates(taxonomy, runName, specialistPhaseOverride)
  }
  }

  const prevAutoLoopRunningRef = useRef<boolean | null>(null)
  const [loopStopToast, setLoopStopToast] = useState<{ stopReason: string | null; lastExit: number | null } | null>(null)

  const loadAutoLoopStatus = useCallback(async (taxonomy: string, runName: string) => {
    setAutoLoopLoading(true)
    try {
      const resp = await fetch(`${API_BASE}/runs/${taxonomy}/${encodeURIComponent(runName)}/auto-loop-status`)
      if (!resp.ok) {
        throw new Error(`Failed to load auto-loop status (${resp.status})`)
      }
      const data = await resp.json()
      const next: AutoLoopStatus = {
        running: Boolean(data.running),
        stop_pending: Boolean(data.stop_pending),
        stop_reason: typeof data.stop_reason === 'string' ? data.stop_reason : undefined,
        last_exit: typeof data.last_exit === 'number' ? data.last_exit : undefined,
      }
      // Detect running → stopped transition and fire toast
      if (prevAutoLoopRunningRef.current === true && !next.running) {
        setLoopStopToast({
          stopReason: next.stop_reason ?? null,
          lastExit: next.last_exit ?? null,
        })
      }
      prevAutoLoopRunningRef.current = next.running
      setAutoLoopStatus(next)
    } catch {
      setAutoLoopStatus(null)
    } finally {
      setAutoLoopLoading(false)
    }
  }, [])

  const startAutoLoop = useCallback(async (taxonomy: string, runName: string, buildScript?: string) => {
    setAutoLoopMutating('start')
    try {
      const resp = await fetch(`${API_BASE}/runs/${taxonomy}/${encodeURIComponent(runName)}/start-auto-loop`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(buildScript ? { build_script: buildScript } : {}),
      })
      const data = await resp.json().catch(() => ({}))
      if (!resp.ok) {
        throw new Error(typeof data.detail === 'string' ? data.detail : `Failed to start auto-loop (${resp.status})`)
      }
      await loadAutoLoopStatus(taxonomy, runName)
    } catch (error) {
      setModalConfig({
        title: 'Failed to Start Auto-Loop',
        message: error instanceof Error ? error.message : 'Failed to start auto-loop.',
        onConfirm: () => setModalConfig(null),
      })
    } finally {
      setAutoLoopMutating(null)
    }
  }, [loadAutoLoopStatus])

  const requestAutoLoopStop = useCallback(async (taxonomy: string, runName: string) => {
    setAutoLoopMutating('stop')
    try {
      const resp = await fetch(`${API_BASE}/runs/${taxonomy}/${encodeURIComponent(runName)}/request-stop`, { method: 'POST' })
      const data = await resp.json().catch(() => ({}))
      if (!resp.ok) {
        throw new Error(typeof data.detail === 'string' ? data.detail : `Failed to request stop (${resp.status})`)
      }
      await loadAutoLoopStatus(taxonomy, runName)
    } catch (error) {
      setModalConfig({
        title: 'Failed to Request Auto-Loop Stop',
        message: error instanceof Error ? error.message : 'Failed to request auto-loop stop.',
        onConfirm: () => setModalConfig(null),
      })
    } finally {
      setAutoLoopMutating(null)
    }
  }, [loadAutoLoopStatus])

  const cancelAutoLoopStop = useCallback(async (taxonomy: string, runName: string) => {
    setAutoLoopMutating('cancel')
    try {
      const resp = await fetch(`${API_BASE}/runs/${taxonomy}/${encodeURIComponent(runName)}/request-stop`, { method: 'DELETE' })
      const data = await resp.json().catch(() => ({}))
      if (!resp.ok) {
        throw new Error(typeof data.detail === 'string' ? data.detail : `Failed to cancel stop (${resp.status})`)
      }
      await loadAutoLoopStatus(taxonomy, runName)
    } catch (error) {
      setModalConfig({
        title: 'Failed to Cancel Stop Request',
        message: error instanceof Error ? error.message : 'Failed to cancel stop request.',
        onConfirm: () => setModalConfig(null),
      })
    } finally {
      setAutoLoopMutating(null)
    }
  }, [loadAutoLoopStatus])

  const loadSpecialistCandidates = async (taxonomy: string, runName: string, phaseOverride?: string | null): Promise<SpecialistCandidatesData | null> => {
    try {
      const data = await apiLoadSpecialistCandidates(taxonomy, runName, phaseOverride)
      setSpecialistCandidates(data)
      return data
    } catch {
      setSpecialistCandidates(null)
      return null
    }
  }

  const handleConfirmSpecialist = async (code: string) => {
    if (!selectedTaxonomy || !targetRun || !specialistCandidates) return
    const resp = await fetch(
      `${API_BASE}/runs/${selectedTaxonomy}/${encodeURIComponent(targetRun)}/confirm-specialist`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ role: specialistCandidates.role, specialist_code: code, source: 'operator-accept' }),
      }
    )
    const data = await resp.json().catch(() => ({} as { detail?: string; artifact_path?: string; target_run_name?: string }))
    if (!resp.ok) {
      throw new Error((data as { detail?: string }).detail || `HTTP ${resp.status}`)
    }
    setCreatedSpecialistResult(null)
    setSpecialistModalSelectedCode(code)
    await Promise.all([
      loadSpecialistCandidates(selectedTaxonomy, targetRun, specialistPhaseOverride),
      refreshAgentOS(selectedTaxonomy, targetRun),
      refreshRunContexts(selectedTaxonomy, targetRun),
    ])
    if (selectedArtifact === 'execution-assignment.md') {
      await fetchArtifact('execution-assignment.md')
    }
    setAgentOSFeedback({
      kind: 'success',
      title: 'Specialist Assignment Updated',
      detail: `Updated ${(data as { artifact_path?: string }).artifact_path || 'execution-assignment.md'} for ${(data as { target_run_name?: string }).target_run_name || targetRun}.`,
      actionId: 'act',
    })
    setSpecialistModalOpen(false)
  }

  const handleCreatedSpecialist = async (result: CreateSpecialistResult) => {
    if (!selectedTaxonomy || !targetRun) return
    setCreateSpecialistModalOpen(false)
    const refreshed = await loadSpecialistCandidates(selectedTaxonomy, targetRun, specialistPhaseOverride)
    const merged = mergeCreatedSpecialistCandidate(refreshed, result)
    if (merged) {
      setSpecialistCandidates(merged)
    }
    setCreatedSpecialistResult(result)
    setSpecialistModalSelectedCode(result.specialist_code)
    setSpecialistModalOpen(true)
  }

  const openSpecialistSelectionModal = async (initialCode?: string) => {
    if (!selectedTaxonomy || !targetRun) return
    const refreshed = await loadSpecialistCandidates(selectedTaxonomy, targetRun, specialistPhaseOverride)
    if (refreshed) {
      setSpecialistCandidates(refreshed)
      setSpecialistModalSelectedCode(initialCode ?? refreshed.current_code ?? '')
    } else {
      setSpecialistModalSelectedCode(initialCode ?? '')
    }
    setCreatedSpecialistResult(null)
    setSpecialistModalOpen(true)
  }

  const openSpecialistSelectionForPhase = async (phase: string) => {
    if (!selectedTaxonomy || !targetRun) return
    const refreshed = await loadSpecialistCandidates(selectedTaxonomy, targetRun, phase)
    if (refreshed) {
      setSpecialistCandidates(refreshed)
      setSpecialistModalSelectedCode(refreshed.current_code ?? '')
    } else {
      setSpecialistModalSelectedCode('')
    }
    setCreatedSpecialistResult(null)
    setSpecialistModalOpen(true)
  }

  const openAutoLoopLaunchModal = () => {
    setAutoLoopLaunchModalOpen(true)
  }

  const openRallyConversation = useCallback(async () => {
    if (!selectedTaxonomy || !targetRun) return
    const availableArtifacts = (targetDetail?.artifacts ?? detail?.artifacts ?? []).filter((artifact) => artifact.exists)
    const orderedArtifacts = [
      { name: 'goal.md', speaker: 'Result', title: 'Goal' },
      { name: 'plan.md', speaker: 'Judge', title: 'Plan' },
      { name: 'build.md', speaker: 'Builder', title: 'Build Report' },
      { name: 'build_review.md', speaker: 'Judge', title: 'Judge Feedback' },
      { name: 'review.md', speaker: 'Critic', title: 'Critic Comment' },
      { name: 'review_review.md', speaker: 'Judge', title: 'Judge Feedback' },
      { name: 'improve.md', speaker: 'Judge', title: 'Judge Decision' },
      { name: 'improve_review.md', speaker: 'Judge', title: 'Improve Feedback' },
      { name: 'result.md', speaker: 'Result', title: 'Closeout' },
    ]

    setRallyLoading(true)
    setRallyModalOpen(true)
    try {
      // Fetch specialist codes from execution-assignment.md in parallel
      const assignmentFetch = fetch(
        `${API_BASE}/runs/${selectedTaxonomy}/${encodeURIComponent(targetRun)}/artifacts/execution-assignment.md`
      )
        .then((r) => r.json())
        .catch(() => ({}))

      const [loaded, assignmentData] = await Promise.all([
        Promise.all(
          orderedArtifacts.map(async (item) => {
            const exists = availableArtifacts.some((artifact) => artifact.name === item.name)
            if (!exists) {
              return { artifact: item.name, speaker: item.speaker, title: item.title, content: '', exists: false } as RallyMessage
            }
            const resp = await fetch(`${API_BASE}/runs/${selectedTaxonomy}/${encodeURIComponent(targetRun)}/artifacts/${item.name}`)
            const data = await resp.json().catch(() => ({}))
            const raw = typeof data.content === 'string' ? data.content : ''
            return { artifact: item.name, speaker: item.speaker, title: item.title, content: raw, exists: raw.trim() !== '' } as RallyMessage
          })
        ),
        assignmentFetch,
      ])

      // Parse specialist codes
      const assignmentContent = typeof assignmentData.content === 'string' ? assignmentData.content : ''
      setRallySpecialistCodes(parseSpecialistCodes(assignmentContent))

      // Show existing artifacts + first pending artifact only
      const lastWrittenIndex = loaded.map((item) => item.exists).lastIndexOf(true)
      const firstPendingAfterWritten =
        lastWrittenIndex >= 0
          ? loaded.findIndex((item, index) => index > lastWrittenIndex && !item.exists)
          : loaded.findIndex((item) => !item.exists)
      const filtered = loaded.filter((item, index) => item.exists || index === firstPendingAfterWritten)
      setRallyMessages(filtered)
    } catch (error) {
      setRallyMessages([
        { artifact: 'system', speaker: 'Result', title: 'Load Error', content: error instanceof Error ? error.message : 'Failed to load rally.', exists: false },
      ])
    } finally {
      setRallyLoading(false)
    }
  }, [detail?.artifacts, selectedTaxonomy, targetDetail?.artifacts, targetRun])

  const makeRunKey = (taxonomy: string, runName: string) => `${taxonomy}:${runName}`
  const isRunExecuting = (taxonomy: string, runName: string) => executingRuns[makeRunKey(taxonomy, runName)] !== undefined
  const executingStateForRun = (taxonomy: string, runName: string) => executingRuns[makeRunKey(taxonomy, runName)] ?? null
  const executingActionForRun = (taxonomy: string, runName: string) => executingStateForRun(taxonomy, runName)?.actionId ?? null
  const startRunExecution = (taxonomy: string, runName: string, actionId: string) => {
    const runKey = makeRunKey(taxonomy, runName)
    setExecutingRuns((current) => ({ ...current, [runKey]: { actionId, startedAt: Date.now() } }))
    setExecutionNow(Date.now())
  }
  const finishRunExecution = (taxonomy: string, runName: string) => {
    const runKey = makeRunKey(taxonomy, runName)
    setExecutingRuns((current) => {
      const next = { ...current }
      delete next[runKey]
      return next
    })
  }

  useEffect(() => {
    if (Object.keys(executingRuns).length === 0 && !targetRun) return
    const timer = window.setInterval(() => setExecutionNow(Date.now()), 1000)
    return () => window.clearInterval(timer)
  }, [executingRuns, targetRun])

  useEffect(() => {
    setSelectedRecoveryCheckpointId(null)
    setSelectedRecoverySnapshotId(null)
    setSelectedRecoveryApplyTraceId(null)
    setAgentOSFeedback(null)
  }, [agentOSData?.run_state?.run_id, selectedRun, selectedTaxonomy])

  useEffect(() => {
    if (!selectedTaxonomy || !targetRun) return
    void refreshAgentOS(selectedTaxonomy, targetRun)
    void loadSpecialistCandidates(selectedTaxonomy, targetRun, specialistPhaseOverride)
    void loadAutoLoopStatus(selectedTaxonomy, targetRun)
  }, [activeDetailPhase, loadAutoLoopStatus, refreshAgentOS, selectedTaxonomy, targetRun, specialistPhaseOverride])

  // Poll auto-loop status every 5 s while the loop is running
  useEffect(() => {
    if (!selectedTaxonomy || !targetRun || !autoLoopStatus?.running) return
    const timer = window.setInterval(() => {
      void loadAutoLoopStatus(selectedTaxonomy, targetRun)
    }, 5000)
    return () => window.clearInterval(timer)
  }, [autoLoopStatus?.running, loadAutoLoopStatus, selectedTaxonomy, targetRun])

  // Atomic: fetch parent detail + history in parallel, update all state together
  const fetchDetail = async (taxonomy: string, runName: string) => {
    const requestId = ++detailRequestIdRef.current
    setSelectedRun(runName)
    setSelectedTaxonomy(taxonomy)
    setTargetRun(runName)
    setWorkspaceTab('agent-os')
    setArtifactModalOpen(false)
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
    setHistoryRun(runName)
  }

  // Atomic: fetch target detail + history in parallel, update all state together
  const fetchTargetDetail = async (taxonomy: string, runName: string) => {
    const requestId = ++detailRequestIdRef.current
    const previousTargetRun = targetRun
    setTargetRun(runName)
    setAgentOSLoading(true)
    setAgentOSData(null)
    setArtifactModalOpen(false)
    setSelectedArtifact(null)
    setArtifactContent('')
    setCodexResult(null)
    setCodexError(null)
    try {
      const [data, historyData, agentData] = await Promise.all([
        loadRunDetail(taxonomy, runName),
        loadHistory(taxonomy, runName),
        loadAgentOS(taxonomy, runName),
      ])
      if (detailRequestIdRef.current !== requestId) return
      setTargetRun(runName)
      setTargetDetail(data)
      setHistory(historyData)
      setHistoryRun(runName)
      setAgentOSData(agentData)
      void loadSpecialistCandidates(taxonomy, runName, specialistPhaseOverride)
    } catch (error) {
      if (detailRequestIdRef.current !== requestId) return
      setTargetRun(previousTargetRun ?? detail?.name ?? null)
      setTargetDetail(previousTargetRun && detail && previousTargetRun !== detail.name ? targetDetail : detail)
      setAgentOSData(null)
      setModalConfig({
        title: 'Failed to Open Target Run',
        message: error instanceof Error ? error.message : 'Failed to load the selected run context.',
        onConfirm: () => setModalConfig(null),
      })
    } finally {
      if (detailRequestIdRef.current === requestId) {
        setAgentOSLoading(false)
      }
    }
  }

  const fetchArtifact = useCallback(async (filename: string) => {
    if (!targetRun || !selectedTaxonomy) return
    setSelectedArtifact(filename)
    const resp = await fetch(`${API_BASE}/runs/${selectedTaxonomy}/${encodeURIComponent(targetRun)}/artifacts/${filename}`)
    const data = await resp.json()
    setArtifactContent(data.content ?? '')
  }, [selectedTaxonomy, targetRun])

  const openArtifactReferenceModal = useCallback((preferredArtifact?: string) => {
    const availableArtifacts = (targetDetail?.artifacts ?? detail?.artifacts ?? []).filter((artifact) => artifact.exists)
    if (availableArtifacts.length === 0) return
    const nextArtifact =
      preferredArtifact
      ?? (selectedArtifact && availableArtifacts.some((artifact) => artifact.name === selectedArtifact) ? selectedArtifact : null)
      ?? availableArtifacts[0].name
    setArtifactModalOpen(true)
    if (nextArtifact !== selectedArtifact || artifactContent === '') {
      void fetchArtifact(nextArtifact)
    }
  }, [artifactContent, detail?.artifacts, fetchArtifact, selectedArtifact, targetDetail?.artifacts])

  useEffect(() => {
    void fetchRuns()
    void loadOperatorMatrix().then(setMatrixRows).catch(() => setMatrixRows([]))
    void loadRecentExecutions().then(setRecentExecutions).catch(() => setRecentExecutions([]))
    void loadViewerConfig().then(setViewerConfig).catch(() => setViewerConfig(null))
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

  useEffect(() => {
    if (typeof window === 'undefined') return
    window.localStorage.setItem(TAXONOMY_PIN_STORAGE_KEY, JSON.stringify(pinnedTaxonomies))
  }, [pinnedTaxonomies])

  useEffect(() => {
    if (typeof window === 'undefined') return
    window.localStorage.setItem(TAXONOMY_OPEN_STORAGE_KEY, JSON.stringify(openTaxonomies))
  }, [openTaxonomies])

  // Atomic auto-refresh: all three fetches in parallel, single render pass
  useEffect(() => {
    if (!selectedRun || !selectedTaxonomy) return
    const detailTimer = setInterval(async () => {
      const requestId = ++refreshRequestIdRef.current
      const parentPromise = loadRunDetail(selectedTaxonomy, selectedRun)
      const histTarget = targetRun ?? selectedRun
      const historyPromise = loadHistory(selectedTaxonomy, histTarget)
      const targetPromise = targetRun ? loadRunDetail(selectedTaxonomy, targetRun) : parentPromise
      const agentPromise = loadAgentOS(selectedTaxonomy, histTarget).catch(() => null)

      const [parentDetail, historyData, targetDetailData, agentData] = await Promise.all([
        parentPromise,
        historyPromise,
        targetPromise,
        agentPromise,
      ])
      if (refreshRequestIdRef.current !== requestId) return
      setDetail(parentDetail)
      setTargetDetail(targetDetailData)
      setHistory(historyData)
      setHistoryRun(histTarget)
      if (agentData) {
        setAgentOSData(agentData)
      }
    }, viewerConfig?.run_detail_refresh_ms ?? SELECTED_RUN_REFRESH_MS)
    return () => clearInterval(detailTimer)
  }, [loadAgentOS, selectedRun, selectedTaxonomy, targetRun, viewerConfig?.run_detail_refresh_ms])

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
          setHistoryRun(runName)
        }
      }),
    )

    await Promise.all(refreshes)
  }

  const sendJudgeChatMessage = async () => {
    if (!judgeChatInput.trim() || judgeChatLoading || !selectedTaxonomy || !activeTargetName) return
    const userMessage = { role: 'user' as const, content: judgeChatInput.trim() }
    const newMessages = [...judgeChatMessages, userMessage]
    setJudgeChatMessages(newMessages)
    setJudgeChatInput('')
    setJudgeChatLoading(true)
    try {
      const resp = await fetch(`${API_BASE}/runs/${selectedTaxonomy}/${encodeURIComponent(activeTargetName)}/judge-chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ messages: newMessages }),
      })
      const text = await resp.text()
      if (!resp.ok) {
        let detail = text
        try { detail = JSON.parse(text).detail ?? text } catch { /* use raw text */ }
        throw new Error(detail)
      }
      const data = JSON.parse(text)
      setJudgeChatMessages([...newMessages, { role: 'assistant', content: data.reply }])
    } catch (error) {
      setJudgeChatMessages([...newMessages, { role: 'assistant', content: `Error: ${error instanceof Error ? error.message : 'Unknown error'}` }])
    } finally {
      setJudgeChatLoading(false)
    }
  }

  const openJudgeChat = () => {
    if (judgeChatMessages.length === 0) {
      const phaseLine = activeDetailPhase ? `Current phase: ${activeDetailPhase}.` : ''
      const recommendationLine = activeJudgeRecommendation
        ? `Suggested return: ${activeJudgeRecommendation.suggested_action_label || activeJudgeRecommendation.decision}.`
        : 'No judge advisory is loaded yet.'
      setJudgeChatMessages([
        {
          role: 'assistant',
          content: `Judge support is ready. ${phaseLine} ${recommendationLine} Ask about next action, tradeoffs, or what to write in the return comment.`.trim(),
        },
      ])
    }
    setJudgeChatOpen(true)
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

    const activeTargetName = targetDetail?.name ?? targetRun ?? null
    const matrixTargetsDifferentRun = activeTargetName !== null && activeTargetName !== row.name
    const matrixContextWarning = matrixTargetsDifferentRun
      ? `Execution Matrix always targets the top-level run on the card.\n\nCurrent target: ${activeTargetName}\nMatrix target: ${row.name}\n\nUse Run Detail actions if you intend to operate on the current child run.`
      : null

    setModalConfig({
      title: `Confirm ${action.label}`,
      message: matrixContextWarning ? `${matrixContextWarning}\n\n${action.command}` : `${row.name}\n\n${action.command}`,
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
          const shouldRefreshParent = selectedRun === row.name
          const shouldRefreshTarget = targetRun === row.name
          if (shouldRefreshParent || shouldRefreshTarget) {
            const refreshes: Promise<void>[] = []
            if (shouldRefreshParent) {
              refreshes.push(
                loadRunDetail(row.taxonomy, row.name).then((refreshedDetail) => {
                  setDetail(refreshedDetail)
                  if ((targetRun ?? refreshedDetail.name) === refreshedDetail.name) {
                    setTargetDetail(refreshedDetail)
                  }
                }),
              )
            }
            if (shouldRefreshTarget) {
              refreshes.push(
                Promise.all([
                  loadRunDetail(row.taxonomy, row.name),
                  loadHistory(row.taxonomy, row.name),
                ]).then(([refreshedTarget, historyData]) => {
                  setTargetDetail(refreshedTarget)
                  setHistory(historyData)
                  setHistoryRun(row.name)
                }),
              )
            }
            await Promise.all(refreshes)
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

  const runAgentOSAction = async (
    taxonomy: string,
    runName: string,
    payload: {
      action_id: 'act' | 'capture-snapshot' | 'capture-checkpoint' | 'apply-snapshot' | 'apply-checkpoint'
      snapshot_id?: string | null
      checkpoint_id?: string | null
      reason?: string
      confirmed?: boolean
    },
  ) => {
    startRunExecution(taxonomy, runName, payload.action_id)
    setExecutionResult(null)
    setAgentOSFeedback({
      kind: 'running',
      title: 'Action In Flight',
      detail: `${payload.action_id} is running for ${runName}.`,
      actionId: payload.action_id,
    })
    try {
      const resp = await fetch(`${API_BASE}/runs/${taxonomy}/${encodeURIComponent(runName)}/agent-os/actions/execute`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })
      const data = (await resp.json()) as ExecutionResult
      if (!resp.ok) throw new Error('Failed to execute Agent OS action')
      setExecutionResult(data)
      if (data.status === 'FAILED') {
        setAgentOSFeedback({
          kind: data.exit_code === 1 && !data.stdout ? 'blocked' : 'failure',
          title: data.exit_code === 1 && !data.stdout ? 'Action Blocked' : 'Action Failed',
          detail: data.stderr || 'Agent OS action failed',
          actionId: payload.action_id,
        })
      } else {
        setAgentOSFeedback({
          kind: 'success',
          title: 'Action Succeeded',
          detail: data.stdout || `${payload.action_id} completed successfully.`,
          actionId: payload.action_id,
        })
      }
      await Promise.all([
        fetchRuns(),
        loadOperatorMatrix().then(setMatrixRows).catch(() => {}),
        loadRecentExecutions().then(setRecentExecutions).catch(() => {}),
        refreshRunContexts(taxonomy, runName),
        refreshAgentOS(taxonomy, runName),
      ])
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to execute Agent OS action'
      setAgentOSFeedback({
        kind: 'failure',
        title: 'Action Failed',
        detail: message,
        actionId: payload.action_id,
      })
      setExecutionResult({
        action_id: payload.action_id,
        command: `agent-os:${payload.action_id}`,
        status: 'FAILED',
        exit_code: -1,
        stdout: '',
        stderr: message,
      })
    } finally {
      finishRunExecution(taxonomy, runName)
    }
  }

  const executeAgentOSAction = (
    actionId: 'act' | 'capture-snapshot' | 'capture-checkpoint' | 'apply-snapshot' | 'apply-checkpoint',
    taxonomy: string,
    runName: string,
  ) => {
    if (actionId === 'apply-checkpoint') {
      if (!selectedRecoveryCheckpointId) {
        setAgentOSFeedback({
          kind: 'blocked',
          title: 'Action Blocked',
          detail: 'Apply checkpoint is blocked: select a checkpoint candidate first.',
          actionId,
        })
        return
      }
      setModalConfig({
        title: 'Confirm Checkpoint Apply',
        message: `Selected checkpoint: ${selectedRecoveryCheckpointId}\n\nThis will overwrite current execution state in run_state.json.`,
        confirmLabel: 'Apply Checkpoint',
        tone: 'danger',
        inputLabel: 'Reason',
        inputPlaceholder: 'Why is this checkpoint apply necessary?',
        inputRequired: true,
        onConfirm: async (inputValue) => {
          setModalConfig(null)
          await runAgentOSAction(taxonomy, runName, {
            action_id: 'apply-checkpoint',
            checkpoint_id: selectedRecoveryCheckpointId,
            reason: inputValue?.trim() ?? '',
            confirmed: true,
          })
        },
      })
      return
    }

    if (actionId === 'apply-snapshot') {
      if (!selectedRecoverySnapshotId) {
        setAgentOSFeedback({
          kind: 'blocked',
          title: 'Action Blocked',
          detail: 'Apply snapshot is blocked: select a snapshot candidate first.',
          actionId,
        })
        return
      }
      setModalConfig({
        title: 'Confirm Snapshot Apply',
        message: `Selected snapshot: ${selectedRecoverySnapshotId}\n\nThis will overwrite current file state for the snapshot target paths.`,
        confirmLabel: 'Apply Snapshot',
        tone: 'danger',
        inputLabel: 'Reason',
        inputPlaceholder: 'Why is this snapshot apply necessary?',
        inputRequired: true,
        onConfirm: async (inputValue) => {
          setModalConfig(null)
          await runAgentOSAction(taxonomy, runName, {
            action_id: 'apply-snapshot',
            snapshot_id: selectedRecoverySnapshotId,
            reason: inputValue?.trim() ?? '',
            confirmed: true,
          })
        },
      })
      return
    }

    void runAgentOSAction(taxonomy, runName, { action_id: actionId })
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

  const filteredRuns = runs.filter((run) => {
    const matchesSearch = run.name.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesHumanBlocker = humanBlockerFilter === 'all' || Boolean(run.human_blocker_active)
    return matchesSearch && matchesHumanBlocker
  })
  const detailActions = targetDetail?.operator_actions ?? []
  const activeDetail = targetDetail ?? detail
  const activeJudgeRecommendation = activeDetail?.judge_recommendation ?? null
  const recommendedActionId = activeJudgeRecommendation?.suggested_action_id ?? null
  const sortedDetailActions = [...detailActions].sort((a, b) => {
    if (a.id === recommendedActionId) return -1
    if (b.id === recommendedActionId) return 1
    if (a.primary && !b.primary) return -1
    if (!a.primary && b.primary) return 1
    return 0
  })
  const executableActions = sortedDetailActions.filter((action) => action.execution_type !== 'human')
  const humanActions = sortedDetailActions.filter((action) => action.execution_type === 'human')
  const improveDecisionActionIds = ['accept-improve', 'phase-primary', 'rerun-plan', 'rerun-build', 'rerun-review']
  const improveDecisionActions = activeDetailPhase === 'IMPROVE_NEEDED'
    ? improveDecisionActionIds
        .map((id) => sortedDetailActions.find((action) => action.id === id) ?? null)
        .filter((action): action is OperatorAction => action !== null)
    : []
  const improveDecisionActionIdSet = new Set(improveDecisionActions.map((action) => action.id))
  const regularExecutableActions = executableActions.filter((action) => !improveDecisionActionIdSet.has(action.id))
  const regularHumanActions = humanActions.filter((action) => !improveDecisionActionIdSet.has(action.id))
  const primaryExecutableAction = executableActions.find((action) => action.primary) ?? executableActions[0] ?? null
  const phaseContextActions = activeDetailPhase === 'IMPROVE_NEEDED' ? sortedDetailActions : [...executableActions, ...humanActions]
  const childRuns = detail?.children ?? []
  const matchingMatrixRows = matrixRows.filter((row) => row.name.toLowerCase().includes(searchTerm.toLowerCase()))
  const activePhases = new Set(['PLAN_NEEDED', 'BUILD_NEEDED', 'REVIEW_NEEDED', 'IMPROVE_NEEDED', 'RESULT_NEEDED'])
  const recentRunNames = new Set(recentExecutions.map((job) => job.run_name))
  const togglePinnedTaxonomy = (taxonomy: string) => {
    setPinnedTaxonomies((current) =>
      current.includes(taxonomy) ? current.filter((value) => value !== taxonomy) : [...current, taxonomy],
    )
    setOpenTaxonomies((current) => (current.includes(taxonomy) ? current : [...current, taxonomy]))
  }
  const toggleOpenTaxonomy = (taxonomy: string) => {
    setOpenTaxonomies((current) =>
      current.includes(taxonomy) ? current.filter((value) => value !== taxonomy) : [...current, taxonomy],
    )
  }
  const filteredRecentExecutions = recentExecutions.filter((job) =>
    job.run_name.toLowerCase().includes(jobsSearchTerm.toLowerCase()),
  )
  const operatorRows = matchingMatrixRows.filter((row) => {
    if (operatorFilter === 'all') return true
    if (operatorFilter === 'recent') return recentRunNames.has(row.name)
    return activePhases.has(row.phase)
  }).slice(0, 10)
  const showDetailedAssignmentCard = searchTerm.trim() === '__show_assignment_details__'
  const taxonomySections = (() => {
    const grouped = new Map<string, RunSummary[]>()
    for (const run of filteredRuns) {
      const bucket = grouped.get(run.taxonomy) ?? []
      bucket.push(run)
      grouped.set(run.taxonomy, bucket)
    }
    const seen = new Set<string>()
    const orderedTaxonomies = [
      ...TAXONOMY_SECTION_ORDER.filter((taxonomy) => grouped.has(taxonomy)),
      ...Array.from(grouped.keys()).filter((taxonomy) => !TAXONOMY_SECTION_ORDER.includes(taxonomy as (typeof TAXONOMY_SECTION_ORDER)[number])).sort(),
    ]
    return orderedTaxonomies
      .filter((taxonomy) => {
        if (seen.has(taxonomy)) return false
        seen.add(taxonomy)
        return true
      })
      .map((taxonomy) => ({
        taxonomy,
        label: TAXONOMY_SECTION_LABELS[taxonomy] ?? taxonomy,
        pinned: pinnedTaxonomies.includes(taxonomy),
        open: openTaxonomies.includes(taxonomy),
        runs: (grouped.get(taxonomy) ?? []).sort((left, right) => right.last_modified - left.last_modified),
      }))
      .sort((left, right) => {
        if (left.pinned !== right.pinned) return left.pinned ? -1 : 1
        const leftIndex = TAXONOMY_SECTION_ORDER.indexOf(left.taxonomy as (typeof TAXONOMY_SECTION_ORDER)[number])
        const rightIndex = TAXONOMY_SECTION_ORDER.indexOf(right.taxonomy as (typeof TAXONOMY_SECTION_ORDER)[number])
        if (leftIndex !== -1 || rightIndex !== -1) {
          if (leftIndex === -1) return 1
          if (rightIndex === -1) return -1
          return leftIndex - rightIndex
        }
        return left.label.localeCompare(right.label)
      })
  })()
  const activeTargetName = targetDetail?.name ?? detail?.name ?? ''
  const activeChildName = detail && activeTargetName !== detail.name ? activeTargetName : null
  const activeRunExecutionState =
    selectedTaxonomy && activeTargetName ? executingStateForRun(selectedTaxonomy, activeTargetName) : null
  const activeRunExecutionId = activeRunExecutionState?.actionId ?? null
  const isActiveRunBusy = activeRunExecutionId !== null
  const activeExecutionElapsed = activeRunExecutionState ? formatElapsedMs(executionNow - activeRunExecutionState.startedAt) : null
  const failingGateResults = agentOSData?.gate_results?.filter((gate) => !gate.passed) ?? []
  const getCodexPresetsForPhase = (phase: string) =>
    (Object.entries(CODEX_PRESET_RULES) as Array<[CodexBridgeResult['preset_id'], (typeof CODEX_PRESET_RULES)[keyof typeof CODEX_PRESET_RULES]]>)
      .filter(([, rule]) => rule.allowedPhases.has(phase))
  const runLineage = detail
    ? [
        {
          name: detail.name,
          label: 'Parent',
          displayName: detail.name,
          phase: detail.phase,
          nextRole: detail.next_role,
          hasChildren: childRuns.length > 0,
          isParent: true,
          isSelected: targetRun === detail.name,
        },
        ...childRuns.map((child) => ({
          name: child.name,
          label: 'Child',
          displayName: child.child_name,
          phase: child.phase,
          nextRole: child.next_role,
          hasChildren: child.has_children,
          isParent: false,
          isSelected: targetRun === child.name,
        })),
      ]
    : []
  const targetReworkCount = [
    (targetDetail?.artifacts ?? detail?.artifacts ?? []).some((a) => a.name === 'plan_review.md' && a.exists),
    (targetDetail?.artifacts ?? detail?.artifacts ?? []).some((a) => a.name === 'build_review.md' && a.exists),
    (targetDetail?.artifacts ?? detail?.artifacts ?? []).some((a) => a.name === 'review_review.md' && a.exists),
    (targetDetail?.artifacts ?? detail?.artifacts ?? []).some((a) => a.name === 'improve_review.md' && a.exists),
  ].filter(Boolean).length
  const latestRunExecution =
    history?.latest_execution
      ? history.latest_execution
      : selectedTaxonomy && targetRun
        ? recentExecutions.find((job) =>
            job.taxonomy === selectedTaxonomy &&
            job.run_name === targetRun,
          ) ?? null
        : null
  const agentOSActionIds = new Set([
    'capture-snapshot',
    'capture-checkpoint',
    'apply-snapshot',
    'apply-checkpoint',
  ])
  const recentAgentOSExecutions =
    selectedTaxonomy && targetRun
      ? recentExecutions.filter((job) =>
          job.taxonomy === selectedTaxonomy &&
          job.run_name === targetRun &&
          agentOSActionIds.has(job.action_id),
        ).slice(0, 5)
      : []
  const activePhase = activeDetail?.phase ?? ''
  const activePriority = activeDetail?.priority ?? 'Unranked'
  const activeNextRole = activeDetail?.next_role ?? ''
  const activeOperatorCommand = activeDetail?.operator_command ?? ''
  const activeDecisionReason = activeDetail?.decision_reason ?? ''
  const activeAssignment = activeDetail?.assignment_summary ?? null
  const activeSpecialist = activeDetail?.specialist_visibility ?? null
  const activeOwner = agentOSData?.run_state?.current_owner ?? activeNextRole ?? ''
  const activePhaseStatus = agentOSData?.run_state?.phase_status ?? ''
  const ownerWorkingNow = activePhaseStatus === 'in_progress'
  const phaseEnteredAtMs = agentOSData?.run_state?.phase_entered_at ? Date.parse(agentOSData.run_state.phase_entered_at) : NaN
  const activePhaseElapsed = Number.isFinite(phaseEnteredAtMs) ? formatElapsedMs(Math.max(0, executionNow - phaseEnteredAtMs)) : null
  const ownerStatusLabel = ownerWorkingNow ? '実行中' : activePhaseStatus === 'pending' ? '待機中' : activePhaseStatus || 'Pending'
  const selectedPhaseContextAction =
    phaseContextActions.find((action) => action.id === phaseContextActionId)
    ?? primaryExecutableAction
    ?? phaseContextActions[0]
    ?? null
  const suggestedJudgeAction =
    activeJudgeRecommendation?.suggested_action_id
      ? detailActions.find((action) => action.id === activeJudgeRecommendation.suggested_action_id) ?? null
      : null

  useEffect(() => {
    if (phaseContextActions.length === 0) {
      setPhaseContextActionId('')
      return
    }
    setPhaseContextActionId((current) => (
      current && phaseContextActions.some((action) => action.id === current)
        ? current
        : (primaryExecutableAction?.id ?? phaseContextActions[0].id)
    ))
  }, [phaseContextActions, primaryExecutableAction])

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
  }, [fetchArtifact, targetDetail, selectedArtifact, selectedTaxonomy, targetRun])

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
    const runningState = executingStateForRun(taxonomy, runName)
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
          {isRunning ? 'Running...' : action.execution_type === 'human' ? 'Human Guidance Only' : action.label}
        </button>
      </div>
    )
  }

  return (
    <div className="flex h-screen overflow-hidden bg-zinc-950 text-zinc-100">
      {sidebarOpen && (
      <aside className="w-72 min-w-[18rem] shrink-0 border-r border-zinc-800 p-4 overflow-y-auto xl:w-80">
        <div className="mb-4 flex items-center gap-2">
          <Activity size={20} className="text-indigo-400" />
          <h1 className="flex-1 text-lg font-bold">APSF Viewer</h1>
          <button
            type="button"
            onClick={() => setViewerConfigModalOpen(true)}
            className="rounded border border-zinc-700 bg-zinc-900 p-1.5 text-zinc-300 hover:bg-zinc-800 hover:text-white"
            aria-label="Viewer Config"
            title="Viewer Config"
          >
            <Settings size={16} />
          </button>
          <button
            type="button"
            onClick={() => setSidebarOpen(false)}
            className="rounded border border-zinc-700 bg-zinc-900 p-1.5 text-zinc-300 hover:bg-zinc-800"
            aria-label="Hide run list"
            title="Hide run list"
          >
            <ChevronLeft size={16} />
          </button>
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
        <div className="mb-4 flex flex-wrap gap-2">
          {(['all', 'blocked'] as const).map((filter) => (
            <button
              key={filter}
              type="button"
              onClick={() => setHumanBlockerFilter(filter)}
              className={`rounded border px-2.5 py-1 text-[10px] font-bold uppercase ${
                humanBlockerFilter === filter
                  ? 'border-amber-400 bg-amber-500/20 text-amber-100'
                  : 'border-zinc-700 bg-zinc-900 text-zinc-400'
              }`}
            >
              {filter === 'all' ? 'All Runs' : 'Human Blockers'}
            </button>
          ))}
        </div>
        <div className="space-y-3">
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
            taxonomySections.map((section) => (
              <section key={section.taxonomy} className={`rounded-xl border ${section.pinned ? 'border-indigo-500/30 bg-indigo-500/5' : 'border-zinc-800 bg-zinc-950/30'}`}>
                <div className="flex items-center justify-between gap-2 px-3 py-2.5">
                  <button
                    type="button"
                    onClick={() => toggleOpenTaxonomy(section.taxonomy)}
                    className="min-w-0 flex-1 text-left"
                  >
                    <div className="flex items-center gap-2">
                      <span className={`rounded border px-1.5 py-0.5 text-[10px] font-bold uppercase ${section.pinned ? 'border-indigo-400/40 bg-indigo-500/20 text-indigo-100' : 'border-zinc-700 bg-zinc-900 text-zinc-400'}`}>
                        {section.taxonomy}
                      </span>
                      <span className="truncate text-[11px] font-bold uppercase tracking-[0.16em] text-zinc-400">{section.label}</span>
                    </div>
                    <div className="mt-1 text-[10px] text-zinc-600">
                      {section.runs.length} run{section.runs.length === 1 ? '' : 's'}{section.pinned ? ' / pinned' : ''}
                    </div>
                  </button>
                  <div className="flex items-center gap-2">
                    <button
                      type="button"
                      onClick={() => togglePinnedTaxonomy(section.taxonomy)}
                      className={`rounded border p-1.5 ${section.pinned ? 'border-indigo-400/40 bg-indigo-500/20 text-indigo-100' : 'border-zinc-700 bg-zinc-900 text-zinc-500 hover:text-zinc-200'}`}
                      title={section.pinned ? 'Unpin taxonomy' : 'Pin taxonomy'}
                      aria-label={section.pinned ? 'Unpin taxonomy' : 'Pin taxonomy'}
                    >
                      <Pin size={12} />
                    </button>
                    <button
                      type="button"
                      onClick={() => toggleOpenTaxonomy(section.taxonomy)}
                      className="rounded border border-zinc-700 bg-zinc-900 px-2 py-1 text-[10px] font-semibold text-zinc-400"
                    >
                      {section.open ? 'Hide' : 'Show'}
                    </button>
                  </div>
                </div>
                {section.open && (
                  <div className="space-y-2 border-t border-zinc-800/80 px-2 pb-2 pt-2">
                    {section.runs.map((run) => (
                      <button
                        key={`${run.taxonomy}-${run.name}`}
                        onClick={() => void fetchDetail(run.taxonomy, run.name)}
                        className={`w-full rounded-lg border p-3 text-left ${selectedRun === run.name ? 'border-indigo-500/40 bg-indigo-500/10' : 'border-zinc-800 bg-zinc-900/40 hover:bg-zinc-900'}`}
                      >
                        <div className="mb-2 break-words text-sm font-medium">{run.name}</div>
                        <div className="mb-2 text-[11px] text-zinc-500">Next: {run.next_role}</div>
                        <div className="flex flex-wrap items-center gap-1">
                          <PhaseBadge phase={run.phase} />
                          <PriorityBadge priority={run.priority} />
                          <CountBadge count={run.child_count} />
                          <ReworkBadge count={[run.has_plan_review, run.has_build_review, run.has_review_review, run.has_improve_review].filter(Boolean).length} />
                          {run.human_blocker_active && (
                            <span className="rounded border border-amber-500/40 bg-amber-500/15 px-1.5 py-0.5 text-[10px] font-bold text-amber-200">
                              HUMAN BLOCKER
                            </span>
                          )}
                        </div>
                      </button>
                    ))}
                  </div>
                )}
              </section>
            ))
          )}
        </div>
      </aside>
      )}

      <main className="flex min-w-0 flex-1 flex-col overflow-hidden 2xl:flex-row">
        {!detail ? (
          <div className="flex flex-1 items-center justify-center text-zinc-500 font-medium">
            {!sidebarOpen && (
              <button
                type="button"
                onClick={() => setSidebarOpen(true)}
                className="absolute left-4 top-4 flex items-center gap-2 rounded border border-zinc-700 bg-zinc-900 px-3 py-2 text-xs font-bold text-zinc-200 hover:bg-zinc-800"
              >
                <ChevronRight size={16} />
                Show Run List
              </button>
            )}
            Select a run from the list to view details.
          </div>
        ) : (
          <>
            <section
              className={`min-h-0 min-w-0 border-b border-zinc-800 p-4 overflow-y-auto 2xl:border-b-0 ${workspaceTab === 'detail' ? 'xl:w-[28rem] xl:shrink-0 xl:border-r 2xl:w-[min(36rem,35vw)]' : 'flex-1'}`}
            >
              <div className="sticky top-0 z-20 -mx-4 mb-4 border-b border-zinc-800 bg-zinc-950/95 px-4 pb-4 backdrop-blur">
                {/* Stable Core: Badges and Title */}
                <div className="flex items-start justify-between gap-3">
                  {!sidebarOpen && (
                    <button
                      type="button"
                      onClick={() => setSidebarOpen(true)}
                      className="mt-0.5 rounded border border-zinc-700 bg-zinc-900 p-1.5 text-zinc-300 hover:bg-zinc-800"
                      aria-label="Show run list"
                      title="Show run list"
                    >
                      <ChevronRight size={16} />
                    </button>
                  )}
                  <div className="min-w-0 flex-1">
                    <div className="mb-2 flex flex-wrap items-center gap-2">
                      <PhaseBadge phase={targetDetail?.phase ?? detail.phase} />
                      <PriorityBadge priority={targetDetail?.priority ?? detail.priority} />
                      {targetDetail && targetDetail.name !== detail.name && (
                        <span className="flex items-center gap-1 rounded bg-indigo-500/25 border border-indigo-500/40 px-1.5 py-0.5 font-bold text-indigo-100 text-[10px]">
                          <Terminal size={10} />
                          CHILD
                        </span>
                      )}
                    </div>
                    <div className="flex flex-col min-w-0">
                      <span className="mb-0.5 truncate leading-tight text-xs text-zinc-500" title={targetDetail?.name ?? detail.name}>
                        {(targetDetail?.name ?? detail.name).split('_')[0]}
                      </span>
                      <h2 className="truncate text-base font-bold leading-snug">
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
                  compact
                />

                {workspaceTab !== 'agent-os' && (
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
                )}

                <div className="overflow-hidden">
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
                </div>

                {runLineage.length > 1 && (
                  <div className="mt-3 space-y-2 border-t border-zinc-800/70 pt-3">
                    <div className="flex items-center justify-between gap-3">
                      <div className="text-[10px] font-semibold uppercase tracking-[0.16em] text-zinc-600">Run Lineage</div>
                      <button
                        type="button"
                        onClick={() => setCurrentViewOpen((open) => !open)}
                        className="rounded border border-zinc-800 bg-zinc-900/60 px-2 py-1 text-[10px] font-semibold text-zinc-400"
                      >
                        {currentViewOpen ? 'Hide' : 'Show'}
                      </button>
                    </div>
                    {currentViewOpen && (
                      <div className="space-y-2">
                        {runLineage.map((entry) => (
                          <button
                            key={entry.name}
                            onClick={() => {
                              setCurrentViewOpen(false)
                              void fetchTargetDetail(detail.taxonomy, entry.name)
                            }}
                            className={`w-full rounded-xl border px-3 py-3 text-left ${
                              entry.isSelected
                                ? 'border-indigo-500/40 bg-indigo-500/10 text-indigo-100'
                                : 'border-zinc-800 bg-zinc-900/60 text-zinc-300 hover:bg-zinc-900'
                            }`}
                          >
                            <div className="flex items-start justify-between gap-3">
                              <div className="min-w-0">
                                <div className="flex flex-wrap items-center gap-2">
                                  <span className={`rounded border px-1.5 py-0.5 text-[10px] font-bold uppercase ${entry.isParent ? 'border-emerald-500/30 bg-emerald-500/10 text-emerald-200' : 'border-indigo-500/30 bg-indigo-500/10 text-indigo-200'}`}>
                                    {entry.label}
                                  </span>
                                  {entry.isSelected && (
                                    <span className="rounded border border-indigo-400/40 bg-indigo-500/15 px-1.5 py-0.5 text-[10px] font-bold uppercase text-indigo-100">
                                      Viewing
                                    </span>
                                  )}
                                </div>
                                <div className="mt-2 truncate text-sm font-semibold text-zinc-100">{entry.displayName}</div>
                                <div className="mt-1 flex flex-wrap items-center gap-2 text-[11px] text-zinc-500">
                                  <span>{entry.phase}</span>
                                  <span className="opacity-40">/</span>
                                  <span>{entry.nextRole}</span>
                                  {entry.hasChildren && (
                                    <>
                                      <span className="opacity-40">/</span>
                                      <span>has children</span>
                                    </>
                                  )}
                                </div>
                              </div>
                              <div className="shrink-0 flex flex-col items-end gap-1">
                                <PhaseBadge phase={entry.phase} />
                              </div>
                            </div>
                          </button>
                        ))}
                      </div>
                    )}
                  </div>
                )}

                <div className="mt-3 flex flex-wrap items-center gap-2 border-t border-zinc-800/70 pt-3">
                  <button
                    onClick={() => openAgentOSWorkspace(selectedTaxonomy, targetRun)}
                    className={`rounded border px-3 py-1.5 text-xs font-bold transition-all duration-200 ${workspaceTab === 'agent-os' ? 'border-emerald-400 bg-emerald-500/20 text-emerald-100' : 'border-zinc-700 bg-zinc-900 text-zinc-300 hover:bg-zinc-800'}`}
                  >
                    Agent OS
                  </button>
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
                  {((targetDetail?.artifacts ?? detail.artifacts).some((artifact) => artifact.exists)) && (
                    <button
                      type="button"
                      onClick={() => openArtifactReferenceModal()}
                      className="ml-auto inline-flex items-center gap-2 rounded border border-indigo-500/30 bg-indigo-500/10 px-3 py-1.5 text-xs font-bold text-indigo-100 transition-colors hover:bg-indigo-500/20"
                    >
                      <FileText size={14} />
                      Artifacts
                    </button>
                  )}
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
                      {(targetDetail?.human_blocker?.active ?? detail.human_blocker?.active ?? false) && (
                        <div className="mt-3 rounded border border-amber-500/30 bg-amber-500/10 p-3">
                          <div className="flex flex-wrap items-center gap-2">
                            <span className="rounded border border-amber-400/40 bg-amber-500/15 px-2 py-0.5 text-[10px] font-bold uppercase tracking-[0.16em] text-amber-100">
                              Human Blocker
                            </span>
                            {((targetDetail?.human_blocker?.source ?? detail.human_blocker?.source)) && (
                              <span className="text-[10px] text-amber-200/80">
                                source: {targetDetail?.human_blocker?.source ?? detail.human_blocker?.source}
                              </span>
                            )}
                          </div>
                          <div className="mt-2 text-xs text-zinc-200">
                            {targetDetail?.human_blocker?.summary ?? detail.human_blocker?.summary}
                          </div>
                          {((targetDetail?.human_blocker?.actions ?? detail.human_blocker?.actions ?? []).length > 0) && (
                            <div className="mt-2 space-y-1">
                              {(targetDetail?.human_blocker?.actions ?? detail.human_blocker?.actions ?? []).slice(0, 3).map((action, index) => (
                                <div key={`${action}-${index}`} className="text-[11px] text-zinc-300">
                                  {action}
                                </div>
                              ))}
                            </div>
                          )}
                        </div>
                      )}
                    </div>

                    <div className="rounded border border-zinc-800 bg-zinc-900/40 p-4">
                      <div className="mb-2 text-[11px] font-bold uppercase tracking-[0.2em] text-zinc-500">Topology Summary</div>
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="rounded border border-emerald-500/30 bg-emerald-500/10 px-2 py-0.5 text-[10px] font-bold text-emerald-300">
                          parent
                        </span>
                        <span className="rounded border border-indigo-500/30 bg-indigo-500/10 px-2 py-0.5 text-[10px] font-bold text-indigo-300">
                          {childRuns.length} child run{childRuns.length === 1 ? '' : 's'}
                        </span>
                        {activeChildName && (
                          <span className="rounded border border-indigo-500/30 bg-indigo-500/10 px-2 py-0.5 text-[10px] font-bold text-indigo-300">
                            viewing child
                          </span>
                        )}
                      </div>
                      <div className="mt-3 text-xs text-zinc-400">
                        Parent and child runs are now selectable from the lineage list above. The active run stays highlighted there with its phase and next role.
                      </div>
                      {childRuns.length === 0 && (
                        <div className="mt-3 text-xs text-zinc-500">No child runs for this target.</div>
                      )}
                    </div>
                  </div>

                  {history && (history.latest_execution || history.latest_rerun_comment) && (
                    <div className="rounded border border-emerald-500/20 bg-emerald-500/5 p-4">
                      <div className="mb-3 text-[11px] font-bold uppercase tracking-[0.2em] text-emerald-300">Latest Persisted Activity</div>
                      <div className="mb-3 text-[11px] text-zinc-400">
                        Showing history for <span className="font-mono text-zinc-200">{historyRun ?? targetRun ?? detail.name}</span>
                      </div>
                      <div className="grid gap-3 xl:grid-cols-2">
                        {history.latest_execution ? (
                          <div className="rounded border border-zinc-800 bg-black/20 p-3">
                            <div className="mb-1 text-[10px] font-bold uppercase tracking-[0.2em] text-zinc-500">Execution</div>
                            <div className="flex items-center gap-2">
                              <span className="rounded bg-zinc-900 px-2 py-0.5 text-[10px] font-bold text-zinc-300">{history.latest_execution.action_id}</span>
                              <PhaseBadge phase={history.latest_execution.result_status} />
                            </div>
                            <div className="mt-2 text-xs text-zinc-400">{history.latest_execution.triggered_at}</div>
                            {(history.latest_execution.result_status === 'PARTIAL' || history.latest_execution.result_status === 'FAILED') && history.latest_execution.stdout_summary && (
                              <div className="mt-2 rounded border border-amber-500/20 bg-black/40 p-2">
                                <div className="mb-1 text-[9px] font-bold uppercase tracking-[0.15em] text-amber-400/70">Last Output</div>
                                <pre className="whitespace-pre-wrap font-mono text-[10px] leading-relaxed text-zinc-300 line-clamp-4">{history.latest_execution.stdout_summary.split('\n').slice(-4).join('\n')}</pre>
                              </div>
                            )}
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

                  {improveDecisionActions.length > 0 && selectedTaxonomy && targetDetail && (
                    <div className="space-y-3">
                      <div className="text-[11px] font-bold uppercase tracking-[0.2em] text-zinc-500">Judge Decision Paths</div>
                      <div className="rounded border border-fuchsia-500/20 bg-fuchsia-500/5 px-3 py-2 text-[11px] text-zinc-300">
                        Accept, return to Plan, and return to Build stay visible here even when Judge Advisory recommends only one path.
                      </div>
                      {improveDecisionActions.map((action) =>
                        renderOperatorAction(
                          action,
                          action.execution_type === 'human' ? 'manual' : 'executable',
                          selectedTaxonomy,
                          targetDetail.name,
                        ),
                      )}
                    </div>
                  )}

                  {regularExecutableActions.length > 0 && selectedTaxonomy && targetDetail && (
                    <div className="space-y-3">
                      <div className="text-[11px] font-bold uppercase tracking-[0.2em] text-zinc-500">
                        {recommendedActionId ? 'Recommended And More Actions' : 'More Actions'}
                      </div>
                      {recommendedActionId && (
                        <div className="rounded border border-emerald-500/20 bg-emerald-500/5 px-3 py-2 text-[11px] text-zinc-300">
                          Judge Advisory recommends the first action in this list.
                        </div>
                      )}
                      {regularExecutableActions.map((action) => renderOperatorAction(action, 'executable', selectedTaxonomy, targetDetail.name))}
                    </div>
                  )}

                  {regularHumanActions.length > 0 && selectedTaxonomy && targetDetail && (
                    <div className="space-y-3">
                      <div className="pt-2 text-[11px] font-bold uppercase tracking-[0.2em] text-zinc-500">Run Manual Steps</div>
                      {regularHumanActions.map((action) => renderOperatorAction(action, 'manual', selectedTaxonomy, targetDetail.name))}
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
                    {targetDetail && targetDetail.name !== detail.name && (
                      <div className="mb-3 rounded border border-amber-500/30 bg-amber-500/10 px-3 py-2 text-xs text-amber-100">
                        Execution Matrix runs parent-level commands. Current child target: <span className="font-mono">{targetDetail.name}</span>. Use Run Detail actions for child runs.
                      </div>
                    )}
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
                              {selectedRun === row.name && (
                                <span className="rounded border border-indigo-500/30 bg-indigo-500/10 px-1.5 py-0.5 text-[10px] font-bold text-indigo-200">
                                  SELECTED PARENT
                                </span>
                              )}
                            </div>
                          </div>
                          <div className="mb-3 flex items-center justify-between gap-3">
                            <div className="text-xs text-zinc-500">Open the parent run in Agent OS, or operate directly from this top-level card.</div>
                            <button
                              onClick={() => void fetchDetail(row.taxonomy, row.name)}
                              className="rounded border border-zinc-700 bg-zinc-950 px-2.5 py-1 text-[10px] font-bold text-zinc-200"
                            >
                              Open Parent
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
              ) : workspaceTab === 'agent-os' ? (
                <div className="space-y-4">
                  {agentOSLoading && (
                    <div className="flex items-center justify-center py-8 text-xs text-zinc-500">Loading Agent OS data…</div>
                  )}
                  {!agentOSLoading && !agentOSData && (
                    <div className="rounded border border-dashed border-zinc-800 bg-zinc-900/20 p-6 text-center text-xs text-zinc-500">
                      Select a run to view the default Agent OS workspace.
                    </div>
                  )}
                  {!agentOSLoading && agentOSData && (
                        <>
                      {executionResult && (
                        <div className={`rounded border p-4 ${
                          executionResult.status === 'FAILED' && executionResult.exit_code === 1 && !executionResult.stdout
                            ? 'border-yellow-500/40 bg-yellow-500/5'
                            : executionResult.status === 'FAILED'
                              ? 'border-red-500/40 bg-red-500/5'
                              : executionResult.status === 'SUCCESS'
                                ? 'border-emerald-500/30 bg-emerald-500/8'
                                : 'border-zinc-800 bg-zinc-900/40'
                        }`}>
                          <div className="mb-2 flex items-center justify-between gap-3">
                            <div>
                              <div className="text-[11px] font-bold uppercase tracking-[0.2em] text-zinc-400">Latest Result</div>
                              <div className="mt-1 text-xs text-zinc-300">{executionResult.action_id}</div>
                            </div>
                            <div className="flex items-center gap-2">
                              {hasExecutionLogContent(executionResult.stdout, executionResult.stderr) && (
                                <CopyButton text={buildExecutionLogText(executionResult.stdout, executionResult.stderr)} />
                              )}
                              <PhaseBadge phase={executionResult.status} />
                            </div>
                          </div>
                          <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-[11px] text-zinc-400">
                            <span>Exit code: <span className={executionResult.exit_code !== 0 ? 'text-red-300' : 'text-zinc-200'}>{executionResult.exit_code}</span></span>
                            <span className="truncate">Action: <span className="font-mono text-zinc-200">{executionResult.action_id}</span></span>
                          </div>
                          <div className="mt-2 rounded border border-zinc-800 bg-black/20 px-3 py-2 text-[11px] text-zinc-300">
                            {executionResult.status === 'FAILED' && executionResult.exit_code === 1 && !executionResult.stdout
                              ? 'Operation was blocked before execution.'
                              : executionResult.status === 'FAILED'
                                ? (executionResult.stderr || executionResult.stdout || 'Operation failed. Open the lower result panel for details.')
                                : executionResult.status === 'SUCCESS'
                                  ? (executionResult.stdout || executionResult.stderr || 'Operation completed successfully.')
                                  : 'Execution finished.'}
                          </div>
                        </div>
                      )}
                      <div className="grid gap-4 xl:grid-cols-2 2xl:grid-cols-3">
                        <div className="rounded border border-emerald-500/20 bg-emerald-500/5 p-4">
                          <div className="mb-2 flex items-center justify-between gap-2">
                            <div>
                              <div className="text-[11px] font-bold uppercase tracking-[0.2em] text-emerald-300">Phase Context</div>
                              <div className="mt-1 text-[10px] text-zinc-500">Default workspace for current truth.</div>
                            </div>
                            <div className="flex items-center gap-2">
                              <button
                                type="button"
                                onClick={() => setViewerConfigModalOpen(true)}
                                className="rounded border border-zinc-700 bg-zinc-900 px-2.5 py-1 text-[10px] font-semibold uppercase tracking-wide text-zinc-300 hover:border-zinc-500 hover:text-white"
                              >
                                Config
                              </button>
                              <PhaseBadge phase={activePhase} />
                            </div>
                          </div>
                          <div className="space-y-2 text-xs">
                            <div>
                              <div className="text-[10px] uppercase tracking-wide text-zinc-500">Target</div>
                              <div className="mt-0.5 break-words font-semibold text-zinc-100">{activeDetail?.name ?? detail.name}</div>
                            </div>
                            <div className="flex flex-wrap items-center gap-2">
                              <PriorityBadge priority={activePriority} />
                              {agentOSData.run_state && (
                                <span className="rounded border border-zinc-700 bg-black/20 px-2 py-0.5 text-[10px] font-semibold text-zinc-300">
                                  {agentOSData.run_state.phase_status}
                                </span>
                              )}
                            </div>
                            <div className="text-zinc-400">Next: {activeNextRole || 'n/a'}</div>
                            {agentOSData.run_state?.current_owner && (
                              <div className="text-zinc-400">Owner: {agentOSData.run_state.current_owner}</div>
                            )}
                            {(() => {
                              const parsed = parseSatisfiabilityReason(activeDecisionReason)
                              return parsed.primary ? (
                                <div className="line-clamp-2 text-[11px] text-zinc-500">{parsed.primary}</div>
                              ) : null
                            })()}
                            <div className="pt-1">
                              <button
                                type="button"
                                onClick={openJudgeChat}
                                className="rounded border border-fuchsia-500/40 bg-fuchsia-500/10 px-3 py-1.5 text-[11px] font-semibold text-fuchsia-200 hover:bg-fuchsia-500/20"
                              >
                                AI と相談する
                              </button>
                            </div>
                            {activeJudgeRecommendation && (
                              <div className="rounded border border-fuchsia-500/25 bg-fuchsia-500/10 p-2.5">
                                <div className="mb-2 flex items-center justify-between gap-2">
                                  <div>
                                    <div className="text-[10px] uppercase tracking-wide text-fuchsia-200">Judge Advisory</div>
                                    <div className="mt-0.5 text-[11px] font-semibold text-zinc-100">
                                      {activeJudgeRecommendation.decision}
                                      {activeJudgeRecommendation.suggested_action_label ? ` -> ${activeJudgeRecommendation.suggested_action_label}` : ''}
                                    </div>
                                  </div>
                                  <span className="rounded border border-fuchsia-400/30 bg-fuchsia-500/10 px-2 py-0.5 text-[9px] font-bold uppercase text-fuchsia-100">
                                    {activeJudgeRecommendation.confidence}
                                  </span>
                                </div>
                                <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-[10px] text-zinc-400">
                                  <span>Critical: <span className="text-zinc-200">{activeJudgeRecommendation.critical_count}</span></span>
                                  <span>Major: <span className="text-zinc-200">{activeJudgeRecommendation.major_count}</span></span>
                                  <span>Minor: <span className="text-zinc-200">{activeJudgeRecommendation.minor_count}</span></span>
                                  {activeJudgeRecommendation.suggested_return_phase && (
                                    <span>Likely return: <span className="text-zinc-200">{activeJudgeRecommendation.suggested_return_phase}</span></span>
                                  )}
                                </div>
                                {activeJudgeRecommendation.counts_note && (
                                  <div className="mt-2 text-[10px] text-amber-200/90">
                                    {activeJudgeRecommendation.counts_note}
                                  </div>
                                )}
                                {activeJudgeRecommendation.review_verdict && (
                                  <div className="mt-2 text-[11px] text-zinc-300">
                                    Review verdict: <span className="text-zinc-100">{activeJudgeRecommendation.review_verdict}</span>
                                  </div>
                                )}
                                {activeJudgeRecommendation.suggested_return_phase && (
                                  <div className="mt-2 rounded border border-zinc-800/80 bg-black/20 p-2 text-[10px] text-zinc-400">
                                    <div className="mb-1 uppercase tracking-wide text-zinc-500">Return Target Preview</div>
                                    <div className="grid gap-1">
                                      <div>
                                        Role: <span className="text-zinc-100">{activeJudgeRecommendation.target_role || 'n/a'}</span>
                                        {' / '}
                                        Exec: <span className="text-zinc-100">{activeJudgeRecommendation.target_execution_type || 'n/a'}</span>
                                      </div>
                                      <div>
                                        Provider: <span className="text-zinc-100">{activeJudgeRecommendation.target_provider || 'n/a'}</span>
                                        {activeJudgeRecommendation.target_model ? (
                                          <>
                                            {' / '}
                                            Model: <span className="font-mono text-zinc-100">{activeJudgeRecommendation.target_model}</span>
                                          </>
                                        ) : null}
                                      </div>
                                      <div>
                                        Specialist: <span className="text-zinc-100">{activeJudgeRecommendation.target_specialist_code || 'n/a'}</span>
                                        {activeJudgeRecommendation.target_specialist_mode ? (
                                          <>
                                            {' / '}
                                            Mode: <span className="text-zinc-100">{activeJudgeRecommendation.target_specialist_mode}</span>
                                          </>
                                        ) : null}
                                      </div>
                                    </div>
                                  </div>
                                )}
                                <div className="mt-2 text-[11px] text-zinc-400">{activeJudgeRecommendation.rationale}</div>
                                <div className="mt-3">
                                  <button
                                    type="button"
                                    onClick={() => {
                                      if (judgeChatMessages.length === 0) {
                                        setJudgeChatMessages([{
                                          role: 'assistant',
                                          content: 'レビューを読みました。何から始めましょうか？Critical や Major の問題を一つずつ整理してお手伝いします。',
                                        }])
                                      }
                                      setJudgeChatOpen(true)
                                    }}
                                    className="rounded border border-fuchsia-500/40 bg-fuchsia-500/10 px-3 py-1.5 text-[11px] font-semibold text-fuchsia-200 hover:bg-fuchsia-500/20"
                                  >
                                    AI と相談する
                                  </button>
                                </div>
                                {activeJudgeRecommendation.human_owned_blocker && (
                                  <div className="mt-2 rounded border border-amber-500/30 bg-amber-500/10 p-2 text-[11px] text-amber-100">
                                    Human-owned blocker: {activeJudgeRecommendation.human_blocker_summary ?? 'Manual confirmation is required before Builder can make progress.'}
                                  </div>
                                )}
                                <div className="mt-2 text-[10px] text-zinc-500">
                                  Advisory only. Judge still decides, records the decision in improve.md, reflects the findings, and then returns the run to Planner or Builder when needed.
                                </div>
                              </div>
                            )}
                            {activeRunExecutionState && (
                              <div className="rounded border border-amber-500/30 bg-amber-500/10 p-2.5">
                                <div className="flex items-center justify-between gap-2">
                                  <div>
                                    <div className="text-[10px] uppercase tracking-wide text-amber-200">Running Now</div>
                                    <div className="mt-0.5 text-[11px] font-semibold text-zinc-100">{activeRunExecutionState.actionId}</div>
                                  </div>
                                  <span className="rounded border border-amber-400/30 bg-amber-500/10 px-2 py-0.5 text-[9px] font-bold uppercase text-amber-100">
                                    {activeExecutionElapsed ? activeExecutionElapsed : 'Running'}
                                  </span>
                                </div>
                                <div className="mt-2 text-[11px] text-zinc-400">
                                  Agent OS is executing this run. The latest result panel will update after completion.
                                </div>
                              </div>
                            )}
                            {selectedPhaseContextAction && selectedTaxonomy && activeTargetName ? (
                              <div className="rounded border border-emerald-500/25 bg-black/20 p-2.5">
                                <div className="mb-2 flex items-center justify-between gap-2">
                                  <div>
                                    <div className="text-[10px] uppercase tracking-wide text-emerald-300">Next Action</div>
                                    <div className="mt-0.5 text-[11px] font-semibold text-zinc-100">{selectedPhaseContextAction.label}</div>
                                  </div>
                                  {selectedPhaseContextAction.id === primaryExecutableAction?.id && (
                                    <span className="rounded border border-emerald-500/30 bg-emerald-500/10 px-2 py-0.5 text-[9px] font-bold uppercase text-emerald-100">
                                      Recommended
                                    </span>
                                  )}
                                </div>
                                <select
                                  value={selectedPhaseContextAction.id}
                                  onChange={(e) => setPhaseContextActionId(e.target.value)}
                                  className="mb-2 w-full rounded border border-zinc-700 bg-zinc-950 px-2 py-2 text-[11px] text-zinc-100"
                                >
                                  {phaseContextActions.map((action) => (
                                    <option key={action.id} value={action.id}>
                                      {action.primary ? '[Recommended] ' : ''}{action.label}
                                    </option>
                                  ))}
                                </select>
                                <div className="mb-2 text-[11px] text-zinc-400">{selectedPhaseContextAction.description}</div>
                                {selectedPhaseContextAction.comment_artifact && (
                                  <div className="mb-2 rounded border border-zinc-800 bg-zinc-950/50 p-2">
                                    <div className="mb-1 text-[10px] text-zinc-500">
                                      Comment artifact: <span className="font-mono text-zinc-300">{selectedPhaseContextAction.comment_artifact}</span>
                                    </div>
                                    <textarea
                                      value={rerunComments[selectedPhaseContextAction.id] ?? ''}
                                      onChange={(e) => {
                                        const next = e.target.value
                                        setRerunComments((current) => ({ ...current, [selectedPhaseContextAction.id]: next }))
                                        if (savedCommentByAction[selectedPhaseContextAction.id] && savedCommentByAction[selectedPhaseContextAction.id] !== next.trim()) {
                                          setSavedCommentByAction((current) => {
                                            const copy = { ...current }
                                            delete copy[selectedPhaseContextAction.id]
                                            return copy
                                          })
                                        }
                                      }}
                                      className="min-h-24 w-full rounded border border-zinc-700 bg-zinc-950 p-2 text-[11px] text-zinc-200"
                                      placeholder={`Comment to save into ${selectedPhaseContextAction.comment_artifact}`}
                                    />
                                    <div className="mt-2 flex flex-wrap items-center justify-between gap-2">
                                      <div className="text-[10px] text-zinc-500">
                                        {savedCommentByAction[selectedPhaseContextAction.id] === (rerunComments[selectedPhaseContextAction.id] ?? '').trim() && (rerunComments[selectedPhaseContextAction.id] ?? '').trim() !== ''
                                          ? 'Saved to artifact.'
                                          : 'Save the comment before running when feedback is required.'}
                                      </div>
                                      <button
                                        type="button"
                                        onClick={() => void saveRerunComment(selectedPhaseContextAction, selectedTaxonomy, activeTargetName)}
                                        disabled={savingActionId !== null || ((rerunComments[selectedPhaseContextAction.id] ?? '').trim() === '') || savedCommentByAction[selectedPhaseContextAction.id] === (rerunComments[selectedPhaseContextAction.id] ?? '').trim()}
                                        className="rounded border border-emerald-500/30 bg-emerald-500/15 px-3 py-1.5 text-[10px] font-semibold text-emerald-100 disabled:border-zinc-800 disabled:bg-zinc-900 disabled:text-zinc-500"
                                      >
                                        {savingActionId === selectedPhaseContextAction.id ? 'Saving...' : 'Save Comment'}
                                      </button>
                                    </div>
                                  </div>
                                )}
                                <button
                                  type="button"
                                  onClick={() => void executeAction(selectedPhaseContextAction, selectedTaxonomy, activeTargetName)}
                                  disabled={!selectedPhaseContextAction.enabled || isActiveRunBusy}
                                  className="w-full rounded border border-emerald-500/30 bg-emerald-500/15 px-3 py-2 text-[11px] font-bold text-emerald-50 transition-colors hover:bg-emerald-500/20 disabled:border-zinc-800 disabled:bg-zinc-900 disabled:text-zinc-500"
                                >
                                  {activeRunExecutionId === selectedPhaseContextAction.id ? 'Running...' : selectedPhaseContextAction.label}
                                </button>
                                {selectedPhaseContextAction.command && (
                                  <div className="mt-2 rounded border border-zinc-800 bg-zinc-950/50 p-2">
                                    <div className="mb-1 flex items-start justify-between gap-2 text-[10px] text-zinc-500">
                                      <span>Action Command</span>
                                      <CopyButton text={selectedPhaseContextAction.command} />
                                    </div>
                                    <div className="line-clamp-2 whitespace-pre-wrap break-words font-mono text-[10px] text-zinc-300">{selectedPhaseContextAction.command}</div>
                                  </div>
                                )}
                              </div>
                            ) : activeOperatorCommand && (
                              <div className="rounded border border-zinc-800 bg-black/20 p-2">
                                <div className="mb-1 flex items-start justify-between gap-2 text-[10px] text-zinc-500">
                                  <span>Recommended Command</span>
                                  <CopyButton text={activeOperatorCommand} />
                                </div>
                                <div className="line-clamp-3 whitespace-pre-wrap break-words font-mono text-[10px] text-zinc-300">{activeOperatorCommand}</div>
                              </div>
                            )}
                            {selectedTaxonomy && activeTargetName && (
                              <div className="rounded border border-cyan-500/20 bg-cyan-500/5 p-2.5">
                                <div className="mb-2 flex items-center justify-between gap-2">
                                  <div>
                                    <div className="text-[10px] uppercase tracking-wide text-cyan-300">Auto-Loop</div>
                                    <div className="mt-0.5 text-[11px] text-zinc-400">Run the default APSF loop for this run or child run.</div>
                                  </div>
                                  <span className={`rounded border px-2 py-0.5 text-[9px] font-bold uppercase ${
                                    autoLoopStatus?.running
                                      ? autoLoopStatus.stop_pending
                                        ? 'border-amber-400/30 bg-amber-500/10 text-amber-100'
                                        : 'border-emerald-400/30 bg-emerald-500/10 text-emerald-100'
                                      : 'border-zinc-700 bg-zinc-900 text-zinc-400'
                                  }`}>
                                    {autoLoopLoading ? 'Checking' : autoLoopStatus?.running ? (autoLoopStatus.stop_pending ? 'Stop Pending' : 'Running') : 'Idle'}
                                  </span>
                                </div>
                                <div className="mb-2 rounded border border-zinc-800 bg-black/20 px-3 py-2">
                                  <div className="grid gap-2 text-[10px] md:grid-cols-3">
                                    <div>
                                      <div className="uppercase tracking-wide text-zinc-500">Current Worker</div>
                                      <div className="mt-0.5 font-semibold text-zinc-100">{activeOwner || 'Unknown'}</div>
                                    </div>
                                    <div>
                                      <div className="uppercase tracking-wide text-zinc-500">Status</div>
                                      <div className="mt-0.5 font-semibold text-zinc-200">{ownerStatusLabel}</div>
                                    </div>
                                    <div>
                                      <div className="uppercase tracking-wide text-zinc-500">Elapsed</div>
                                      <div className="mt-0.5 font-mono text-zinc-200">{(ownerWorkingNow ? (activeExecutionElapsed ?? activePhaseElapsed) : activePhaseElapsed) || '00:00'}</div>
                                    </div>
                                  </div>
                                </div>
                                <div className="flex flex-wrap gap-2">
                                  <button
                                    type="button"
                                    onClick={openAutoLoopLaunchModal}
                                    disabled={autoLoopLoading || autoLoopMutating !== null || autoLoopStatus?.running === true}
                                    className="rounded border border-cyan-500/30 bg-cyan-500/15 px-3 py-1.5 text-[10px] font-semibold text-cyan-100 disabled:border-zinc-800 disabled:bg-zinc-900 disabled:text-zinc-500"
                                  >
                                    {autoLoopMutating === 'start' ? 'Starting...' : 'Start Auto-Loop'}
                                  </button>
                                  <button
                                    type="button"
                                    onClick={() => void openRallyConversation()}
                                    disabled={autoLoopLoading}
                                    className="rounded border border-indigo-500/30 bg-indigo-500/15 px-3 py-1.5 text-[10px] font-semibold text-indigo-100 disabled:border-zinc-800 disabled:bg-zinc-900 disabled:text-zinc-500"
                                  >
                                    View Rally
                                  </button>
                                  <button
                                    type="button"
                                    onClick={() => void requestAutoLoopStop(selectedTaxonomy, activeTargetName)}
                                    disabled={autoLoopLoading || autoLoopMutating !== null || autoLoopStatus?.running !== true || autoLoopStatus?.stop_pending === true}
                                    className="rounded border border-amber-500/30 bg-amber-500/15 px-3 py-1.5 text-[10px] font-semibold text-amber-100 disabled:border-zinc-800 disabled:bg-zinc-900 disabled:text-zinc-500"
                                  >
                                    {autoLoopMutating === 'stop' ? 'Requesting...' : 'Request Stop'}
                                  </button>
                                  <button
                                    type="button"
                                    onClick={() => void cancelAutoLoopStop(selectedTaxonomy, activeTargetName)}
                                    disabled={autoLoopLoading || autoLoopMutating !== null || autoLoopStatus?.stop_pending !== true}
                                    className="rounded border border-zinc-700 bg-zinc-900 px-3 py-1.5 text-[10px] font-semibold text-zinc-200 disabled:border-zinc-800 disabled:bg-zinc-900 disabled:text-zinc-500"
                                  >
                                    {autoLoopMutating === 'cancel' ? 'Cancelling...' : 'Cancel Stop'}
                                  </button>
                                </div>
                              </div>
                            )}
                          </div>
                        </div>

                        <div className="rounded border border-zinc-800 bg-zinc-900/40 p-4">
                          <div className="mb-2 flex items-center justify-between gap-2">
                            <div>
                              <div className="text-[11px] font-bold uppercase tracking-[0.2em] text-zinc-400">Assignment</div>
                              <div className="mt-1 text-[10px] text-zinc-500">Phase, provider, specialist in one pass.</div>
                            </div>
                            {activeAssignment && <AssignmentModeBadge mode={activeAssignment.execution.mode} />}
                          </div>
                          {activeAssignment && activeSpecialist ? (
                            <div className="space-y-2 text-xs">
                              <div className="rounded border border-zinc-800 bg-black/20 p-2">
                                <div className="text-[10px] uppercase tracking-wide text-zinc-500">Agent</div>
                                <div className="mt-0.5 font-semibold text-zinc-100">{activeAssignment.role || 'unset'}</div>
                                <div className="mt-1 text-zinc-400">{activeAssignment.execution.execution_type || 'unset'}</div>
                              </div>
                              <div className="rounded border border-zinc-800 bg-black/20 p-2">
                                <div className="text-[10px] uppercase tracking-wide text-zinc-500">Provider / Model</div>
                                <div className="mt-0.5 text-zinc-200">{activeAssignment.model.provider || 'unset'}</div>
                                <div className="font-mono text-[10px] text-zinc-400">{activeAssignment.model.model || 'unset'}</div>
                              </div>
                              <div className={`rounded border bg-black/20 p-2 ${activeSpecialist.has_gap ? 'border-red-500/30' : 'border-zinc-800'}`}>
                                <div className="text-[10px] uppercase tracking-wide text-zinc-500">Specialist</div>
                                <div className="mt-0.5 font-semibold text-zinc-100">{activeSpecialist.specialist_code || '(generic)'}</div>
                                <div className={activeSpecialist.has_gap ? 'text-red-300' : 'text-zinc-400'}>
                                  {activeSpecialist.has_gap ? 'Gap detected' : 'No gap'}
                                </div>
                              </div>
                              {selectedTaxonomy && targetRun && (
                                <div className="space-y-2 rounded border border-amber-500/20 bg-amber-500/5 p-2">
                                  <div className="text-[10px] uppercase tracking-wide text-zinc-500">Change Assignment</div>
                                  <div className="flex gap-1.5">
                                    {(['Planner', 'Builder', 'Critic'] as const).map((role) => {
                                      const phase = role === 'Planner' ? 'PLAN_NEEDED' : role === 'Builder' ? 'BUILD_NEEDED' : 'REVIEW_NEEDED'
                                      return (
                                        <button
                                          key={role}
                                          type="button"
                                          onClick={() => void openSpecialistSelectionForPhase(phase)}
                                          disabled={isActiveRunBusy}
                                          className="flex-1 rounded border border-amber-500/40 bg-amber-500/10 px-2 py-1.5 text-[11px] font-semibold text-amber-100 hover:bg-amber-500/20 disabled:border-zinc-800 disabled:bg-zinc-900 disabled:text-zinc-500"
                                        >
                                          {role}
                                        </button>
                                      )
                                    })}
                                  </div>
                                  {detail && targetRun !== detail.name && (
                                    <div className="rounded border border-indigo-500/30 bg-indigo-500/10 px-3 py-2 text-[10px] text-indigo-100">
                                      Targeting child run: <span className="font-mono">{targetRun}</span>
                                    </div>
                                  )}
                                  {isActiveRunBusy && (
                                    <div className="rounded border border-yellow-500/20 bg-yellow-500/5 px-3 py-2 text-[10px] text-yellow-100">
                                      Specialist changes are blocked while this run is executing.
                                    </div>
                                  )}
                                </div>
                              )}
                            </div>
                          ) : (
                            <div className="text-xs text-zinc-500">Assignment summary unavailable.</div>
                          )}
                        </div>

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
                                <div className="mt-1 line-clamp-3 text-[11px] text-zinc-400">
                                  {summarizeExecutionOutcome(latestRunExecution.stdout_summary, latestRunExecution.stderr_summary)}
                                </div>
                              </div>
                            </div>
                          ) : (
                            <div className="text-xs text-zinc-500">No Agent OS operator execution captured yet.</div>
                          )}
                        </div>

                      </div>
                      {showDetailedAssignmentCard && (() => {
                        const assignmentDetail = targetDetail ?? detail
                        if (!assignmentDetail) return null
                        const assignment = assignmentDetail.assignment_summary
                        const specialist = assignmentDetail.specialist_visibility
                        return (
                          <div className="rounded border border-emerald-500/20 bg-emerald-500/5 p-4">
                            <div className="mb-3 flex items-center justify-between gap-3">
                              <div>
                                <div className="text-[11px] font-bold uppercase tracking-[0.2em] text-emerald-300">Assignment</div>
                                <div className="mt-1 text-[10px] text-zinc-500">Current phase selection for agent, provider/model, and specialist.</div>
                              </div>
                              <PhaseBadge phase={assignmentDetail.phase} />
                            </div>
                            <div className="grid gap-3 lg:grid-cols-3">
                              <div className="rounded border border-zinc-800 bg-black/20 p-3 text-xs">
                                <div className="mb-2 flex items-center justify-between gap-2">
                                  <div className="text-[10px] font-bold uppercase tracking-[0.2em] text-zinc-500">Agent</div>
                                  <AssignmentModeBadge mode={assignment.execution.mode} />
                                </div>
                                <div className="text-[11px] text-zinc-500 uppercase tracking-wide">Role</div>
                                <div className="mt-0.5 font-semibold text-zinc-100">{assignment.role || '—'}</div>
                                <div className="mt-2 text-[11px] text-zinc-500 uppercase tracking-wide">Execution</div>
                                <div className="mt-0.5 text-zinc-200">{assignment.execution.execution_type}</div>
                                <div className="mt-2 text-[11px] text-zinc-500 uppercase tracking-wide">Target</div>
                                <div className="mt-0.5 font-mono text-[11px] text-zinc-200">{assignment.execution.target || '—'}</div>
                                {assignment.execution.workspace && (
                                  <>
                                    <div className="mt-2 text-[11px] text-zinc-500 uppercase tracking-wide">Workspace</div>
                                    <div className="mt-0.5 font-mono text-[11px] text-zinc-400">{assignment.execution.workspace}</div>
                                  </>
                                )}
                                <div className="mt-2 text-[10px] text-zinc-500">{assignment.execution.reason}</div>
                              </div>

                              <div className="rounded border border-zinc-800 bg-black/20 p-3 text-xs">
                                <div className="mb-2 flex items-center justify-between gap-2">
                                  <div className="text-[10px] font-bold uppercase tracking-[0.2em] text-zinc-500">Provider</div>
                                  <AssignmentModeBadge mode={assignment.model.mode} />
                                </div>
                                <div className="text-[11px] text-zinc-500 uppercase tracking-wide">Provider</div>
                                <div className="mt-0.5 font-semibold text-zinc-100">{assignment.model.provider || '—'}</div>
                                <div className="mt-2 text-[11px] text-zinc-500 uppercase tracking-wide">Model</div>
                                <div className="mt-0.5 font-mono text-[11px] text-zinc-200">{assignment.model.model || '—'}</div>
                                <div className="mt-2 text-[10px] text-zinc-500">{assignment.model.reason}</div>
                              </div>

                              <div className={`rounded border bg-black/20 p-3 text-xs ${specialist.has_gap ? 'border-red-500/30' : 'border-zinc-800'}`}>
                                <div className="mb-2 flex items-center justify-between gap-2">
                                  <div className="text-[10px] font-bold uppercase tracking-[0.2em] text-zinc-500">Specialist</div>
                                  <AssignmentModeBadge mode={specialist.mode} />
                                </div>
                                <div className="text-[11px] text-zinc-500 uppercase tracking-wide">Code</div>
                                <div className="mt-0.5 font-semibold text-zinc-100">{specialist.specialist_code || '(generic)'}</div>
                                <div className="mt-2 text-[11px] text-zinc-500 uppercase tracking-wide">Gap</div>
                                <div className={`mt-0.5 font-semibold ${specialist.has_gap ? 'text-red-300' : 'text-zinc-300'}`}>{specialist.has_gap ? 'Yes' : 'No'}</div>
                                <div className="mt-2 text-[10px] text-zinc-500">{specialist.reason}</div>
                                {specialistCandidates && selectedTaxonomy && targetRun && (
                                  <div className="mt-3 space-y-2">
                                    <button
                                      type="button"
                                      onClick={() => void openSpecialistSelectionModal(specialist.specialist_code || specialistCandidates.current_code || '')}
                                      className="w-full rounded border border-amber-500/40 bg-amber-500/10 px-3 py-2 text-[11px] font-semibold text-amber-100 hover:bg-amber-500/20"
                                    >
                                      Select Specialist
                                    </button>
                                    {detail && targetRun !== detail.name && (
                                      <div className="rounded border border-indigo-500/30 bg-indigo-500/10 px-3 py-2 text-[10px] text-indigo-100">
                                        Targeting child run: <span className="font-mono">{targetRun}</span>
                                      </div>
                                    )}
                                    <div className="text-[10px] text-zinc-500">
                                      Inspect the current library, assign an existing specialist, use generic explicitly, or branch into new specialist authoring.
                                    </div>
                                  </div>
                                )}
                              </div>
                            </div>
                          </div>
                        )
                      })()}

                      {/* Legacy run banner — shown when no Agent OS v1 artifacts exist at all */}
                      {!agentOSData.run_state && agentOSData.gate_results.length === 0 && !agentOSData.artifact_manifest && (
                        <div className="rounded border border-dashed border-zinc-700 bg-zinc-900/30 p-5 text-center">
                          <div className="text-xs font-semibold text-zinc-400">Agent OS state not initialized</div>
                          <div className="mt-1 text-[11px] text-zinc-600">This run pre-dates the state-first workflow, or <code className="font-mono">apsf act</code> has not been called yet.</div>
                          <div className="mt-2 text-[10px] text-zinc-700">Expected: <code className="font-mono">run_state.json</code> / <code className="font-mono">artifact_manifest.json</code></div>
                        </div>
                      )}

                      {/* Run State */}
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

                      {/* Gate Results: show only when something failed */}
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

                      {/* Artifact Manifest */}
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

                      {/* Force Audit (optional) */}
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

                      {/* Recovery (read-only) */}
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

                      {selectedTaxonomy && targetRun && (
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
                              const toneClass = isStrongAction
                                ? 'border-red-500/25 bg-red-500/5'
                                : 'border-zinc-800 bg-zinc-900/30'
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
                      )}
                    </>
                  )}
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
              )}
            </section>

          </>
        )}
      </main>

      {judgeChatOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4">
          <div className="flex h-[75vh] w-full max-w-2xl flex-col rounded-lg border border-fuchsia-500/30 bg-zinc-950 shadow-2xl">
            {/* Header */}
            <div className="flex items-center justify-between border-b border-zinc-800 px-4 py-3">
              <div>
                <div className="text-[11px] uppercase tracking-wide text-fuchsia-300">Judge AI Assistant</div>
                <div className="text-[13px] font-semibold text-zinc-100">{activeTargetName}</div>
              </div>
              <button
                type="button"
                onClick={() => setJudgeChatOpen(false)}
                className="rounded p-1 text-zinc-400 hover:bg-zinc-800 hover:text-zinc-100"
              >
                ✕
              </button>
            </div>
            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-4 space-y-3">
              {judgeChatMessages.map((msg, i) => (
                <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                  <div className={`max-w-[85%] rounded-lg px-3 py-2 text-[12px] leading-relaxed ${
                    msg.role === 'user'
                      ? 'bg-fuchsia-500/20 text-fuchsia-100'
                      : 'bg-zinc-800 text-zinc-200'
                  }`}>
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>{msg.content}</ReactMarkdown>
                  </div>
                </div>
              ))}
              {judgeChatLoading && (
                <div className="flex justify-start">
                  <div className="rounded-lg bg-zinc-800 px-3 py-2 text-[12px] text-zinc-400">考え中...</div>
                </div>
              )}
            </div>
            {/* Save last AI message as comment */}
            {judgeChatMessages.length > 0 && judgeChatMessages[judgeChatMessages.length - 1].role === 'assistant' && suggestedJudgeAction && (
              <div className="border-t border-zinc-800 px-4 py-2">
                <button
                  type="button"
                  onClick={() => {
                    const lastAI = judgeChatMessages[judgeChatMessages.length - 1].content
                    setRerunComments((c) => ({ ...c, [suggestedJudgeAction.id]: lastAI }))
                    setJudgeChatOpen(false)
                  }}
                  className="text-[11px] text-fuchsia-300 underline hover:text-fuchsia-100"
                >
                  最後の AI メッセージをコメント欄に貼り付ける
                </button>
              </div>
            )}
            {/* Input */}
            <div className="border-t border-zinc-800 p-3 flex gap-2">
              <textarea
                className="flex-1 resize-none rounded border border-zinc-700 bg-zinc-900 px-3 py-2 text-[12px] text-zinc-100 placeholder-zinc-500 focus:border-fuchsia-500/50 focus:outline-none"
                rows={2}
                placeholder="Judge として決定・質問を入力..."
                value={judgeChatInput}
                onChange={(e) => setJudgeChatInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault()
                    void sendJudgeChatMessage()
                  }
                }}
              />
              <button
                type="button"
                onClick={() => void sendJudgeChatMessage()}
                disabled={judgeChatLoading || !judgeChatInput.trim()}
                className="rounded border border-fuchsia-500/30 bg-fuchsia-500/15 px-4 text-[12px] font-semibold text-fuchsia-200 disabled:opacity-40 hover:bg-fuchsia-500/25"
              >
                送信
              </button>
            </div>
          </div>
        </div>
      )}
      {modalConfig && (
        <ConfirmModal
          key={`${modalConfig.title}-${modalConfig.inputDefaultValue ?? ''}-${modalConfig.message}`}
          config={modalConfig}
          onCancel={() => setModalConfig(null)}
        />
      )}
      {viewerConfigModalOpen && (
        <ViewerConfigModal
          config={viewerConfig}
          savingKey={viewerConfigSavingKey}
          onClose={() => setViewerConfigModalOpen(false)}
          onUpdate={updateViewerConfig}
        />
      )}
      {specialistModalOpen && specialistCandidates && selectedTaxonomy && targetRun && (
        <SpecialistSelectionModal
          taxonomy={selectedTaxonomy}
          runName={targetRun}
          candidatesData={specialistCandidates}
          initialCode={specialistModalSelectedCode}
          createResult={createdSpecialistResult}
          onClose={() => {
            setCreatedSpecialistResult(null)
            setSpecialistModalOpen(false)
          }}
          onConfirm={handleConfirmSpecialist}
          onCreateNew={(suggestedCode) => {
            setSpecialistModalSelectedCode(suggestedCode ?? '')
            setSpecialistModalOpen(false)
            setCreateSpecialistModalOpen(true)
          }}
        />
      )}
      {autoLoopLaunchModalOpen && selectedTaxonomy && targetRun && (
        <AutoLoopLaunchModal
          taxonomy={selectedTaxonomy}
          runName={targetRun}
          phase={activeDetailPhase || ''}
          assignment={activeAssignment}
          specialist={activeSpecialist}
          starting={autoLoopMutating === 'start'}
          onClose={() => setAutoLoopLaunchModalOpen(false)}
          onChangeAssignment={() => {
            setAutoLoopLaunchModalOpen(false)
            void openSpecialistSelectionForPhase(activeDetailPhase || 'REVIEW_NEEDED')
          }}
          onStart={async (buildScript) => {
            const runName = targetDetail?.name ?? targetRun
            await startAutoLoop(selectedTaxonomy, runName, buildScript)
            setAutoLoopLaunchModalOpen(false)
          }}
        />
      )}
      {rallyModalOpen && targetRun && (
        <RallyConversationModal
          runName={targetRun}
          messages={rallyMessages}
          loading={rallyLoading}
          onClose={() => setRallyModalOpen(false)}
          autoLoopRunning={autoLoopStatus?.running ?? false}
          stopPending={autoLoopStatus?.stop_pending ?? false}
          currentOwner={agentOSData?.run_state?.current_owner ?? ''}
          elapsedDisplay={(ownerWorkingNow ? (activeExecutionElapsed ?? activePhaseElapsed) : activePhaseElapsed) ?? null}
          specialistCodes={rallySpecialistCodes}
        />
      )}
      {createSpecialistModalOpen && specialistCandidates && selectedTaxonomy && targetRun && (
        <CreateSpecialistModal
          taxonomy={selectedTaxonomy}
          runName={targetRun}
          role={specialistCandidates.role as 'Planner' | 'Builder' | 'Critic'}
          suggestedCode={specialistModalSelectedCode}
          onClose={() => {
            setCreateSpecialistModalOpen(false)
            setSpecialistModalOpen(true)
          }}
          onCreated={handleCreatedSpecialist}
        />
      )}
      {artifactModalOpen && detail && (
        <ArtifactReferenceModal
          artifacts={targetDetail?.artifacts ?? detail.artifacts}
          selectedArtifact={selectedArtifact}
          artifactContent={artifactContent}
          runName={targetDetail?.name ?? detail.name}
          onClose={() => setArtifactModalOpen(false)}
          onSelect={(name) => void fetchArtifact(name)}
        />
      )}
      {selectedExecutionLog && <ExecutionLogModal job={selectedExecutionLog} onClose={() => setSelectedExecutionLog(null)} />}

      {/* ── Auto-loop stop notification toast ──────────────────────── */}
      {loopStopToast && (
        <div className="fixed bottom-5 right-5 z-[200] w-80 animate-in fade-in slide-in-from-bottom-3">
          <div className={`rounded-xl border shadow-2xl shadow-black/60 px-4 py-3 ${
            loopStopToast.lastExit !== null && loopStopToast.lastExit !== 0
              ? 'border-red-500/40 bg-red-950/90'
              : 'border-zinc-700 bg-zinc-900/95'
          }`}>
            <div className="flex items-start justify-between gap-3">
              <div className="min-w-0 flex-1">
                <div className={`text-[11px] font-bold uppercase tracking-wide ${
                  loopStopToast.lastExit !== null && loopStopToast.lastExit !== 0
                    ? 'text-red-300'
                    : 'text-zinc-300'
                }`}>
                  {loopStopToast.lastExit !== null && loopStopToast.lastExit !== 0
                    ? '⚠ Auto-Loop Stopped (Error)'
                    : '■ Auto-Loop Stopped'}
                </div>
                <div className="mt-1 space-y-0.5 text-[10px] text-zinc-400">
                  {loopStopToast.stopReason && (
                    <div>Reason: <span className="font-mono text-zinc-200">{loopStopToast.stopReason}</span></div>
                  )}
                  {loopStopToast.lastExit !== null && (
                    <div>Exit: <span className={`font-mono ${loopStopToast.lastExit !== 0 ? 'text-red-300' : 'text-emerald-300'}`}>{loopStopToast.lastExit}</span></div>
                  )}
                </div>
              </div>
              <button
                onClick={() => setLoopStopToast(null)}
                className="flex-shrink-0 rounded border border-zinc-700 bg-zinc-800 px-2 py-1 text-[10px] text-zinc-400 hover:text-zinc-200"
              >
                ✕
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
