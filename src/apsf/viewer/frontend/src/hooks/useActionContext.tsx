import type { OperatorAction, RunDetail } from '../types'
import { OperatorActionCard } from '../components/OperatorActionCard'

interface ActionContextParams {
  targetDetail: RunDetail | null
  activeJudgeRecommendation: RunDetail['judge_recommendation']
  activeDetailPhase: string | null
  executionNow: number
  savingActionId: string | null
  rerunComments: Record<string, string>
  savedCommentByAction: Record<string, string>
  setRerunComments: React.Dispatch<React.SetStateAction<Record<string, string>>>
  setSavedCommentByAction: React.Dispatch<React.SetStateAction<Record<string, string>>>
  executingActionForRun: (taxonomy: string, runName: string) => string | null
  executingStateForRun: (taxonomy: string, runName: string) => { actionId: string; startedAt: number } | null
  saveRerunComment: (action: OperatorAction, taxonomy: string, runName: string) => Promise<void>
  executeAction: (action: OperatorAction, taxonomy: string, runName: string) => Promise<void>
}

export function useActionContext({
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
}: ActionContextParams) {
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
  const primaryExecutableAction = executableActions.find((action) => action.primary) ?? executableActions[0] ?? null
  const phaseContextActions = activeDetailPhase === 'IMPROVE_NEEDED' ? sortedDetailActions : [...executableActions, ...humanActions]
  const suggestedJudgeAction =
    activeJudgeRecommendation?.suggested_action_id
      ? detailActions.find((action) => action.id === activeJudgeRecommendation.suggested_action_id) ?? null
      : null

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

  return {
    recommendedActionId,
    sortedDetailActions,
    executableActions,
    humanActions,
    primaryExecutableAction,
    phaseContextActions,
    suggestedJudgeAction,
    renderOperatorAction,
  }
}
