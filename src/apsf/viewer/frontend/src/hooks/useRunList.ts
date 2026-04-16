import { useState } from 'react'
import type { RunSummary, MatrixRow, ActionExecutionRecord, ViewerConfig } from '../types'
import {
  apiLoadOperatorMatrix,
  apiLoadRecentExecutions,
} from '../api/runsApi'
import { apiLoadViewerConfig } from '../api/configApi'

const API_BASE = '/api'

export function useRunList() {
  const [runs, setRuns] = useState<RunSummary[]>([])
  const [isLoadingRuns, setIsLoadingRuns] = useState(true)
  const [runsError, setRunsError] = useState<string | null>(null)
  const [matrixRows, setMatrixRows] = useState<MatrixRow[]>([])
  const [recentExecutions, setRecentExecutions] = useState<ActionExecutionRecord[]>([])
  const [viewerConfig, setViewerConfig] = useState<ViewerConfig | null>(null)
  const [viewerConfigSavingKey, setViewerConfigSavingKey] = useState<string | null>(null)

  const fetchRuns = async () => {
    setRunsError(null)
    try {
      const resp = await fetch(`${API_BASE}/runs`)
      if (!resp.ok) throw new Error(`Failed to load runs (${resp.status})`)
      setRuns(await resp.json())
    } catch (error) {
      setRuns([])
      setRunsError(error instanceof Error ? error.message : 'Failed to load runs')
    } finally {
      setIsLoadingRuns(false)
    }
  }

  return {
    runs,
    setRuns,
    isLoadingRuns,
    setIsLoadingRuns,
    runsError,
    matrixRows,
    setMatrixRows,
    recentExecutions,
    setRecentExecutions,
    viewerConfig,
    setViewerConfig,
    viewerConfigSavingKey,
    setViewerConfigSavingKey,
    fetchRuns,
    loadOperatorMatrix: apiLoadOperatorMatrix,
    loadRecentExecutions: apiLoadRecentExecutions,
    loadViewerConfig: apiLoadViewerConfig,
  }
}
