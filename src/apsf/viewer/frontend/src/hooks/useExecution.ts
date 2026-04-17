import { useEffect, useState } from 'react'
import type {
  OperatorAction,
  MatrixRow,
  ExecutionResult,
  SaveCommentResult,
  RunningExecutionState,
  ModalConfig,
  AgentOSActionFeedback,
} from '../types'
import {
  apiLoadRunDetail,
  apiLoadHistory,
  apiLoadOperatorMatrix,
  apiLoadRecentExecutions,
} from '../api/runsApi'

const API_BASE = '/api'

interface ExecutionParams {
  selectedTaxonomy: string | null
  selectedRun: string | null
  targetRun: string | null
  rerunComments: Record<string, string>
  savedCommentByAction: Record<string, string>
  selectedArtifact: string | null
  selectedRecoveryCheckpointId: string | null
  selectedRecoverySnapshotId: string | null
  setModalConfig: (config: ModalConfig | null) => void
  setMatrixRows: (rows: MatrixRow[]) => void
  setRecentExecutions: (records: import('../types').ActionExecutionRecord[]) => void
  setDetail: (detail: import('../types').RunDetail) => void
  setTargetDetail: (detail: import('../types').RunDetail | null) => void
  setHistory: (history: import('../types').RunHistory) => void
  setHistoryRun: (run: string) => void
  setAgentOSFeedback: (feedback: AgentOSActionFeedback | null) => void
  setSavedCommentByAction: React.Dispatch<React.SetStateAction<Record<string, string>>>
  fetchRuns: () => Promise<void>
  fetchDetail: (taxonomy: string, runName: string) => Promise<void>
  fetchArtifact: (filename: string) => Promise<void>
  refreshRunContexts: (taxonomy: string, runName: string) => Promise<void>
  refreshAgentOS: (taxonomy: string, runName: string) => Promise<void>
}

export function useExecution({
  selectedTaxonomy,
  selectedRun,
  targetRun,
  rerunComments,
  savedCommentByAction,
  selectedArtifact,
  selectedRecoveryCheckpointId,
  selectedRecoverySnapshotId,
  setModalConfig,
  setMatrixRows,
  setRecentExecutions,
  setDetail,
  setTargetDetail,
  setHistory,
  setHistoryRun,
  setAgentOSFeedback,
  setSavedCommentByAction,
  fetchRuns,
  fetchDetail,
  fetchArtifact,
  refreshRunContexts,
  refreshAgentOS,
}: ExecutionParams) {
  const [executionResult, setExecutionResult] = useState<ExecutionResult | null>(null)
  const [saveCommentResult, setSaveCommentResult] = useState<SaveCommentResult | null>(null)
  const [savingActionId, setSavingActionId] = useState<string | null>(null)
  const [executingRuns, setExecutingRuns] = useState<Record<string, RunningExecutionState>>({})
  const [executionNow, setExecutionNow] = useState(() => Date.now())

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
            apiLoadOperatorMatrix().then(setMatrixRows).catch(() => {}),
            apiLoadRecentExecutions().then(setRecentExecutions).catch(() => {}),
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
    const activeTargetName = targetRun ?? null
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
            apiLoadOperatorMatrix().then(setMatrixRows).catch(() => {}),
            apiLoadRecentExecutions().then(setRecentExecutions).catch(() => {}),
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
        apiLoadOperatorMatrix().then(setMatrixRows).catch(() => {}),
        apiLoadRecentExecutions().then(setRecentExecutions).catch(() => {}),
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

  // Keep executionNow ticking while any run is executing or a run is selected
  useEffect(() => {
    if (Object.keys(executingRuns).length === 0 && !targetRun) return
    const timer = window.setInterval(() => setExecutionNow(Date.now()), 1000)
    return () => window.clearInterval(timer)
  }, [executingRuns, targetRun])

  return {
    executionResult,
    setExecutionResult,
    saveCommentResult,
    setSaveCommentResult,
    savingActionId,
    executingRuns,
    executionNow,
    setExecutionNow,
    isRunExecuting,
    executingStateForRun,
    executingActionForRun,
    startRunExecution,
    finishRunExecution,
    saveRerunComment,
    executeAction,
    executeMatrixAction,
    executeAgentOSAction,
  }
}
