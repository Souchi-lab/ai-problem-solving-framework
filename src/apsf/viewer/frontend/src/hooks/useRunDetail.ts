import { useState, useRef, useCallback } from 'react'
import type {
  RunDetail,
  RunHistory,
  CodexBridgeResult,
  ModalConfig,
  ViewerConfig,
  MatrixRow,
  ActionExecutionRecord,
} from '../types'
import { apiLoadRunDetail, apiLoadHistory } from '../api/runsApi'
import { apiUpdateViewerConfig } from '../api/configApi'

const API_BASE = '/api'

export const DEFAULT_PREVIEW_PHASES = new Set(['COMPLETE', 'TRANSCRIPT_RECOMMENDED'])
export const TRANSCRIPT_ARTIFACT = 'transcript.md'
export const RESULT_ARTIFACT = 'result.md'

interface UseRunDetailParams {
  setAgentOSLoading: (v: boolean) => void
  setAgentOSData: (v: null) => void
  loadAgentOS: (taxonomy: string, runName: string) => Promise<import('../types').AgentOSInfo>
  loadSpecialistCandidates: (taxonomy: string, runName: string, phaseOverride?: string | null) => Promise<void>
  setArtifactModalOpen: (v: boolean) => void
  setModalConfig: (config: ModalConfig | null) => void
  loadOperatorMatrix: () => Promise<MatrixRow[]>
  loadRecentExecutions: () => Promise<ActionExecutionRecord[]>
  setMatrixRows: (rows: MatrixRow[]) => void
  setRecentExecutions: (records: ActionExecutionRecord[]) => void
}

