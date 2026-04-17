import type {
  RunDetail,
  OperatorAction,
  AutoLoopStatus,
  AgentOSInfo,
} from '../../types'
import { PhaseBadge, PriorityBadge, CopyButton } from '../badges'
import { parseSatisfiabilityReason } from '../../utils/formatting'

interface PhaseContextCardProps {
  activePhase: string
  activePriority: import('../../types').RunDetail['priority']
  activeNextRole: string
  activeDecisionReason: string
  activeOperatorCommand: string
  agentOSData: AgentOSInfo
  activeDetail: RunDetail | null
  detail: RunDetail
  activeJudgeRecommendation: RunDetail['judge_recommendation']
  activeRunExecutionId: string | null
  isActiveRunBusy: boolean
  activeExecutionElapsed: string | null
  activePhaseElapsed: string | null
  activeRunExecutionState: { actionId: string; startedAt: number } | null
  ownerWorkingNow: boolean
  ownerStatusLabel: string
  activeOwner: string
  autoLoopLoading: boolean
  autoLoopStatus: AutoLoopStatus | null
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
  selectedTaxonomy: string | null
  activeTargetName: string
  setViewerConfigModalOpen: (value: boolean) => void
  openJudgeChat: () => void
  setJudgeChatMessages: React.Dispatch<React.SetStateAction<Array<{ role: 'user' | 'assistant'; content: string }>>>
  setJudgeChatOpen: (value: boolean) => void
  openAutoLoopLaunchModal: () => void
  openRallyConversation: () => Promise<void>
  requestAutoLoopStop: (taxonomy: string, runName: string) => Promise<void>
  cancelAutoLoopStop: (taxonomy: string, runName: string) => Promise<void>
  saveRerunComment: (action: OperatorAction, taxonomy: string, runName: string) => Promise<void>
  executeAction: (action: OperatorAction, taxonomy: string, runName: string) => Promise<void>
}

export function PhaseContextCard({
  activePhase,
  activePriority,
  activeNextRole,
  activeDecisionReason,
  activeOperatorCommand,
  agentOSData,
  activeDetail,
  detail,
  activeJudgeRecommendation,
  activeRunExecutionId,
  isActiveRunBusy,
  activeExecutionElapsed,
  activePhaseElapsed,
  activeRunExecutionState,
  ownerWorkingNow,
  ownerStatusLabel,
  activeOwner,
  autoLoopLoading,
  autoLoopStatus,
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
  selectedTaxonomy,
  activeTargetName,
  setViewerConfigModalOpen,
  openJudgeChat,
  setJudgeChatMessages,
  setJudgeChatOpen,
  openAutoLoopLaunchModal,
  openRallyConversation,
  requestAutoLoopStop,
  cancelAutoLoopStop,
  saveRerunComment,
  executeAction,
}: PhaseContextCardProps) {
  return (
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
  )
}
