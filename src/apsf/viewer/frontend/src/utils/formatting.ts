export function stripMarkdownForSummary(markdown: string) {
  return markdown
    .replace(/```[\s\S]*?```/g, ' ')
    .replace(/`([^`]+)`/g, '$1')
    .replace(/^#{1,6}\s*/gm, '')
    .replace(/^\|.*\|$/gm, '')
    .replace(/^\s*[-*+]\s+/gm, '• ')
    .replace(/^\s*\d+\.\s+/gm, '• ')
    .replace(/\*\*([^*]+)\*\*/g, '$1')
    .replace(/\*([^*]+)\*/g, '$1')
    .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1')
    .replace(/\r/g, '')
}

// Extract first meaningful line from raw markdown for stop-summary display
export function extractSummaryLine(markdown: string, maxLen = 130): string {
  return (
    stripMarkdownForSummary(markdown)
      .split('\n')
      .map((l) => l.trim())
      .filter((l) => l && l !== '---' && !/^•\s*\[[ xX]\]/.test(l) && l.length > 10)
      .at(0)
      ?.slice(0, maxLen) ?? ''
  )
}

export const formatDuration = (start?: string | null, end?: string | null) => {
  if (!start || !end) return null
  try {
    const d1 = new Date(start)
    const d2 = new Date(end)
    const diff = Math.floor((d2.getTime() - d1.getTime()) / 1000)
    if (diff < 0) return null
    if (diff < 60) return `${diff}s`
    return `${Math.floor(diff / 60)}m ${diff % 60}s`
  } catch {
    return null
  }
}

export const formatRelativeTime = (isoString?: string | null) => {
  if (!isoString) return '-'
  try {
    const date = new Date(isoString)
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffSec = Math.floor(diffMs / 1000)

    if (diffSec < 60) return 'Just now'
    if (diffSec < 3600) return `${Math.floor(diffSec / 60)}m ago`
    if (diffSec < 86400) return `${Math.floor(diffSec / 3600)}h ago`
    return date.toLocaleDateString()
  } catch {
    return isoString
  }
}

export const formatElapsedMs = (elapsedMs: number) => {
  const totalSeconds = Math.max(0, Math.floor(elapsedMs / 1000))
  const minutes = Math.floor(totalSeconds / 60)
  const seconds = totalSeconds % 60
  return `${minutes}:${seconds.toString().padStart(2, '0')}`
}

export function parseSatisfiabilityReason(reason?: string | null) {
  if (!reason) return { primary: '', warning: null as null | { state: 'EXPLORATORY' | 'UNSATISFIED'; message: string } }

  const markerMatch = reason.match(/\[SATISFIABILITY:\s*(EXPLORATORY|UNSATISFIED)\]\s*([\s\S]*)/i)
  if (!markerMatch) {
    return { primary: reason, warning: null as null | { state: 'EXPLORATORY' | 'UNSATISFIED'; message: string } }
  }

  const markerStart = markerMatch.index ?? 0
  const primary = reason.slice(0, markerStart).trim()
  const state = markerMatch[1].toUpperCase() as 'EXPLORATORY' | 'UNSATISFIED'
  const message = markerMatch[2].trim()
  return {
    primary,
    warning: {
      state,
      message,
    },
  }
}

export function buildExecutionLogText(stdout?: string | null, stderr?: string | null) {
  const parts: string[] = []
  if (stdout?.trim()) {
    parts.push(`STDOUT\n${stdout.trim()}`)
  }
  if (stderr?.trim()) {
    parts.push(`STDERR\n${stderr.trim()}`)
  }
  return parts.join('\n\n')
}

export function hasExecutionLogContent(stdout?: string | null, stderr?: string | null) {
  return Boolean(stdout?.trim() || stderr?.trim())
}

export function formatAgentOSTimestamp(value?: string | null) {
  if (!value) return '—'
  try {
    return new Date(value).toLocaleString()
  } catch {
    return value
  }
}

export function prettifyActionId(actionId?: string | null) {
  if (!actionId) return 'Unknown Action'
  return actionId
    .split(/[-_]/g)
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(' ')
}

export function summarizeExecutionIntent(actionId?: string | null, command?: string | null, actionType?: string | null) {
  const normalized = (actionId || '').trim()
  const commandText = (command || '').trim().toLowerCase()
  const typeText = (actionType || '').trim().toLowerCase()
  if (normalized === 'phase-primary') {
    if (typeText === 'build' || commandText.includes('apsf-wrapper-build') || commandText.includes('apsf build')) return 'Ran Builder'
    if (typeText === 'act') {
      if (commandText.includes('review_needed') || commandText.includes('critic')) return 'Ran Critic'
      if (commandText.includes('plan_needed') || commandText.includes('planner')) return 'Ran Planner'
      return 'Ran phase actor'
    }
    return 'Primary phase action executed'
  }
  if (normalized === 'rerun-plan') return 'Returned the run to Planner'
  if (normalized === 'rerun-build') return 'Returned the run to Builder'
  if (normalized === 'rerun-review') return 'Returned the run to Critic'
  if (normalized === 'rerun-improve') return 'Reopened the Judge step'
  if (normalized === 'act') return 'Ran the current phase actor'
  if (normalized === 'capture-snapshot') return 'Captured a recovery snapshot'
  if (normalized === 'capture-checkpoint') return 'Captured an execution checkpoint'
  if (normalized === 'apply-snapshot') return 'Applied a recovery snapshot'
  if (normalized === 'apply-checkpoint') return 'Applied an execution checkpoint'

  const text = (command || '').trim()
  if (!text) return prettifyActionId(actionId)
  const firstLine = text.split('\n')[0]?.trim()
  return firstLine || prettifyActionId(actionId)
}

export function summarizeExecutionOutcome(stdoutSummary?: string | null, stderrSummary?: string | null) {
  const source = (stderrSummary || stdoutSummary || '').trim()
  if (!source) return 'No summary recorded.'
  return source.split('\n').map((line) => line.trim()).find(Boolean) || 'No summary recorded.'
}

export function loadStoredStringArray(key: string, fallback: string[]) {
  if (typeof window === 'undefined') return fallback
  try {
    const raw = window.localStorage.getItem(key)
    if (!raw) return fallback
    const parsed = JSON.parse(raw)
    return Array.isArray(parsed) ? parsed.filter((value): value is string => typeof value === 'string') : fallback
  } catch {
    return fallback
  }
}
