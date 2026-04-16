import type { ViewerConfig } from '../types'

const API_BASE = '/api'

export async function apiLoadViewerConfig(): Promise<ViewerConfig> {
  const resp = await fetch(`${API_BASE}/viewer-config`)
  if (!resp.ok) throw new Error(`Failed to load viewer config (${resp.status})`)
  return resp.json()
}

export async function apiUpdateViewerConfig(
  patch: Partial<Pick<ViewerConfig, 'execution_mode' | 'cli_tool_mode' | 'build_max_turns' | 'run_detail_refresh_ms'>>,
): Promise<ViewerConfig> {
  const resp = await fetch(`${API_BASE}/viewer-config`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(patch),
  })
  const data = await resp.json()
  if (!resp.ok) throw new Error(data.detail ?? `Failed to update viewer config (${resp.status})`)
  return data as ViewerConfig
}
