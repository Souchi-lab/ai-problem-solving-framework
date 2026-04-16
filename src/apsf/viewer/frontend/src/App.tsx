import { useCallback, useEffect, useRef, useState } from 'react'
import { ChevronRight } from 'lucide-react'
import type {
  OperatorAction,
  RunDetail,
  MatrixRow,
  ExecutionResult,
  SaveCommentResult,
  ActionExecutionRecord,
  RunHistory,
  ViewerConfig,
  CodexBridgeResult,
  RunningExecutionState,
} from './types'
import {
  formatElapsedMs,
  loadStoredStringArray,
} from './utils/formatting'
import { OperatorActionCard } from './components/OperatorActionCard'
import { JudgeChatModal } from './components/JudgeChatModal'
import { WorkspaceHeader } from './components/WorkspaceHeader'
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
} from './api/runsApi'
import { apiUpdateViewerConfig } from './api/configApi'

// Hooks
import { useModalState } from './hooks/useModalState'
import { useAutoLoop } from './hooks/useAutoLoop'
import { useJudgeChat } from './hooks/useJudgeChat'
import { useRallyConversation } from './hooks/useRallyConversation'
import { useRunList } from './hooks/useRunList'
import { useSpecialists } from './hooks/useSpecialists'
import { useAgentOS } from './hooks/useAgentOS'

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
  // ── UI state ──────────────────────────────────────────────────────────────
  const [workspaceTab, setWorkspaceTab] = useState<'detail' | 'management' | 'activity' | 'agent-os'>('agent-os')
  const [operatorFilter, setOperatorFilter] = useState<'active' | 'recent' | 'all'>('active')
  const [humanBlockerFilter, setHumanBlockerFilter] = useState<'all' | 'blocked'>('all')
  const [pinnedTaxonomies, setPinnedTaxonomies] = useState<string[]>(() => loadStoredStringArray(TAXONOMY_PIN_STORAGE_KEY, ['work']))
  const [openTaxonomies, setOpenTaxonomies] = useState<string[]>(() => loadStoredStringArray(TAXONOMY_OPEN_STORAGE_KEY, ['work', 'fw-improvement', 'sochi-blocks']))
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [currentViewOpen, setCurrentViewOpen] = useState(false)
  const [searchTerm, setSearchTerm] = useState('')
  const [jobsSearchTerm, setJobsSearchTerm] = useState('')

  // ── Run selection state ───────────────────────────────────────────────────
  const [detail, setDetail] = useState<RunDetail | null>(null)
  const [selectedRun, setSelectedRun] = useState<string | null>(null)
  const [selectedTaxonomy, setSelectedTaxonomy] = useState<string | null>(null)
  const [targetRun, setTargetRun] = useState<string | null>(null)
  const [targetDetail, setTargetDetail] = useState<RunDetail | null>(null)
  const [history, setHistory] = useState<RunHistory | null>(null)
  const [historyRun, setHistoryRun] = useState<string | null>(null)

  // ── Artifact state ────────────────────────────────────────────────────────
  const [selectedArtifact, setSelectedArtifact] = useState<string | null>(null)
  const [artifactContent, setArtifactContent] = useState<string>('')

  // ── Execution state ───────────────────────────────────────────────────────
  const [executionResult, setExecutionResult] = useState<ExecutionResult | null>(null)
  const [selectedExecutionLog, setSelectedExecutionLog] = useState<ActionExecutionRecord | null>(null)
  const [saveCommentResult, setSaveCommentResult] = useState<SaveCommentResult | null>(null)
  const [phaseContextActionId, setPhaseContextActionId] = useState<string>('')
  const [executingRuns, setExecutingRuns] = useState<Record<string, RunningExecutionState>>({})
  const [executionNow, setExecutionNow] = useState(() => Date.now())
  const [savingActionId, setSavingActionId] = useState<string | null>(null)
  const [rerunComments, setRerunComments] = useState<Record<string, string>>({})
  const [savedCommentByAction, setSavedCommentByAction] = useState<Record<string, string>>({})

  // ── Codex state ───────────────────────────────────────────────────────────
  const [codexResult, setCodexResult] = useState<CodexBridgeResult | null>(null)
  const [codexError, setCodexError] = useState<string | null>(null)
  const [codexLoadingPreset, setCodexLoadingPreset] = useState<CodexBridgeResult['preset_id'] | null>(null)
  const [codexTargetKey, setCodexTargetKey] = useState<string | null>(null)

  // ── Refs ──────────────────────────────────────────────────────────────────
  const detailRequestIdRef = useRef(0)
  const refreshRequestIdRef = useRef(0)

  // ── Hooks ─────────────────────────────────────────────────────────────────
  const modals = useModalState()
  const {
    modalConfig, setModalConfig,
    viewerConfigModalOpen, setViewerConfigModalOpen,
    artifactModalOpen, setArtifactModalOpen,
    specialistModalOpen, setSpecialistModalOpen,
    createSpecialistModalOpen, setCreateSpecialistModalOpen,
    autoLoopLaunchModalOpen, setAutoLoopLaunchModalOpen,
    rallyModalOpen, setRallyModalOpen,
    judgeChatOpen, setJudgeChatOpen,
  } = modals

  const runList = useRunList()
  const {
    runs, isLoadingRuns, setIsLoadingRuns, runsError,
    matrixRows, setMatrixRows,
    recentExecutions, setRecentExecutions,
    viewerConfig, setViewerConfig,
    viewerConfigSavingKey, setViewerConfigSavingKey,
    fetchRuns,
    loadOperatorMatrix,
    loadRecentExecutions,
    loadViewerConfig,
  } = runList

  const agentOS = useAgentOS()
  const {
    agentOSData, setAgentOSData,
    agentOSLoading, setAgentOSLoading,
    agentOSFeedback, setAgentOSFeedback,
    selectedRecoveryCheckpointId, setSelectedRecoveryCheckpointId,
    selectedRecoverySnapshotId, setSelectedRecoverySnapshotId,
    selectedRecoveryApplyTraceId, setSelectedRecoveryApplyTraceId,
    loadAgentOS, refreshAgentOS,
  } = agentOS

  const autoLoop = useAutoLoop(setModalConfig)
  const {
    autoLoopStatus,
    autoLoopLoading,
    autoLoopMutating,
    loopStopToast, setLoopStopToast,
    loadAutoLoopStatus,
    startAutoLoop,
    requestAutoLoopStop,
    cancelAutoLoopStop,
  } = autoLoop

  // ── Derived values ────────────────────────────────────────────────────────
  const currentActiveDetail = targetDetail ?? detail
  const activeDetailPhase = currentActiveDetail?.phase ?? null
  const specialistPhaseOverride =
    currentActiveDetail?.phase === 'IMPROVE_NEEDED' && currentActiveDetail?.judge_recommendation?.suggested_return_phase
      ? currentActiveDetail.judge_recommendation.suggested_return_phase
      : null
  const activeTargetName = targetDetail?.name ?? detail?.name ?? ''
  const activeDetail = targetDetail ?? detail
  const activeJudgeRecommendation = activeDetail?.judge_recommendation ?? null

  // ── Artifact fetch ────────────────────────────────────────────────────────
  const fetchArtifact = useCallback(async (filename: string) => {
    if (!targetRun || !selectedTaxonomy) return
    setSelectedArtifact(filename)
    const resp = await fetch(`${API_BASE}/runs/${selectedTaxonomy}/${encodeURIComponent(targetRun)}/artifacts/${filename}`)
    const data = await resp.json()
    setArtifactContent(data.content ?? '')
  }, [selectedTaxonomy, targetRun])

  // ── Specialist hook ───────────────────────────────────────────────────────
  const refreshRunContexts = useCallback(async (taxonomy: string, runName: string) => {
    const refreshes: Promise<void>[] = []
    if (detail && selectedTaxonomy === taxonomy) {
      refreshes.push(
        apiLoadRunDetail(taxonomy, detail.name).then((refreshedDetail) => {
          setDetail(refreshedDetail)
          if ((targetRun ?? detail.name) === detail.name) {
            setTargetDetail(refreshedDetail)
          }
        }),
      )
    }
    refreshes.push(
      Promise.all([apiLoadRunDetail(taxonomy, runName), apiLoadHistory(taxonomy, runName)]).then(([refreshedRun, refreshedHistory]) => {
        if (selectedTaxonomy === taxonomy && targetRun === runName) {
          setTargetDetail(refreshedRun)
          setHistory(refreshedHistory)
          setHistoryRun(runName)
        }
      }),
    )
    await Promise.all(refreshes)
  }, [detail, selectedTaxonomy, targetRun])

  const specialists = useSpecialists({
    selectedTaxonomy,
    targetRun,
    specialistPhaseOverride,
    selectedArtifact,
    fetchArtifact,
    refreshAgentOS,
    refreshRunContexts,
    setAgentOSFeedback,
    setSpecialistModalOpen,
    setCreateSpecialistModalOpen,
  })
  const {
    specialistCandidates,
    specialistModalSelectedCode, setSpecialistModalSelectedCode,
    createdSpecialistResult, setCreatedSpecialistResult,
    loadSpecialistCandidates,
    handleConfirmSpecialist,
    handleCreatedSpecialist,
    openSpecialistSelectionModal,
    openSpecialistSelectionForPhase,
  } = specialists

  // ── Judge chat hook ───────────────────────────────────────────────────────
  const judgeChat = useJudgeChat({
    selectedTaxonomy,
    activeTargetName,
    activeDetailPhase,
    activeJudgeRecommendation,
  })
  const {
    judgeChatMessages, setJudgeChatMessages,
    judgeChatInput, setJudgeChatInput,
    judgeChatLoading,
    sendJudgeChatMessage,
    openJudgeChat: openJudgeChatFn,
  } = judgeChat

  const openJudgeChat = () => openJudgeChatFn(setJudgeChatOpen)

  // ── Rally conversation hook ───────────────────────────────────────────────
  const rally = useRallyConversation({ selectedTaxonomy, targetRun, detail, targetDetail })
  const {
    rallyMessages,
    rallyLoading,
    rallySpecialistCodes,
    openRallyConversation: openRallyConversationFn,
  } = rally

  const openRallyConversation = useCallback(async () => {
    await openRallyConversationFn(setRallyModalOpen)
  }, [openRallyConversationFn, setRallyModalOpen])

  // ── Execution helpers ─────────────────────────────────────────────────────
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

  // ── Viewer config update ──────────────────────────────────────────────────
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
        const parentPromise = apiLoadRunDetail(selectedTaxonomy, selectedRun)
        const historyTarget = targetRun ?? selectedRun
        const historyPromise = apiLoadHistory(selectedTaxonomy, historyTarget)
        const targetPromise = targetRun ? apiLoadRunDetail(selectedTaxonomy, targetRun) : parentPromise
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

  // ── AgentOS workspace ─────────────────────────────────────────────────────
  const openAgentOSWorkspace = (taxonomy?: string | null, runName?: string | null) => {
    setWorkspaceTab('agent-os')
    if (taxonomy && runName) {
      void refreshAgentOS(taxonomy, runName)
      void loadSpecialistCandidates(taxonomy, runName, specialistPhaseOverride)
    }
  }

  const openAutoLoopLaunchModal = () => setAutoLoopLaunchModalOpen(true)

  // ── Run detail fetching ───────────────────────────────────────────────────
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
      apiLoadRunDetail(taxonomy, runName),
      apiLoadHistory(taxonomy, runName),
    ])
    if (detailRequestIdRef.current !== requestId) return
    setDetail(data)
    setTargetDetail(data)
    setHistory(historyData)
    setHistoryRun(runName)
  }

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
        apiLoadRunDetail(taxonomy, runName),
        apiLoadHistory(taxonomy, runName),
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

  // ── Action handlers ───────────────────────────────────────────────────────
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
    const activeTargetNameLocal = targetDetail?.name ?? targetRun ?? null
    const matrixTargetsDifferentRun = activeTargetNameLocal !== null && activeTargetNameLocal !== row.name
    const matrixContextWarning = matrixTargetsDifferentRun
      ? `Execution Matrix always targets the top-level run on the card.\n\nCurrent target: ${activeTargetNameLocal}\nMatrix target: ${row.name}\n\nUse Run Detail actions if you intend to operate on the current child run.`
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
                apiLoadRunDetail(row.taxonomy, row.name).then((refreshedDetail) => {
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
                  apiLoadRunDetail(row.taxonomy, row.name),
                  apiLoadHistory(row.taxonomy, row.name),
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
        setAgentOSFeedback({ kind: 'blocked', title: 'Action Blocked', detail: 'Apply checkpoint is blocked: select a checkpoint candidate first.', actionId })
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
          await runAgentOSAction(taxonomy, runName, { action_id: 'apply-checkpoint', checkpoint_id: selectedRecoveryCheckpointId, reason: inputValue?.trim() ?? '', confirmed: true })
        },
      })
      return
    }
    if (actionId === 'apply-snapshot') {
      if (!selectedRecoverySnapshotId) {
        setAgentOSFeedback({ kind: 'blocked', title: 'Action Blocked', detail: 'Apply snapshot is blocked: select a snapshot candidate first.', actionId })
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
          await runAgentOSAction(taxonomy, runName, { action_id: 'apply-snapshot', snapshot_id: selectedRecoverySnapshotId, reason: inputValue?.trim() ?? '', confirmed: true })
        },
      })
      return
    }
    void runAgentOSAction(taxonomy, runName, { action_id: actionId })
  }

  const invokeCodexPreset = async (presetId: CodexBridgeResult['preset_id'], taxonomy: string, runName: string) => {
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
      <OperatorActionCard
        key={action.id}
        action={action}
        mode={mode}
        taxonomy={taxonomy}
        runName={runName}
        comment={comment}
        isSaved={isSaved}
        canExecute={canExecute}
        isRunning={isRunning}
        runBusy={runBusy}
        runningState={runningState}
        executionNow={executionNow}
        savingActionId={savingActionId}
        rerunComments={rerunComments}
        savedCommentByAction={savedCommentByAction}
        setRerunComments={setRerunComments}
        setSavedCommentByAction={setSavedCommentByAction}
        saveRerunComment={saveRerunComment}
        executeAction={executeAction}
      />
    )
  }

  // ── Computed values ───────────────────────────────────────────────────────
  const filteredRuns = runs.filter((run) => {
    const matchesSearch = run.name.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesHumanBlocker = humanBlockerFilter === 'all' || Boolean(run.human_blocker_active)
    return matchesSearch && matchesHumanBlocker
  })
  const detailActions = targetDetail?.operator_actions ?? []
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
    const grouped = new Map<string, typeof runs[number][]>()
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
        { name: detail.name, label: 'Parent', displayName: detail.name, phase: detail.phase, nextRole: detail.next_role, hasChildren: childRuns.length > 0, isParent: true, isSelected: targetRun === detail.name },
        ...childRuns.map((child) => ({ name: child.name, label: 'Child', displayName: child.child_name, phase: child.phase, nextRole: child.next_role, hasChildren: child.has_children, isParent: false, isSelected: targetRun === child.name })),
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
        ? recentExecutions.find((job) => job.taxonomy === selectedTaxonomy && job.run_name === targetRun) ?? null
        : null
  const agentOSActionIds = new Set(['capture-snapshot', 'capture-checkpoint', 'apply-snapshot', 'apply-checkpoint'])
  const recentAgentOSExecutions =
    selectedTaxonomy && targetRun
      ? recentExecutions.filter((job) =>
          job.taxonomy === selectedTaxonomy && job.run_name === targetRun && agentOSActionIds.has(job.action_id),
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

  // ── Effects ───────────────────────────────────────────────────────────────
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

  useEffect(() => {
    if (!selectedTaxonomy || !targetRun || !autoLoopStatus?.running) return
    const timer = window.setInterval(() => {
      void loadAutoLoopStatus(selectedTaxonomy, targetRun)
    }, 5000)
    return () => window.clearInterval(timer)
  }, [autoLoopStatus?.running, loadAutoLoopStatus, selectedTaxonomy, targetRun])

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

  useEffect(() => {
    if (!selectedRun || !selectedTaxonomy) return
    const detailTimer = setInterval(async () => {
      const requestId = ++refreshRequestIdRef.current
      const parentPromise = apiLoadRunDetail(selectedTaxonomy, selectedRun)
      const histTarget = targetRun ?? selectedRun
      const historyPromise = apiLoadHistory(selectedTaxonomy, histTarget)
      const targetPromise = targetRun ? apiLoadRunDetail(selectedTaxonomy, targetRun) : parentPromise
      const agentPromise = loadAgentOS(selectedTaxonomy, histTarget).catch(() => null)
      const [parentDetail, historyData, targetDetailData, agentData] = await Promise.all([
        parentPromise, historyPromise, targetPromise, agentPromise,
      ])
      if (refreshRequestIdRef.current !== requestId) return
      setDetail(parentDetail)
      setTargetDetail(targetDetailData)
      setHistory(historyData)
      setHistoryRun(histTarget)
      if (agentData) setAgentOSData(agentData)
    }, viewerConfig?.run_detail_refresh_ms ?? SELECTED_RUN_REFRESH_MS)
    return () => clearInterval(detailTimer)
  }, [loadAgentOS, selectedRun, selectedTaxonomy, targetRun, viewerConfig?.run_detail_refresh_ms])

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
    if (!DEFAULT_PREVIEW_PHASES.has(targetDetail.phase)) return
    const preferred = [TRANSCRIPT_ARTIFACT, RESULT_ARTIFACT].find((name) =>
      (targetDetail.artifacts ?? []).some((artifact) => artifact.name === name && artifact.exists),
    )
    if (!preferred) return
    void fetchArtifact(preferred)
  }, [fetchArtifact, targetDetail, selectedArtifact, selectedTaxonomy, targetRun])

  // ── JSX ───────────────────────────────────────────────────────────────────
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
              <WorkspaceHeader
                detail={detail}
                targetDetail={targetDetail}
                sidebarOpen={sidebarOpen}
                setSidebarOpen={setSidebarOpen}
                workspaceTab={workspaceTab}
                setWorkspaceTab={setWorkspaceTab}
                runLineage={runLineage}
                currentViewOpen={currentViewOpen}
                setCurrentViewOpen={setCurrentViewOpen}
                selectedTaxonomy={selectedTaxonomy}
                targetRun={targetRun}
                openAgentOSWorkspace={openAgentOSWorkspace}
                openArtifactReferenceModal={openArtifactReferenceModal}
                fetchTargetDetail={fetchTargetDetail}
              />

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
        <JudgeChatModal
          activeTargetName={activeTargetName}
          judgeChatMessages={judgeChatMessages}
          judgeChatInput={judgeChatInput}
          judgeChatLoading={judgeChatLoading}
          suggestedJudgeAction={suggestedJudgeAction}
          setJudgeChatOpen={setJudgeChatOpen}
          setJudgeChatInput={setJudgeChatInput}
          setRerunComments={setRerunComments}
          sendJudgeChatMessage={sendJudgeChatMessage}
        />
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

      {loopStopToast && (
        <div className="fixed bottom-5 right-5 z-[200] w-80 animate-in fade-in slide-in-from-bottom-3">
          <div className={`rounded-xl border shadow-2xl shadow-black/60 px-4 py-3 ${
            loopStopToast.lastExit !== null && loopStopToast.lastExit !== 0
              ? 'border-red-500/40 bg-red-950/90'
              : 'border-zinc-700 bg-zinc-900/95'
          }`}>
            <div className="flex items-start justify-between gap-3">
              <div className="min-w-0 flex-1">
                <div className={`text-[11px] font-bold uppercase tracking-wide ${loopStopToast.lastExit !== null && loopStopToast.lastExit !== 0 ? 'text-red-300' : 'text-zinc-300'}`}>
                  {loopStopToast.lastExit !== null && loopStopToast.lastExit !== 0 ? '⚠ Auto-Loop Stopped (Error)' : '■ Auto-Loop Stopped'}
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
