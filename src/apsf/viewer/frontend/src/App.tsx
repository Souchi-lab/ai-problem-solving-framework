import { useEffect, useRef, useState } from 'react'
import { ChevronRight } from 'lucide-react'
import { loadStoredStringArray } from './utils/formatting'
import { WorkspaceHeader } from './components/WorkspaceHeader'
import { SidebarPanel } from './components/panels/SidebarPanel'
import { DetailTab } from './components/panels/DetailTab'
import { ManagementTab } from './components/panels/ManagementTab'
import { AgentOSTab } from './components/panels/AgentOSTab'
import { ActivityTab } from './components/panels/ActivityTab'
import { AppModals } from './components/AppModals'
import { useModalState } from './hooks/useModalState'
import { useAutoLoop } from './hooks/useAutoLoop'
import { useJudgeChat } from './hooks/useJudgeChat'
import { useRallyConversation } from './hooks/useRallyConversation'
import { useRunList } from './hooks/useRunList'
import { useSpecialists } from './hooks/useSpecialists'
import { useAgentOS } from './hooks/useAgentOS'
import { useRunDetail, DEFAULT_PREVIEW_PHASES, TRANSCRIPT_ARTIFACT, RESULT_ARTIFACT } from './hooks/useRunDetail'
import { useExecution } from './hooks/useExecution'
import { usePeriodicRefresh } from './hooks/usePeriodicRefresh'
import { useActionContext } from './hooks/useActionContext.tsx'

const RUN_LIST_REFRESH_MS = 30000
const TAXONOMY_PIN_STORAGE_KEY = 'apsf.viewer.sidebar.pinnedTaxonomies'
const TAXONOMY_OPEN_STORAGE_KEY = 'apsf.viewer.sidebar.openTaxonomies'

