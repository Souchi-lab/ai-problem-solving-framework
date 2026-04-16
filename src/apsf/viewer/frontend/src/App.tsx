import { useCallback, useEffect, useRef, useState } from 'react'
import { ChevronRight, FileText, Terminal } from 'lucide-react'
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
  formatElapsedMs,
  parseSatisfiabilityReason,
  loadStoredStringArray,
} from './utils/formatting'
import {
  parseSpecialistCodes,
  mergeCreatedSpecialistCandidate,
} from './utils/specialist'
import {
  PhaseBadge,
  PriorityBadge,
  WorkflowProgress,
  SatisfiabilityWarning,
  CopyButton,
} from './components/badges'
import { SidebarPanel } from './components/panels/SidebarPanel'
import { DetailTab } from './components/panels/DetailTab'
import { ManagementTab } from './components/panels/ManagementTab'
import { AgentOSTab } from './components/panels/AgentOSTab'
import { ActivityTab } from './components/panels/ActivityTab'
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
        <SidebarPanel
          searchTerm={searchTerm}
          setSearchTerm={setSearchTerm}
          humanBlockerFilter={humanBlockerFilter}
          setHumanBlockerFilter={setHumanBlockerFilter}
          isLoadingRuns={isLoadingRuns}
          runsError={runsError}
          filteredRuns={filteredRuns}
          taxonomySections={taxonomySections}
          selectedRun={selectedRun}
          fetchRuns={fetchRuns}
          setIsLoadingRuns={setIsLoadingRuns}
          fetchDetail={fetchDetail}
          toggleOpenTaxonomy={toggleOpenTaxonomy}
          togglePinnedTaxonomy={togglePinnedTaxonomy}
          setSidebarOpen={setSidebarOpen}
          setViewerConfigModalOpen={setViewerConfigModalOpen}
        />
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
                <DetailTab
                  detail={detail}
                  targetDetail={targetDetail}
                  history={history}
                  historyRun={historyRun}
                  childRuns={childRuns}
                  activeTargetName={activeTargetName}
                  targetReworkCount={targetReworkCount}
                  improveDecisionActions={improveDecisionActions}
                  regularExecutableActions={regularExecutableActions}
                  regularHumanActions={regularHumanActions}
                  recommendedActionId={recommendedActionId}
                  selectedTaxonomy={selectedTaxonomy}
                  renderOperatorAction={renderOperatorAction}
                />
              ) : workspaceTab === 'management' ? (
                <ManagementTab
                  operatorFilter={operatorFilter}
                  setOperatorFilter={setOperatorFilter}
                  operatorRows={operatorRows}
                  targetDetail={targetDetail}
                  detail={detail}
                  selectedRun={selectedRun}
                  fetchDetail={fetchDetail}
                  executeMatrixAction={executeMatrixAction}
                  isRunExecuting={isRunExecuting}
                  executingActionForRun={executingActionForRun}
                  codexLoadingPreset={codexLoadingPreset}
                  codexTargetKey={codexTargetKey}
                  codexError={codexError}
                  codexResult={codexResult}
                  invokeCodexPreset={invokeCodexPreset}
                  getCodexPresetsForPhase={getCodexPresetsForPhase}
                />
              ) : workspaceTab === 'agent-os' ? (
                <AgentOSTab
                  agentOSLoading={agentOSLoading}
                  agentOSData={agentOSData}
                  executionResult={executionResult}
                  detail={detail}
                  targetDetail={targetDetail}
                  selectedTaxonomy={selectedTaxonomy}
                  targetRun={targetRun}
                  activePhase={activePhase}
                  activePriority={activePriority}
                  activeNextRole={activeNextRole}
                  activeDecisionReason={activeDecisionReason}
                  activeAssignment={activeAssignment}
                  activeSpecialist={activeSpecialist}
                  activeJudgeRecommendation={activeJudgeRecommendation}
                  activeRunExecutionState={activeRunExecutionState}
                  activeRunExecutionId={activeRunExecutionId}
                  activeExecutionElapsed={activeExecutionElapsed}
                  activePhaseElapsed={activePhaseElapsed}
                  isActiveRunBusy={isActiveRunBusy}
                  activeOwner={activeOwner}
                  ownerStatusLabel={ownerStatusLabel}
                  ownerWorkingNow={ownerWorkingNow}
                  activeOperatorCommand={activeOperatorCommand}
                  activeDetail={activeDetail}
                  latestRunExecution={latestRunExecution}
                  recentAgentOSExecutions={recentAgentOSExecutions}
                  failingGateResults={failingGateResults}
                  showDetailedAssignmentCard={showDetailedAssignmentCard}
                  selectedRecoveryCheckpointId={selectedRecoveryCheckpointId}
                  setSelectedRecoveryCheckpointId={setSelectedRecoveryCheckpointId}
                  selectedRecoverySnapshotId={selectedRecoverySnapshotId}
                  setSelectedRecoverySnapshotId={setSelectedRecoverySnapshotId}
                  selectedRecoveryApplyTraceId={selectedRecoveryApplyTraceId}
                  setSelectedRecoveryApplyTraceId={setSelectedRecoveryApplyTraceId}
                  agentOSFeedback={agentOSFeedback}
                  autoLoopStatus={autoLoopStatus}
                  autoLoopLoading={autoLoopLoading}
                  autoLoopMutating={autoLoopMutating}
                  judgeChatMessages={judgeChatMessages}
                  phaseContextActions={phaseContextActions}
                  selectedPhaseContextAction={selectedPhaseContextAction}
                  primaryExecutableAction={primaryExecutableAction}
                  setPhaseContextActionId={setPhaseContextActionId}
                  rerunComments={rerunComments}
                  setRerunComments={setRerunComments}
                  savedCommentByAction={savedCommentByAction}
                  setSavedCommentByAction={setSavedCommentByAction}
                  savingActionId={savingActionId}
                  specialistCandidates={specialistCandidates}
                  setViewerConfigModalOpen={setViewerConfigModalOpen}
                  openJudgeChat={openJudgeChat}
                  setJudgeChatMessages={setJudgeChatMessages}
                  setJudgeChatOpen={setJudgeChatOpen}
                  openAutoLoopLaunchModal={openAutoLoopLaunchModal}
                  openRallyConversation={openRallyConversation}
                  requestAutoLoopStop={requestAutoLoopStop}
                  cancelAutoLoopStop={cancelAutoLoopStop}
                  openSpecialistSelectionForPhase={openSpecialistSelectionForPhase}
                  openSpecialistSelectionModal={openSpecialistSelectionModal}
                  saveRerunComment={saveRerunComment}
                  executeAction={executeAction}
                  executeAgentOSAction={executeAgentOSAction}
                  executingActionForRun={executingActionForRun}
                  isRunExecuting={isRunExecuting}
                  openArtifactReferenceModal={openArtifactReferenceModal}
                  activeTargetName={activeTargetName}
                />
              ) : (
                <ActivityTab
                  jobsSearchTerm={jobsSearchTerm}
                  setJobsSearchTerm={setJobsSearchTerm}
                  filteredRecentExecutions={filteredRecentExecutions}
                  setSelectedExecutionLog={setSelectedExecutionLog}
                  executionResult={executionResult}
                  saveCommentResult={saveCommentResult}
                />
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
