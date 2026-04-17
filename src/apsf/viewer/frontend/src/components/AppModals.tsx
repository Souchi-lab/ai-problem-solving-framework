import type {
  ModalConfig,
  ViewerConfig,
  SpecialistCandidatesData,
  RallyMessage,
  AutoLoopStatus,
  ActionExecutionRecord,
  CreateSpecialistResult,
  AgentOSInfo,
  OperatorAction,
} from '../types'
import { formatElapsedMs } from '../utils/formatting'
import { JudgeChatModal } from './JudgeChatModal'
import {
  ConfirmModal,
  SpecialistSelectionModal,
  AutoLoopLaunchModal,
  RallyConversationModal,
  CreateSpecialistModal,
  ViewerConfigModal,
  ExecutionLogModal,
  ArtifactReferenceModal,
} from './modals'

interface AppModalsProps {
  // JudgeChat
  judgeChatOpen: boolean
  setJudgeChatOpen: (open: boolean) => void
  activeTargetName: string
  judgeChatMessages: Array<{ role: 'user' | 'assistant'; content: string }>
  judgeChatInput: string
  judgeChatLoading: boolean
  suggestedJudgeAction: OperatorAction | null
  setJudgeChatInput: (input: string) => void
  setRerunComments: React.Dispatch<React.SetStateAction<Record<string, string>>>
  sendJudgeChatMessage: () => Promise<void>

  // ConfirmModal
  modalConfig: ModalConfig | null
  setModalConfig: (config: ModalConfig | null) => void

  // ViewerConfigModal
  viewerConfigModalOpen: boolean
  setViewerConfigModalOpen: (open: boolean) => void
  viewerConfig: ViewerConfig | null
  viewerConfigSavingKey: string | null
  updateViewerConfig: (patch: Partial<Pick<ViewerConfig, 'execution_mode' | 'cli_tool_mode' | 'build_max_turns' | 'run_detail_refresh_ms'>>) => Promise<void>

  // SpecialistSelectionModal
  specialistModalOpen: boolean
  setSpecialistModalOpen: (open: boolean) => void
  specialistCandidates: SpecialistCandidatesData | null
  selectedTaxonomy: string | null
  targetRun: string | null
  specialistModalSelectedCode: string
  setSpecialistModalSelectedCode: (code: string) => void
  createdSpecialistResult: CreateSpecialistResult | null
  setCreatedSpecialistResult: (result: CreateSpecialistResult | null) => void
  setCreateSpecialistModalOpen: (open: boolean) => void
  handleConfirmSpecialist: (code: string) => Promise<void>

  // AutoLoopLaunchModal
  autoLoopLaunchModalOpen: boolean
  setAutoLoopLaunchModalOpen: (open: boolean) => void
  activeDetailPhase: string | null
  autoLoopMutating: string | null
  startAutoLoop: (taxonomy: string, runName: string, buildScript?: string) => Promise<void>
  targetDetail: import('../types').RunDetail | null
  openSpecialistSelectionForPhase: (phase: string) => Promise<void>

  // RallyConversationModal
  rallyModalOpen: boolean
  setRallyModalOpen: (open: boolean) => void
  rallyMessages: RallyMessage[]
  rallyLoading: boolean
  autoLoopStatus: AutoLoopStatus | null
  agentOSData: AgentOSInfo | null
  executionNow: number
  executingStateForRun: (taxonomy: string, runName: string) => { actionId: string; startedAt: number } | null
  rallySpecialistCodes: { planner: string; builder: string; critic: string }

  // CreateSpecialistModal
  createSpecialistModalOpen: boolean
  handleCreatedSpecialist: (result: CreateSpecialistResult) => Promise<void>

  // ArtifactReferenceModal
  artifactModalOpen: boolean
  setArtifactModalOpen: (open: boolean) => void
  detail: import('../types').RunDetail | null
  selectedArtifact: string | null
  artifactContent: string
  fetchArtifact: (filename: string) => Promise<void>

  // ExecutionLogModal
  selectedExecutionLog: ActionExecutionRecord | null
  setSelectedExecutionLog: (log: ActionExecutionRecord | null) => void

  // LoopStopToast
  loopStopToast: { stopReason: string | null; lastExit: number | null } | null
  setLoopStopToast: (toast: { stopReason: string | null; lastExit: number | null } | null) => void
}

export function AppModals({
  judgeChatOpen,
  setJudgeChatOpen,
  activeTargetName,
  judgeChatMessages,
  judgeChatInput,
  judgeChatLoading,
  suggestedJudgeAction,
  setJudgeChatInput,
  setRerunComments,
  sendJudgeChatMessage,
  modalConfig,
  setModalConfig,
  viewerConfigModalOpen,
  setViewerConfigModalOpen,
  viewerConfig,
  viewerConfigSavingKey,
  updateViewerConfig,
  specialistModalOpen,
  setSpecialistModalOpen,
  specialistCandidates,
  selectedTaxonomy,
  targetRun,
  specialistModalSelectedCode,
  setSpecialistModalSelectedCode,
  createdSpecialistResult,
  setCreatedSpecialistResult,
  setCreateSpecialistModalOpen,
  handleConfirmSpecialist,
  autoLoopLaunchModalOpen,
  setAutoLoopLaunchModalOpen,
  activeDetailPhase,
  autoLoopMutating,
  startAutoLoop,
  targetDetail,
  openSpecialistSelectionForPhase,
  rallyModalOpen,
  setRallyModalOpen,
  rallyMessages,
  rallyLoading,
  autoLoopStatus,
  agentOSData,
  executionNow,
  executingStateForRun,
  rallySpecialistCodes,
  createSpecialistModalOpen,
  handleCreatedSpecialist,
  artifactModalOpen,
  setArtifactModalOpen,
  detail,
  selectedArtifact,
  artifactContent,
  fetchArtifact,
  selectedExecutionLog,
  setSelectedExecutionLog,
  loopStopToast,
  setLoopStopToast,
}: AppModalsProps) {
  const activeAssignment = (targetDetail ?? detail)?.assignment_summary ?? null
  const activeSpecialist = (targetDetail ?? detail)?.specialist_visibility ?? null
  const activeRunExecutionState = selectedTaxonomy && activeTargetName ? executingStateForRun(selectedTaxonomy, activeTargetName) : null
  const activeExecutionElapsed = activeRunExecutionState ? formatElapsedMs(executionNow - activeRunExecutionState.startedAt) : null
  const activePhaseStatus = agentOSData?.run_state?.phase_status ?? ''
  const ownerWorkingNow = activePhaseStatus === 'in_progress'
  const phaseEnteredAtMs = agentOSData?.run_state?.phase_entered_at ? Date.parse(agentOSData.run_state.phase_entered_at) : NaN
  const activePhaseElapsed = Number.isFinite(phaseEnteredAtMs) ? formatElapsedMs(Math.max(0, executionNow - phaseEnteredAtMs)) : null
  return (
    <>
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

      {selectedExecutionLog && (
        <ExecutionLogModal job={selectedExecutionLog} onClose={() => setSelectedExecutionLog(null)} />
      )}

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
    </>
  )
}
