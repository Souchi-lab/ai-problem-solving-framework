import type { ArtifactPreview } from '../types'

export const ARTIFACT_REFERENCE_GROUPS = [
  { key: 'G', label: 'Goal' },
  { key: 'P', label: 'Plan' },
  { key: 'B', label: 'Build' },
  { key: 'I', label: 'Improve' },
  { key: 'R', label: 'Result' },
] as const

const ARTIFACT_DISPLAY_META: Record<string, { group: (typeof ARTIFACT_REFERENCE_GROUPS)[number]['key']; title: string }> = {
  'execution-assignment.md': { group: 'G', title: 'Execution Assignment' },
  'model-assignment.md': { group: 'G', title: 'Model Assignment' },
  'goal.md': { group: 'G', title: 'Goal' },
  'plan.md': { group: 'P', title: 'Plan' },
  'plan_review.md': { group: 'P', title: 'Plan Review' },
  'handoff.md': { group: 'P', title: 'Handoff' },
  'build.md': { group: 'B', title: 'Build' },
  'build_review.md': { group: 'B', title: 'Build Review' },
  'review.md': { group: 'I', title: 'Review' },
  'review_review.md': { group: 'I', title: 'Review Rework' },
  'improve.md': { group: 'I', title: 'Improve' },
  'improve_review.md': { group: 'I', title: 'Improve Review' },
  'result.md': { group: 'R', title: 'Result' },
  'transcript.md': { group: 'R', title: 'Transcript' },
}

export function titleCaseArtifactName(value: string) {
  return value
    .replace(/\.md$/i, '')
    .split(/[_-]+/)
    .filter(Boolean)
    .map((segment) => segment.charAt(0).toUpperCase() + segment.slice(1))
    .join(' ')
}

export function getArtifactDisplayMeta(name: string) {
  const exact = ARTIFACT_DISPLAY_META[name]
  if (exact) {
    return {
      group: exact.group,
      title: exact.title,
      subtitle: name,
    }
  }
  return {
    group: 'R' as const,
    title: titleCaseArtifactName(name),
    subtitle: name,
  }
}

export function buildArtifactReferenceGroups(artifacts: ArtifactPreview[]) {
  const grouped = new Map<string, ArtifactPreview[]>()
  for (const artifact of artifacts) {
    if (!artifact.exists) continue
    const { group } = getArtifactDisplayMeta(artifact.name)
    const bucket = grouped.get(group) ?? []
    bucket.push(artifact)
    grouped.set(group, bucket)
  }
  return ARTIFACT_REFERENCE_GROUPS
    .map((section) => ({
      ...section,
      artifacts: (grouped.get(section.key) ?? []).sort((left, right) => left.name.localeCompare(right.name)),
    }))
    .filter((section) => section.artifacts.length > 0)
}
