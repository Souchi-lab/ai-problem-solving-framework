import type {
  RunDetail,
  OperatorAction,
  ExecutionResult,
  ActionExecutionRecord,
  AgentOSInfo,
  AgentOSActionFeedback,
  AutoLoopStatus,
  AssignmentSummary,
  SpecialistVisibility,
  SpecialistCandidatesData,
} from '../../types'
import {
  PhaseBadge,
  PriorityBadge,
  AssignmentModeBadge,
  CopyButton,
} from '../badges'
import {
  parseSatisfiabilityReason,
  buildExecutionLogText,
  hasExecutionLogContent,
  formatAgentOSTimestamp,
  prettifyActionId,
  summarizeExecutionIntent,
  summarizeExecutionOutcome,
} from '../../utils/formatting'
import { getArtifactDisplayMeta } from '../../utils/artifacts'

interface AgentOSTabProps {
  agentOSLoading: boolean
  agentOSData: AgentOSInfo | null
  executionResult: ExecutionResult | null
  detail: RunDetail
  targetDetail: RunDetail | null
  selectedTaxonomy: string | null
  targetRun: string | null
  activePhase: string
  activePriority: 'Now' | 'Next' | 'Later' | 'Unranked'
  activeNextRole: string
  activeDecisionReason: string
  activeAssignment: AssignmentSummary | null
  activeSpecialist: SpecialistVisibility | null
  activeJudgeRecommendation: RunDetail['judge_recommendation']
  activeRunExecutionState: { actionId: string; startedAt: number } | null
  activeRunExecutionId: string | null
  activeExecutionElapsed: string | null
  activePhaseElapsed: string | null
  isActiveRunBusy: boolean
  activeOwner: string
  ownerStatusLabel: string
  ownerWorkingNow: boolean
  activeOperatorCommand: string
  activeDetail: RunDetail | null
  latestRunExecution: ActionExecutionRecord | null
  recentAgentOSExecutions: ActionExecutionRecord[]
  failingGateResults: AgentOSInfo['gate_results']
  showDetailedAssignmentCard: boolean
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
  activePhase,
  activePriority,
  activeNextRole,
  activeDecisionReason,
  activeAssignment,
  activeSpecialist,
  activeJudgeRecommendation,
  activeRunExecutionState,
  activeRunExecutionId,
  activeExecutionElapsed,
  activePhaseElapsed,
  isActiveRunBusy,
  activeOwner,
  ownerStatusLabel,
  ownerWorkingNow,
  activeOperatorCommand,
  activeDetail,
  latestRunExecution,
  recentAgentOSExecutions,
  failingGateResults,
  showDetailedAssignmentCard,
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
                    <div className="mt-0.5 text-zinc-300">
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
  )
}
