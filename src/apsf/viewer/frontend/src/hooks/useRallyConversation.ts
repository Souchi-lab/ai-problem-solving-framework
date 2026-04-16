import { useCallback, useState } from 'react'
import type { RunDetail, RallyMessage } from '../types'
import { parseSpecialistCodes } from '../utils/specialist'

const API_BASE = '/api'

interface RallyParams {
  selectedTaxonomy: string | null
  targetRun: string | null
  detail: RunDetail | null
  targetDetail: RunDetail | null
}

export function useRallyConversation({ selectedTaxonomy, targetRun, detail, targetDetail }: RallyParams) {
  const [rallyMessages, setRallyMessages] = useState<RallyMessage[]>([])
  const [rallyLoading, setRallyLoading] = useState(false)
  const [rallySpecialistCodes, setRallySpecialistCodes] = useState<{ planner: string; builder: string; critic: string }>({ planner: '', builder: '', critic: '' })

  const openRallyConversation = useCallback(async (setRallyModalOpen: (open: boolean) => void) => {
    if (!selectedTaxonomy || !targetRun) return
    const availableArtifacts = (targetDetail?.artifacts ?? detail?.artifacts ?? []).filter((artifact) => artifact.exists)
    const orderedArtifacts = [
      { name: 'goal.md', speaker: 'Result', title: 'Goal' },
      { name: 'plan.md', speaker: 'Judge', title: 'Plan' },
      { name: 'build.md', speaker: 'Builder', title: 'Build Report' },
      { name: 'build_review.md', speaker: 'Judge', title: 'Judge Feedback' },
      { name: 'review.md', speaker: 'Critic', title: 'Critic Comment' },
      { name: 'review_review.md', speaker: 'Judge', title: 'Judge Feedback' },
      { name: 'improve.md', speaker: 'Judge', title: 'Judge Decision' },
      { name: 'improve_review.md', speaker: 'Judge', title: 'Improve Feedback' },
      { name: 'result.md', speaker: 'Result', title: 'Closeout' },
    ]

    setRallyLoading(true)
    setRallyModalOpen(true)
    try {
      // Fetch specialist codes from execution-assignment.md in parallel
      const assignmentFetch = fetch(
        `${API_BASE}/runs/${selectedTaxonomy}/${encodeURIComponent(targetRun)}/artifacts/execution-assignment.md`
      )
        .then((r) => r.json())
        .catch(() => ({}))

      const [loaded, assignmentData] = await Promise.all([
        Promise.all(
          orderedArtifacts.map(async (item) => {
            const exists = availableArtifacts.some((artifact) => artifact.name === item.name)
            if (!exists) {
              return { artifact: item.name, speaker: item.speaker, title: item.title, content: '', exists: false } as RallyMessage
            }
            const resp = await fetch(`${API_BASE}/runs/${selectedTaxonomy}/${encodeURIComponent(targetRun)}/artifacts/${item.name}`)
            const data = await resp.json().catch(() => ({}))
            const raw = typeof data.content === 'string' ? data.content : ''
            return { artifact: item.name, speaker: item.speaker, title: item.title, content: raw, exists: raw.trim() !== '' } as RallyMessage
          })
        ),
        assignmentFetch,
      ])

      // Parse specialist codes
      const assignmentContent = typeof assignmentData.content === 'string' ? assignmentData.content : ''
      setRallySpecialistCodes(parseSpecialistCodes(assignmentContent))

      // Show existing artifacts + first pending artifact only
      const lastWrittenIndex = loaded.map((item) => item.exists).lastIndexOf(true)
      const firstPendingAfterWritten =
        lastWrittenIndex >= 0
          ? loaded.findIndex((item, index) => index > lastWrittenIndex && !item.exists)
          : loaded.findIndex((item) => !item.exists)
      const filtered = loaded.filter((item, index) => item.exists || index === firstPendingAfterWritten)
      setRallyMessages(filtered)
    } catch (error) {
      setRallyMessages([
        { artifact: 'system', speaker: 'Result', title: 'Load Error', content: error instanceof Error ? error.message : 'Failed to load rally.', exists: false },
      ])
    } finally {
      setRallyLoading(false)
    }
  }, [detail?.artifacts, selectedTaxonomy, targetDetail?.artifacts, targetRun])

  return {
    rallyMessages,
    setRallyMessages,
    rallyLoading,
    rallySpecialistCodes,
    openRallyConversation,
  }
}
