import { useEffect } from 'react'
import type { RunDetail, RunHistory, AgentOSInfo } from '../types'
import { apiLoadRunDetail, apiLoadHistory } from '../api/runsApi'

const SELECTED_RUN_REFRESH_MS = 10000

interface PeriodicRefreshParams {
  selectedRun: string | null
  selectedTaxonomy: string | null
  targetRun: string | null
  refreshRequestIdRef: React.MutableRefObject<number>
  viewerConfigRefreshMs: number | undefined
  loadAgentOS: (taxonomy: string, runName: string) => Promise<AgentOSInfo>
  setDetail: (detail: RunDetail) => void
  setTargetDetail: (detail: RunDetail | null) => void
  setHistory: (history: RunHistory) => void
  setHistoryRun: (run: string) => void
  setAgentOSData: (data: AgentOSInfo) => void
}

export function usePeriodicRefresh({
  selectedRun,
  selectedTaxonomy,
  targetRun,
  refreshRequestIdRef,
  viewerConfigRefreshMs,
  loadAgentOS,
  setDetail,
  setTargetDetail,
  setHistory,
  setHistoryRun,
  setAgentOSData,
}: PeriodicRefreshParams) {
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
    }, viewerConfigRefreshMs ?? SELECTED_RUN_REFRESH_MS)
    return () => clearInterval(detailTimer)
  }, [loadAgentOS, selectedRun, selectedTaxonomy, targetRun, viewerConfigRefreshMs])
}