export function useRunDetail({
  setAgentOSLoading,
  setAgentOSData,
  loadAgentOS,
  loadSpecialistCandidates,
  setArtifactModalOpen,
  setModalConfig,
  loadOperatorMatrix,
  loadRecentExecutions,
  setMatrixRows,
  setRecentExecutions,
}: UseRunDetailParams) {
  const [detail, setDetail] = useState<RunDetail | null>(null)
  const [selectedRun, setSelectedRun] = useState<string | null>(null)
  const [selectedTaxonomy, setSelectedTaxonomy] = useState<string | null>(null)
  const [targetRun, setTargetRun] = useState<string | null>(null)
  const [targetDetail, setTargetDetail] = useState<RunDetail | null>(null)
  const [history, setHistory] = useState<RunHistory | null>(null)
  const [historyRun, setHistoryRun] = useState<string | null>(null)
  const [selectedArtifact, setSelectedArtifact] = useState<string | null>(null)
  const [artifactContent, setArtifactContent] = useState<string>('')
  const [codexResult, setCodexResult] = useState<CodexBridgeResult | null>(null)
  const [codexError, setCodexError] = useState<string | null>(null)
  const [codexLoadingPreset, setCodexLoadingPreset] = useState<CodexBridgeResult['preset_id'] | null>(null)
  const [codexTargetKey, setCodexTargetKey] = useState<string | null>(null)

  const detailRequestIdRef = useRef(0)
  const refreshRequestIdRef = useRef(0)

  // Keep refs to current state for use in callbacks
  const selectedTaxonomyRef = useRef<string | null>(null)
  const selectedRunRef = useRef<string | null>(null)
  const targetRunRef = useRef<string | null>(null)
  const detailRef = useRef<RunDetail | null>(null)
  const targetDetailRef = useRef<RunDetail | null>(null)
  const selectedArtifactRef = useRef<string | null>(null)
  const artifactContentRef = useRef<string>('')

  selectedTaxonomyRef.current = selectedTaxonomy
  selectedRunRef.current = selectedRun
  targetRunRef.current = targetRun
  detailRef.current = detail
  targetDetailRef.current = targetDetail
  selectedArtifactRef.current = selectedArtifact
  artifactContentRef.current = artifactContent

  const specialistPhaseOverride =
    (targetDetail?.phase === 'IMPROVE_NEEDED' && targetDetail?.judge_recommendation?.suggested_return_phase)
      ? targetDetail.judge_recommendation.suggested_return_phase
      : (detail?.phase === 'IMPROVE_NEEDED' && detail?.judge_recommendation?.suggested_return_phase)
        ? detail.judge_recommendation.suggested_return_phase
        : null

  const fetchArtifact = useCallback(async (filename: string) => {
    const taxonomy = selectedTaxonomyRef.current
    const run = targetRunRef.current
    if (!run || !taxonomy) return
    setSelectedArtifact(filename)
    const resp = await fetch(`${API_BASE}/runs/${taxonomy}/${encodeURIComponent(run)}/artifacts/${filename}`)
    const data = await resp.json()
    setArtifactContent(data.content ?? '')
  }, [])

  const refreshRunContexts = useCallback(async (taxonomy: string, runName: string) => {
    const currentDetail = detailRef.current
    const currentSelectedTaxonomy = selectedTaxonomyRef.current
    const currentTargetRun = targetRunRef.current
    const refreshes: Promise<void>[] = []
    if (currentDetail && currentSelectedTaxonomy === taxonomy) {
      refreshes.push(
        apiLoadRunDetail(taxonomy, currentDetail.name).then((refreshedDetail) => {
          setDetail(refreshedDetail)
          if ((currentTargetRun ?? currentDetail.name) === currentDetail.name) {
            setTargetDetail(refreshedDetail)
          }
        }),
      )
    }
    refreshes.push(
      Promise.all([apiLoadRunDetail(taxonomy, runName), apiLoadHistory(taxonomy, runName)]).then(([refreshedRun, refreshedHistory]) => {
        if (selectedTaxonomyRef.current === taxonomy && targetRunRef.current === runName) {
          setTargetDetail(refreshedRun)
          setHistory(refreshedHistory)
          setHistoryRun(runName)
        }
      }),
    )
    await Promise.all(refreshes)
  }, [])

  const fetchDetail = useCallback(async (taxonomy: string, runName: string) => {
    const requestId = ++detailRequestIdRef.current
    setSelectedRun(runName)
    setSelectedTaxonomy(taxonomy)
    setTargetRun(runName)
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
  }, [setArtifactModalOpen])

  const fetchTargetDetail = useCallback(async (taxonomy: string, runName: string) => {
    const requestId = ++detailRequestIdRef.current
    const previousTargetRun = targetRunRef.current
    const currentDetail = detailRef.current
    const currentTargetDetail = targetDetailRef.current
    const currentSpecialistPhaseOverride =
      (currentTargetDetail?.phase === 'IMPROVE_NEEDED' && currentTargetDetail?.judge_recommendation?.suggested_return_phase)
        ? currentTargetDetail.judge_recommendation.suggested_return_phase
        : (currentDetail?.phase === 'IMPROVE_NEEDED' && currentDetail?.judge_recommendation?.suggested_return_phase)
          ? currentDetail.judge_recommendation.suggested_return_phase
          : null
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
      void loadSpecialistCandidates(taxonomy, runName, currentSpecialistPhaseOverride)
      return agentData
    } catch (error) {
      if (detailRequestIdRef.current !== requestId) return
      setTargetRun(previousTargetRun ?? currentDetail?.name ?? null)
      setTargetDetail(previousTargetRun && currentDetail && previousTargetRun !== currentDetail.name ? currentTargetDetail : currentDetail)
      setModalConfig({
        title: 'Failed to Open Target Run',
        message: error instanceof Error ? error.message : 'Failed to load the selected run context.',
        onConfirm: () => setModalConfig(null),
      })
      return null
    } finally {
      if (detailRequestIdRef.current === requestId) {
        setAgentOSLoading(false)
      }
    }
  }, [setAgentOSLoading, setAgentOSData, setArtifactModalOpen, loadAgentOS, loadSpecialistCandidates, setModalConfig])

  const openArtifactReferenceModal = useCallback((preferredArtifact?: string) => {
    const currentTargetDetail = targetDetailRef.current
    const currentDetail = detailRef.current
    const currentSelectedArtifact = selectedArtifactRef.current
    const currentArtifactContent = artifactContentRef.current
    const availableArtifacts = (currentTargetDetail?.artifacts ?? currentDetail?.artifacts ?? []).filter((artifact) => artifact.exists)
    if (availableArtifacts.length === 0) return
    const nextArtifact =
      preferredArtifact
      ?? (currentSelectedArtifact && availableArtifacts.some((artifact) => artifact.name === currentSelectedArtifact) ? currentSelectedArtifact : null)
      ?? availableArtifacts[0].name
    setArtifactModalOpen(true)
    if (nextArtifact !== currentSelectedArtifact || currentArtifactContent === '') {
      void fetchArtifact(nextArtifact)
    }
  }, [setArtifactModalOpen, fetchArtifact])

  const invokeCodexPreset = useCallback(async (presetId: CodexBridgeResult['preset_id'], taxonomy: string, runName: string) => {
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
  }, [])

  const updateViewerConfig = useCallback(async (
    patch: Partial<Pick<ViewerConfig, 'execution_mode' | 'cli_tool_mode' | 'build_max_turns' | 'run_detail_refresh_ms'>>,
    setViewerConfig: (cfg: ViewerConfig | null) => void,
    setViewerConfigSavingKey: (key: string | null) => void,
  ) => {
    const savingKey = patch.execution_mode ? `execution:${patch.execution_mode}` : patch.cli_tool_mode ? `cli:${patch.cli_tool_mode}` : patch.build_max_turns !== undefined ? 'build_max_turns' : 'run_detail_refresh_ms'
    setViewerConfigSavingKey(savingKey)
    const currentSelectedTaxonomy = selectedTaxonomyRef.current
    const currentSelectedRun = selectedRunRef.current
    const currentTargetRun = targetRunRef.current
    try {
      const data = await apiUpdateViewerConfig(patch)
      setViewerConfig(data)
      const [rows, recent] = await Promise.all([
        loadOperatorMatrix().catch(() => []),
        loadRecentExecutions().catch(() => []),
      ])
      setMatrixRows(rows)
      setRecentExecutions(recent)
      if (currentSelectedRun && currentSelectedTaxonomy) {
        const requestId = ++detailRequestIdRef.current
        const parentPromise = apiLoadRunDetail(currentSelectedTaxonomy, currentSelectedRun)
        const historyTarget = currentTargetRun ?? currentSelectedRun
        const historyPromise = apiLoadHistory(currentSelectedTaxonomy, historyTarget)
        const targetPromise = currentTargetRun ? apiLoadRunDetail(currentSelectedTaxonomy, currentTargetRun) : parentPromise
        const [parentData, historyData, targetData] = await Promise.all([parentPromise, historyPromise, targetPromise])
        if (detailRequestIdRef.current === requestId) {
          setDetail(parentData)
          setHistory(historyData)
          setHistoryRun(historyTarget)
          setTargetDetail(currentTargetRun ? targetData : null)
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
  }, [loadOperatorMatrix, loadRecentExecutions, setMatrixRows, setRecentExecutions, setModalConfig])

  return {
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
    fetchTargetDetail,
    openArtifactReferenceModal,
    invokeCodexPreset,
    updateViewerConfig,
  }
}
