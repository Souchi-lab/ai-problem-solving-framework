import { useState } from 'react'
import type { SpecialistCandidatesData, CreateSpecialistResult } from '../types'
import { apiLoadSpecialistCandidates } from '../api/runsApi'
import { mergeCreatedSpecialistCandidate } from '../utils/specialist'

const API_BASE = '/api'

interface SpecialistParams {
  selectedTaxonomy: string | null
  targetRun: string | null
  specialistPhaseOverride: string | null
  selectedArtifact: string | null
  fetchArtifact: (filename: string) => Promise<void>
  refreshAgentOS: (taxonomy: string, runName: string) => Promise<void>
  refreshRunContexts: (taxonomy: string, runName: string) => Promise<void>
  setAgentOSFeedback: (feedback: import('../types').AgentOSActionFeedback | null) => void
  setSpecialistModalOpen: (open: boolean) => void
  setCreateSpecialistModalOpen: (open: boolean) => void
}

export function useSpecialists({
  selectedTaxonomy,
  targetRun,
  specialistPhaseOverride,
  selectedArtifact,
  fetchArtifact,
  refreshAgentOS,
  refreshRunContexts,
  setAgentOSFeedback,
  setSpecialistModalOpen,
  setCreateSpecialistModalOpen,
}: SpecialistParams) {
  const [specialistCandidates, setSpecialistCandidates] = useState<SpecialistCandidatesData | null>(null)
  const [specialistModalSelectedCode, setSpecialistModalSelectedCode] = useState<string | null>(null)
  const [createdSpecialistResult, setCreatedSpecialistResult] = useState<CreateSpecialistResult | null>(null)

  const loadSpecialistCandidates = async (taxonomy: string, runName: string, phaseOverride?: string | null): Promise<SpecialistCandidatesData | null> => {
    try {
      const data = await apiLoadSpecialistCandidates(taxonomy, runName, phaseOverride)
      setSpecialistCandidates(data)
      return data
    } catch {
      setSpecialistCandidates(null)
      return null
    }
  }

  const handleConfirmSpecialist = async (code: string) => {
    if (!selectedTaxonomy || !targetRun || !specialistCandidates) return
    const resp = await fetch(
      `${API_BASE}/runs/${selectedTaxonomy}/${encodeURIComponent(targetRun)}/confirm-specialist`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ role: specialistCandidates.role, specialist_code: code, source: 'operator-accept' }),
      }
    )
    const data = await resp.json().catch(() => ({} as { detail?: string; artifact_path?: string; target_run_name?: string }))
    if (!resp.ok) {
      throw new Error((data as { detail?: string }).detail || `HTTP ${resp.status}`)
    }
    setCreatedSpecialistResult(null)
    setSpecialistModalSelectedCode(code)
    await Promise.all([
      loadSpecialistCandidates(selectedTaxonomy, targetRun, specialistPhaseOverride),
      refreshAgentOS(selectedTaxonomy, targetRun),
      refreshRunContexts(selectedTaxonomy, targetRun),
    ])
    if (selectedArtifact === 'execution-assignment.md') {
      await fetchArtifact('execution-assignment.md')
    }
    setAgentOSFeedback({
      kind: 'success',
      title: 'Specialist Assignment Updated',
      detail: `Updated ${(data as { artifact_path?: string }).artifact_path || 'execution-assignment.md'} for ${(data as { target_run_name?: string }).target_run_name || targetRun}.`,
      actionId: 'act',
    })
    setSpecialistModalOpen(false)
  }

  const handleCreatedSpecialist = async (result: CreateSpecialistResult) => {
    if (!selectedTaxonomy || !targetRun) return
    setCreateSpecialistModalOpen(false)
    const refreshed = await loadSpecialistCandidates(selectedTaxonomy, targetRun, specialistPhaseOverride)
    const merged = mergeCreatedSpecialistCandidate(refreshed, result)
    if (merged) {
      setSpecialistCandidates(merged)
    }
    setCreatedSpecialistResult(result)
    setSpecialistModalSelectedCode(result.specialist_code)
    setSpecialistModalOpen(true)
  }

  const openSpecialistSelectionModal = async (initialCode?: string) => {
    if (!selectedTaxonomy || !targetRun) return
    const refreshed = await loadSpecialistCandidates(selectedTaxonomy, targetRun, specialistPhaseOverride)
    if (refreshed) {
      setSpecialistCandidates(refreshed)
      setSpecialistModalSelectedCode(initialCode ?? refreshed.current_code ?? '')
    } else {
      setSpecialistModalSelectedCode(initialCode ?? '')
    }
    setCreatedSpecialistResult(null)
    setSpecialistModalOpen(true)
  }

  const openSpecialistSelectionForPhase = async (phase: string) => {
    if (!selectedTaxonomy || !targetRun) return
    const refreshed = await loadSpecialistCandidates(selectedTaxonomy, targetRun, phase)
    if (refreshed) {
      setSpecialistCandidates(refreshed)
      setSpecialistModalSelectedCode(refreshed.current_code ?? '')
    } else {
      setSpecialistModalSelectedCode('')
    }
    setCreatedSpecialistResult(null)
    setSpecialistModalOpen(true)
  }

  return {
    specialistCandidates,
    setSpecialistCandidates,
    specialistModalSelectedCode,
    setSpecialistModalSelectedCode,
    createdSpecialistResult,
    setCreatedSpecialistResult,
    loadSpecialistCandidates,
    handleConfirmSpecialist,
    handleCreatedSpecialist,
    openSpecialistSelectionModal,
    openSpecialistSelectionForPhase,
  }
}
