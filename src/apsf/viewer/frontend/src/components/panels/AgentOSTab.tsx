import type {
  RunDetail,
  RunHistory,
  OperatorAction,
  ExecutionResult,
  ActionExecutionRecord,
  AgentOSInfo,
  AgentOSActionFeedback,
  AutoLoopStatus,
  SpecialistCandidatesData,
} from '../../types'
import {
  buildExecutionLogText,
  hasExecutionLogContent,
  formatElapsedMs,
} from '../../utils/formatting'
import { PhaseBadge, CopyButton } from '../badges'
import { PhaseContextCard } from '../agentOS/PhaseContextCard'
import { AssignmentCard } from '../agentOS/AssignmentCard'
import { LastActionCard } from '../agentOS/LastActionCard'
import { DetailedAssignmentCard } from '../agentOS/DetailedAssignmentCard'
import { AgentOSStateSection } from '../agentOS/AgentOSStateSection'
import { RecoverySection } from '../agentOS/RecoverySection'
import { OperatorActionsSection } from '../agentOS/OperatorActionsSection'

const AGENT_OS_ACTION_IDS = new Set(['capture-snapshot', 'capture-checkpoint', 'apply-snapshot', 'apply-checkpoint'])

interface AgentOSTabProps {
  agentOSLoading: boolean
  agentOSData: AgentOSInfo | null
  executionResult: ExecutionResult | null
  detail: RunDetail
  targetDetail: RunDetail | null
  selectedTaxonomy: string | null
  targetRun: string | null
  activeJudgeRecommendation: RunDetail['judge_recommendation']
  activeDetail: RunDetail | null
  history: RunHistory | null
  recentExecutions: ActionExecutionRecord[]
  searchTerm: string
  executionNow: number
  executingStateForRun: (taxonomy: string, runName: string) => { actionId: string; startedAt: number } | null
  selectedRecoveryCheckpointId: string | null
  setSelectedRecoveryCheckpointId: (id: string | null) => void
  selectedRecoverySnapshotId: string | null
  setSelectedRecoverySnapshotId: (id: string | null) => void
  selectedRecoveryApplyTraceId: string | null
  setSelectedRecoveryApplyTraceId: (id: string | null) => void
  agentOSFeedback: AgentOSActionFeedback | null
  autoLoopStatus: AutoLoopStatus | null
  autoLoopLoading: boolean
  autoLoopMutating: 'start' | 'stop' | 'cancel' | null
  judgeChatMessages: Array<{ role: 'user' | 'assistant'; content: string }>
  phaseContextActions: OperatorAction[]
  selectedPhaseContextAction: OperatorAction | null
  primaryExecutableAction: OperatorAction | null
  setPhaseContextActionId: (id: string) => void
  rerunComments: Record<string, string>
  setRerunComments: React.Dispatch<React.SetStateAction<Record<string, string>>>
  savedCommentByAction: Record<string, string>
  setSavedCommentByAction: React.Dispatch<React.SetStateAction<Record<string, string>>>
  savingActionId: string | null
  specialistCandidates: SpecialistCandidatesData | null
  setViewerConfigModalOpen: (value: boolean) => void
  openJudgeChat: () => void
  setJudgeChatMessages: React.Dispatch<React.SetStateAction<Array<{ role: 'user' | 'assistant'; content: string }>>>
  setJudgeChatOpen: (value: boolean) => void
  openAutoLoopLaunchModal: () => void
  openRallyConversation: () => Promise<void>
  requestAutoLoopStop: (taxonomy: string, runName: string) => Promise<void>
  cancelAutoLoopStop: (taxonomy: string, runName: string) => Promise<void>
  openSpecialistSelectionForPhase: (phase: string) => Promise<void>
  openSpecialistSelectionModal: (initialCode?: string) => Promise<void>
  saveRerunComment: (action: OperatorAction, taxonomy: string, runName: string) => Promise<void>
  executeAction: (action: OperatorAction, taxonomy: string, runName: string) => Promise<void>
  executeAgentOSAction: (
    actionId: 'act' | 'capture-snapshot' | 'capture-checkpoint' | 'apply-snapshot' | 'apply-checkpoint',
    taxonomy: string,
    runName: string,
  ) => void
  executingActionForRun: (taxonomy: string, runName: string) => string | null
  isRunExecuting: (taxonomy: string, runName: string) => boolean
  openArtifactReferenceModal: (preferredArtifact?: string) => void
  activeTargetName: string
}