export default function App() {
  const [workspaceTab, setWorkspaceTab] = useState<'detail' | 'management' | 'activity' | 'agent-os'>('agent-os')
  const [operatorFilter, setOperatorFilter] = useState<'active' | 'recent' | 'all'>('active')
  const [humanBlockerFilter, setHumanBlockerFilter] = useState<'all' | 'blocked'>('all')
  const [pinnedTaxonomies, setPinnedTaxonomies] = useState<string[]>(() => loadStoredStringArray(TAXONOMY_PIN_STORAGE_KEY, ['work']))
  const [openTaxonomies, setOpenTaxonomies] = useState<string[]>(() => loadStoredStringArray(TAXONOMY_OPEN_STORAGE_KEY, ['work', 'fw-improvement', 'sochi-blocks']))
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [currentViewOpen, setCurrentViewOpen] = useState(false)
  const [searchTerm, setSearchTerm] = useState('')
  const [jobsSearchTerm, setJobsSearchTerm] = useState('')
  const [phaseContextActionId, setPhaseContextActionId] = useState<string>('')
  const [selectedExecutionLog, setSelectedExecutionLog] = useState<import('./types').ActionExecutionRecord | null>(null)
  const [rerunComments, setRerunComments] = useState<Record<string, string>>({})
  const [savedCommentByAction, setSavedCommentByAction] = useState<Record<string, string>>({})

  const {
    modalConfig, setModalConfig,
    viewerConfigModalOpen, setViewerConfigModalOpen,
    artifactModalOpen, setArtifactModalOpen,
    specialistModalOpen, setSpecialistModalOpen,
    createSpecialistModalOpen, setCreateSpecialistModalOpen,
    autoLoopLaunchModalOpen, setAutoLoopLaunchModalOpen,
    rallyModalOpen, setRallyModalOpen,
    judgeChatOpen, setJudgeChatOpen,
  } = useModalState()

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
  } = useRunList()

  const {
    agentOSData, setAgentOSData,
    agentOSLoading, setAgentOSLoading,
    agentOSFeedback, setAgentOSFeedback,
    selectedRecoveryCheckpointId, setSelectedRecoveryCheckpointId,
    selectedRecoverySnapshotId, setSelectedRecoverySnapshotId,
    selectedRecoveryApplyTraceId, setSelectedRecoveryApplyTraceId,
    loadAgentOS, refreshAgentOS,
  } = useAgentOS()

  const {
    autoLoopStatus, autoLoopLoading, autoLoopMutating,
    loopStopToast, setLoopStopToast,
    loadAutoLoopStatus, startAutoLoop, requestAutoLoopStop, cancelAutoLoopStop,
  } = useAutoLoop(setModalConfig)

  const loadSpecialistCandidatesRef = useRef<(taxonomy: string, runName: string, phaseOverride?: string | null) => Promise<unknown>>(async () => {})
  const {
    detail, setDetail,
    selectedRun,
    selectedTaxonomy,
    targetRun,
    targetDetail, setTargetDetail,
    history, setHistory,
    historyRun, setHistoryRun,
    selectedArtifact,
    artifactContent,
    codexResult,
    codexError,
    codexLoadingPreset,
    codexTargetKey,
    specialistPhaseOverride,
    refreshRequestIdRef,
    fetchArtifact,
    refreshRunContexts,
    fetchDetail,
    fetchTargetDetail: fetchTargetDetailBase,
    openArtifactReferenceModal,
    invokeCodexPreset,
    updateViewerConfig: updateViewerConfigBase,
  } = useRunDetail({
    setAgentOSLoading,
    setAgentOSData,
    loadAgentOS,
    loadSpecialistCandidates: (t, r, p) => loadSpecialistCandidatesRef.current(t, r, p).then(() => {}),
    setArtifactModalOpen,
    setModalConfig,
    loadOperatorMatrix,
    loadRecentExecutions,
    setMatrixRows,
    setRecentExecutions,
  })

  const fetchTargetDetailWrapped = (t: string, r: string) =>
    fetchTargetDetailBase(t, r).then((d) => { if (d) setAgentOSData(d) })
  const updateViewerConfig = (patch: Parameters<typeof updateViewerConfigBase>[0]) =>
    updateViewerConfigBase(patch, setViewerConfig, setViewerConfigSavingKey)


  const {
    specialistCandidates,
    specialistModalSelectedCode, setSpecialistModalSelectedCode,
    createdSpecialistResult, setCreatedSpecialistResult,
    loadSpecialistCandidates,
    handleConfirmSpecialist,
    handleCreatedSpecialist,
    openSpecialistSelectionModal,
    openSpecialistSelectionForPhase,
  } = useSpecialists({
    selectedTaxonomy, targetRun, specialistPhaseOverride, selectedArtifact,
    fetchArtifact, refreshAgentOS, refreshRunContexts, setAgentOSFeedback,
    setSpecialistModalOpen, setCreateSpecialistModalOpen,
  })
  loadSpecialistCandidatesRef.current = loadSpecialistCandidates

  const activeDetail = targetDetail ?? detail
  const activeDetailPhase = activeDetail?.phase ?? null
  const activeJudgeRecommendation = activeDetail?.judge_recommendation ?? null
  const activeTargetName = targetDetail?.name ?? detail?.name ?? ''

  const {
    executionResult, saveCommentResult, savingActionId,
    executionNow,
    isRunExecuting, executingStateForRun, executingActionForRun,
    saveRerunComment, executeAction, executeMatrixAction, executeAgentOSAction,
  } = useExecution({
    selectedTaxonomy, selectedRun, targetRun,
    rerunComments, savedCommentByAction, selectedArtifact,
    selectedRecoveryCheckpointId, selectedRecoverySnapshotId,
    setModalConfig, setMatrixRows, setRecentExecutions,
    setDetail, setTargetDetail, setHistory, setHistoryRun,
    setAgentOSFeedback, setSavedCommentByAction,
    fetchRuns, fetchDetail, fetchArtifact, refreshRunContexts, refreshAgentOS,
  })

  const {
    judgeChatMessages, setJudgeChatMessages,
    judgeChatInput, setJudgeChatInput,
    judgeChatLoading, sendJudgeChatMessage,
    openJudgeChat: openJudgeChatFn,
  } = useJudgeChat({ selectedTaxonomy, activeTargetName, activeDetailPhase, activeJudgeRecommendation })

  const {
    recommendedActionId,
    primaryExecutableAction,
    phaseContextActions,
    suggestedJudgeAction,
    renderOperatorAction,
  } = useActionContext({
    targetDetail,
    activeJudgeRecommendation,
    activeDetailPhase,
    executionNow,
    savingActionId,
    rerunComments,
    savedCommentByAction,
    setRerunComments,
    setSavedCommentByAction,
    executingActionForRun,
    executingStateForRun,
    saveRerunComment,
    executeAction,
  })

  const { rallyMessages, rallyLoading, rallySpecialistCodes, openRallyConversation: openRallyConversationFn } =
    useRallyConversation({ selectedTaxonomy, targetRun, detail, targetDetail })

  const selectedPhaseContextAction = phaseContextActions.find((a) => a.id === phaseContextActionId) ?? primaryExecutableAction ?? phaseContextActions[0] ?? null

  const openAgentOSWorkspace = (taxonomy?: string | null, runName?: string | null) => {
    setWorkspaceTab('agent-os')
    if (taxonomy && runName) { void refreshAgentOS(taxonomy, runName); void loadSpecialistCandidates(taxonomy, runName, specialistPhaseOverride) }
  }



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
    window.localStorage.setItem(TAXONOMY_PIN_STORAGE_KEY, JSON.stringify(pinnedTaxonomies))
    window.localStorage.setItem(TAXONOMY_OPEN_STORAGE_KEY, JSON.stringify(openTaxonomies))
  }, [pinnedTaxonomies, openTaxonomies])

  usePeriodicRefresh({
    selectedRun,
    selectedTaxonomy,
    targetRun,
    refreshRequestIdRef,
    viewerConfigRefreshMs: viewerConfig?.run_detail_refresh_ms,
    loadAgentOS,
    setDetail,
    setTargetDetail,
    setHistory,
    setHistoryRun,
    setAgentOSData,
  })

  useEffect(() => {
    if (phaseContextActions.length === 0) { setPhaseContextActionId(''); return }
    setPhaseContextActionId((current) =>
      current && phaseContextActions.some((a) => a.id === current)
        ? current
        : (primaryExecutableAction?.id ?? phaseContextActions[0].id),
    )
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
          runs={runs}
          pinnedTaxonomies={pinnedTaxonomies}
          openTaxonomies={openTaxonomies}
          setPinnedTaxonomies={setPinnedTaxonomies}
          setOpenTaxonomies={setOpenTaxonomies}
          selectedRun={selectedRun}
          fetchRuns={fetchRuns}
          setIsLoadingRuns={setIsLoadingRuns}
          fetchDetail={fetchDetail}
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
                currentViewOpen={currentViewOpen}
                setCurrentViewOpen={setCurrentViewOpen}
                selectedTaxonomy={selectedTaxonomy}
                targetRun={targetRun}
                openAgentOSWorkspace={openAgentOSWorkspace}
                openArtifactReferenceModal={openArtifactReferenceModal}
                fetchTargetDetail={fetchTargetDetailWrapped}
              />

              {workspaceTab === 'detail' ? (
                <DetailTab
                  detail={detail}
                  targetDetail={targetDetail}
                  history={history}
                  historyRun={historyRun}
                  activeTargetName={activeTargetName}
                  activeDetailPhase={activeDetailPhase}
                  recommendedActionId={recommendedActionId}
                  selectedTaxonomy={selectedTaxonomy}
                  renderOperatorAction={renderOperatorAction}
                />
              ) : workspaceTab === 'management' ? (
                <ManagementTab
                  operatorFilter={operatorFilter}
                  setOperatorFilter={setOperatorFilter}
                  matrixRows={matrixRows}
                  recentExecutions={recentExecutions}
                  searchTerm={searchTerm}
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
                  activeJudgeRecommendation={activeJudgeRecommendation}
                  activeDetail={activeDetail}
                  history={history}
                  recentExecutions={recentExecutions}
                  searchTerm={searchTerm}
                  executionNow={executionNow}
                  executingStateForRun={executingStateForRun}
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
                  openJudgeChat={() => openJudgeChatFn(setJudgeChatOpen)}
                  setJudgeChatMessages={setJudgeChatMessages}
                  setJudgeChatOpen={setJudgeChatOpen}
                  openAutoLoopLaunchModal={() => setAutoLoopLaunchModalOpen(true)}
                  openRallyConversation={() => openRallyConversationFn(setRallyModalOpen)}
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
                  recentExecutions={recentExecutions}
                  setSelectedExecutionLog={setSelectedExecutionLog}
                  executionResult={executionResult}
                  saveCommentResult={saveCommentResult}
                />
              )}
            </section>
          </>
        )}
      </main>

      <AppModals
        judgeChatOpen={judgeChatOpen}
        setJudgeChatOpen={setJudgeChatOpen}
        activeTargetName={activeTargetName}
        judgeChatMessages={judgeChatMessages}
        judgeChatInput={judgeChatInput}
        judgeChatLoading={judgeChatLoading}
        suggestedJudgeAction={suggestedJudgeAction}
        setJudgeChatInput={setJudgeChatInput}
        setRerunComments={setRerunComments}
        sendJudgeChatMessage={sendJudgeChatMessage}
        modalConfig={modalConfig}
        setModalConfig={setModalConfig}
        viewerConfigModalOpen={viewerConfigModalOpen}
        setViewerConfigModalOpen={setViewerConfigModalOpen}
        viewerConfig={viewerConfig}
        viewerConfigSavingKey={viewerConfigSavingKey}
        updateViewerConfig={updateViewerConfig}
        specialistModalOpen={specialistModalOpen}
        setSpecialistModalOpen={setSpecialistModalOpen}
        specialistCandidates={specialistCandidates}
        selectedTaxonomy={selectedTaxonomy}
        targetRun={targetRun}
        specialistModalSelectedCode={specialistModalSelectedCode ?? ''}
        setSpecialistModalSelectedCode={setSpecialistModalSelectedCode}
        createdSpecialistResult={createdSpecialistResult}
        setCreatedSpecialistResult={setCreatedSpecialistResult}
        setCreateSpecialistModalOpen={setCreateSpecialistModalOpen}
        handleConfirmSpecialist={handleConfirmSpecialist}
        autoLoopLaunchModalOpen={autoLoopLaunchModalOpen}
        setAutoLoopLaunchModalOpen={setAutoLoopLaunchModalOpen}
        activeDetailPhase={activeDetailPhase}
        autoLoopMutating={autoLoopMutating}
        startAutoLoop={startAutoLoop}
        targetDetail={targetDetail}
        openSpecialistSelectionForPhase={openSpecialistSelectionForPhase}
        rallyModalOpen={rallyModalOpen}
        setRallyModalOpen={setRallyModalOpen}
        rallyMessages={rallyMessages}
        rallyLoading={rallyLoading}
        autoLoopStatus={autoLoopStatus}
        agentOSData={agentOSData}
        executionNow={executionNow}
        executingStateForRun={executingStateForRun}
        rallySpecialistCodes={rallySpecialistCodes}
        createSpecialistModalOpen={createSpecialistModalOpen}
        handleCreatedSpecialist={handleCreatedSpecialist}
        artifactModalOpen={artifactModalOpen}
        setArtifactModalOpen={setArtifactModalOpen}
        detail={detail}
        selectedArtifact={selectedArtifact}
        artifactContent={artifactContent}
        fetchArtifact={fetchArtifact}
        selectedExecutionLog={selectedExecutionLog}
        setSelectedExecutionLog={setSelectedExecutionLog}
        loopStopToast={loopStopToast}
        setLoopStopToast={setLoopStopToast}
      />
    </div>
  )
}
