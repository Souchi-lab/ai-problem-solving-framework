import type { RunDetail, RunHistory, MatrixRow, ActionExecutionRecord, AgentOSInfo, SpecialistCandidatesData } from '../types'

const API_BASE = '/api'

async function parseJsonOrThrowText(resp: Response) {
  const text = await resp.text()
  if (!text) return {}
  try {
    return JSON.parse(text)
  } catch {
    throw new Error(text)
  }
}

export async function apiLoadRunDetail(taxonomy: string, runName: string): Promise<RunDetail> {
  const resp = await fetch(`${API_BASE}/runs/${taxonomy}/${encodeURIComponent(runName)}`)
  const data = await parseJsonOrThrowText(resp)
  if (!resp.ok) {
    const detail = typeof data === 'object' && data && 'detail' in data ? String((data as { detail?: unknown }).detail ?? '') : ''
    throw new Error(detail || `Failed to load run detail (${resp.status})`)
  }
  return data as RunDetail
}

export async function apiLoadHistory(taxonomy: string, runName: string): Promise<RunHistory> {
  const resp = await fetch(`${API_BASE}/runs/${taxonomy}/${encodeURIComponent(runName)}/history`)
  const data = await parseJsonOrThrowText(resp)
  if (!resp.ok) {
    const detail = typeof data === 'object' && data && 'detail' in data ? String((data as { detail?: unknown }).detail ?? '') : ''
    throw new Error(detail || `Failed to load history (${resp.status})`)
  }
  return data as RunHistory
}

export async function apiLoadOperatorMatrix(): Promise<MatrixRow[]> {
  const resp = await fetch(`${API_BASE}/operator-matrix`)
  return resp.json()
}

export async function apiLoadRecentExecutions(): Promise<ActionExecutionRecord[]> {
  const resp = await fetch(`${API_BASE}/executions/recent?limit=12&top_level_only=true`)
  return resp.json()
}

export async function apiLoadAgentOS(taxonomy: string, runName: string): Promise<AgentOSInfo> {
  const resp = await fetch(`${API_BASE}/runs/${taxonomy}/${encodeURIComponent(runName)}/agent-os`)
  const data = await parseJsonOrThrowText(resp)
  if (!resp.ok) {
    const detail = typeof data === 'object' && data && 'detail' in data ? String((data as { detail?: unknown }).detail ?? '') : ''
    throw new Error(detail || `Failed to load Agent OS (${resp.status})`)
  }
  return {
    run_state: data.run_state ?? null,
    artifact_manifest: data.artifact_manifest ?? null,
    gate_results: Array.isArray(data.gate_results) ? data.gate_results : [],
    force_audit: Array.isArray(data.force_audit) ? data.force_audit : null,
    recovery_checkpoints: Array.isArray(data.recovery_checkpoints) ? data.recovery_checkpoints : [],
    recovery_snapshots: Array.isArray(data.recovery_snapshots) ? data.recovery_snapshots : [],
    recovery_apply_traces: Array.isArray(data.recovery_apply_traces) ? data.recovery_apply_traces : [],
  }
}

export async function apiLoadSpecialistCandidates(
  taxonomy: string,
  runName: string,
  phaseOverride?: string | null,
): Promise<SpecialistCandidatesData | null> {
  const params = new URLSearchParams()
  if (phaseOverride) params.set('phase', phaseOverride)
  const resp = await fetch(
    `${API_BASE}/runs/${taxonomy}/${encodeURIComponent(runName)}/specialist-candidates${params.toString() ? `?${params.toString()}` : ''}`
  )
  if (!resp.ok) return null
  return resp.json()
}
