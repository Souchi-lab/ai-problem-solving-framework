import { useCallback, useState } from 'react'
import type { AgentOSInfo, AgentOSActionFeedback } from '../types'
import { apiLoadAgentOS } from '../api/runsApi'

export function useAgentOS() {
  const [agentOSData, setAgentOSData] = useState<AgentOSInfo | null>(null)
  const [agentOSLoading, setAgentOSLoading] = useState(false)
  const [agentOSFeedback, setAgentOSFeedback] = useState<AgentOSActionFeedback | null>(null)
  const [selectedRecoveryCheckpointId, setSelectedRecoveryCheckpointId] = useState<string | null>(null)
  const [selectedRecoverySnapshotId, setSelectedRecoverySnapshotId] = useState<string | null>(null)
  const [selectedRecoveryApplyTraceId, setSelectedRecoveryApplyTraceId] = useState<string | null>(null)

  const loadAgentOS = useCallback(apiLoadAgentOS, [])

  const refreshAgentOS = useCallback(async (taxonomy: string, runName: string) => {
    setAgentOSLoading(true)
    try {
      const data = await loadAgentOS(taxonomy, runName)
      setAgentOSData(data)
    } catch {
      setAgentOSData(null)
    } finally {
      setAgentOSLoading(false)
    }
  }, [loadAgentOS])

  return {
    agentOSData,
    setAgentOSData,
    agentOSLoading,
    setAgentOSLoading,
    agentOSFeedback,
    setAgentOSFeedback,
    selectedRecoveryCheckpointId,
    setSelectedRecoveryCheckpointId,
    selectedRecoverySnapshotId,
    setSelectedRecoverySnapshotId,
    selectedRecoveryApplyTraceId,
    setSelectedRecoveryApplyTraceId,
    loadAgentOS,
    refreshAgentOS,
  }
}