export function AgentOSTab({
  agentOSLoading,
  agentOSData,
  executionResult,
  detail,
  targetDetail,
  selectedTaxonomy,
  targetRun,
  activeJudgeRecommendation,
  activeDetail,
  history,
  recentExecutions,
  searchTerm,
  executionNow,
  executingStateForRun,
  selectedRecoveryCheckpointId,
  setSelectedRecoveryCheckpointId,
  selectedRecoverySnapshotId,
  setSelectedRecoverySnapshotId,
  selectedRecoveryApplyTraceId,
  setSelectedRecoveryApplyTraceId,
  agentOSFeedback,
  autoLoopStatus,
  autoLoopLoading,
  autoLoopMutating,
  judgeChatMessages,
  phaseContextActions,
  selectedPhaseContextAction,
  primaryExecutableAction,
  setPhaseContextActionId,
  rerunComments,
  setRerunComments,
  savedCommentByAction,
  setSavedCommentByAction,
  savingActionId,
  specialistCandidates,
  setViewerConfigModalOpen,
  openJudgeChat,
  setJudgeChatMessages,
  setJudgeChatOpen,
  openAutoLoopLaunchModal,
  openRallyConversation,
  requestAutoLoopStop,
  cancelAutoLoopStop,
  openSpecialistSelectionForPhase,
  openSpecialistSelectionModal,
  saveRerunComment,
  executeAction,
  executeAgentOSAction,
  executingActionForRun,
  openArtifactReferenceModal,
  activeTargetName,
}: AgentOSTabProps) {
  const activeAssignment = activeDetail?.assignment_summary ?? null
  const activeSpecialist = activeDetail?.specialist_visibility ?? null
  const activePhase = activeDetail?.phase ?? ''
  const activePriority = activeDetail?.priority ?? 'Unranked'
  const activeNextRole = activeDetail?.next_role ?? ''
  const activeOperatorCommand = activeDetail?.operator_command ?? ''
  const activeDecisionReason = activeDetail?.decision_reason ?? ''
  const activeRunExecutionState = selectedTaxonomy && activeTargetName ? executingStateForRun(selectedTaxonomy, activeTargetName) : null
  const activeRunExecutionId = activeRunExecutionState?.actionId ?? null
  const isActiveRunBusy = activeRunExecutionId !== null
  const activeExecutionElapsed = activeRunExecutionState ? formatElapsedMs(executionNow - activeRunExecutionState.startedAt) : null
  const activePhaseStatus = agentOSData?.run_state?.phase_status ?? ''
  const ownerWorkingNow = activePhaseStatus === 'in_progress'
  const ownerStatusLabel = ownerWorkingNow ? '実行中' : activePhaseStatus === 'pending' ? '待機中' : activePhaseStatus || 'Pending'
  const activeOwner = agentOSData?.run_state?.current_owner ?? activeNextRole
  const phaseEnteredAtMs = agentOSData?.run_state?.phase_entered_at ? Date.parse(agentOSData.run_state.phase_entered_at) : NaN
  const activePhaseElapsed = Number.isFinite(phaseEnteredAtMs) ? formatElapsedMs(Math.max(0, executionNow - phaseEnteredAtMs)) : null
  const recentAgentOSExecutions = selectedTaxonomy && targetRun
    ? recentExecutions.filter((j) => j.taxonomy === selectedTaxonomy && j.run_name === targetRun && AGENT_OS_ACTION_IDS.has(j.action_id)).slice(0, 5)
    : []
  const latestRunExecution = history?.latest_execution ?? (selectedTaxonomy && targetRun ? recentExecutions.find((j) => j.taxonomy === selectedTaxonomy && j.run_name === targetRun) ?? null : null)
  const showDetailedAssignmentCard = searchTerm.trim() === '__show_assignment_details__'
  return (
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
            <PhaseContextCard
              activePhase={activePhase}
              activePriority={activePriority}
              activeNextRole={activeNextRole}
              activeDecisionReason={activeDecisionReason}
              activeOperatorCommand={activeOperatorCommand}
              agentOSData={agentOSData}
              activeDetail={activeDetail}
              detail={detail}
              activeJudgeRecommendation={activeJudgeRecommendation}
              activeRunExecutionId={activeRunExecutionId}
              isActiveRunBusy={isActiveRunBusy}
              activeExecutionElapsed={activeExecutionElapsed}
              activePhaseElapsed={activePhaseElapsed}
              activeRunExecutionState={activeRunExecutionState}
              ownerWorkingNow={ownerWorkingNow}
              ownerStatusLabel={ownerStatusLabel}
              activeOwner={activeOwner}
              autoLoopLoading={autoLoopLoading}
              autoLoopStatus={autoLoopStatus}
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
              selectedTaxonomy={selectedTaxonomy}
              activeTargetName={activeTargetName}
              setViewerConfigModalOpen={setViewerConfigModalOpen}
              openJudgeChat={openJudgeChat}
              setJudgeChatMessages={setJudgeChatMessages}
              setJudgeChatOpen={setJudgeChatOpen}
              openAutoLoopLaunchModal={openAutoLoopLaunchModal}
              openRallyConversation={openRallyConversation}
              requestAutoLoopStop={requestAutoLoopStop}
              cancelAutoLoopStop={cancelAutoLoopStop}
              saveRerunComment={saveRerunComment}
              executeAction={executeAction}
            />
            <AssignmentCard
              activeAssignment={activeAssignment}
              activeSpecialist={activeSpecialist}
              selectedTaxonomy={selectedTaxonomy}
              targetRun={targetRun}
              detail={detail}
              isActiveRunBusy={isActiveRunBusy}
              openSpecialistSelectionForPhase={openSpecialistSelectionForPhase}
            />
            <LastActionCard latestRunExecution={latestRunExecution} />
          </div>

          {showDetailedAssignmentCard && (
            <DetailedAssignmentCard
              targetDetail={targetDetail}
              detail={detail}
              specialistCandidates={specialistCandidates}
              selectedTaxonomy={selectedTaxonomy}
              targetRun={targetRun}
              openSpecialistSelectionModal={openSpecialistSelectionModal}
            />
          )}

          <AgentOSStateSection
            agentOSData={agentOSData}
            openArtifactReferenceModal={openArtifactReferenceModal}
          />

          <RecoverySection
            agentOSData={agentOSData}
            selectedRecoveryCheckpointId={selectedRecoveryCheckpointId}
            setSelectedRecoveryCheckpointId={setSelectedRecoveryCheckpointId}
            selectedRecoverySnapshotId={selectedRecoverySnapshotId}
            setSelectedRecoverySnapshotId={setSelectedRecoverySnapshotId}
            selectedRecoveryApplyTraceId={selectedRecoveryApplyTraceId}
            setSelectedRecoveryApplyTraceId={setSelectedRecoveryApplyTraceId}
          />

          {selectedTaxonomy && targetRun && (
            <OperatorActionsSection
              selectedTaxonomy={selectedTaxonomy}
              targetRun={targetRun}
              agentOSFeedback={agentOSFeedback}
              selectedRecoveryCheckpointId={selectedRecoveryCheckpointId}
              selectedRecoverySnapshotId={selectedRecoverySnapshotId}
              latestRunExecution={latestRunExecution}
              recentAgentOSExecutions={recentAgentOSExecutions}
              executingActionForRun={executingActionForRun}
              executeAgentOSAction={executeAgentOSAction}
            />
          )}
        </>
      )}
    </div>
  )
}
