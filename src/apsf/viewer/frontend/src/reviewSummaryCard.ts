export interface ReviewSummary {
  available: boolean
  summary_status?: 'blocking' | 'revise' | 'adopt' | 'unknown' | null
  critical_count: number
  major_count: number
  minor_count: number
  review_verdict?: string | null
  counts_note?: string | null
  next_actions: string[]
  source_artifact?: string | null
}

export function reviewSummaryCardTone(status?: ReviewSummary['summary_status']) {
  switch (status) {
    case 'blocking':
      return {
        shell: 'border-amber-500/30 bg-amber-500/10',
        eyebrow: 'text-amber-200',
        badge: 'border-amber-400/30 bg-amber-500/10 text-amber-100',
      }
    case 'revise':
      return {
        shell: 'border-rose-500/25 bg-rose-500/10',
        eyebrow: 'text-rose-200',
        badge: 'border-rose-400/30 bg-rose-500/10 text-rose-100',
      }
    case 'adopt':
      return {
        shell: 'border-emerald-500/25 bg-emerald-500/10',
        eyebrow: 'text-emerald-200',
        badge: 'border-emerald-400/30 bg-emerald-500/10 text-emerald-100',
      }
    default:
      return {
        shell: 'border-sky-500/25 bg-sky-500/10',
        eyebrow: 'text-sky-200',
        badge: 'border-sky-400/30 bg-sky-500/10 text-sky-100',
      }
  }
}

export function reviewSummaryStatusLabel(status?: ReviewSummary['summary_status']) {
  switch (status) {
    case 'blocking':
      return 'Blocking'
    case 'revise':
      return 'Revise'
    case 'adopt':
      return 'Adopt'
    case 'unknown':
      return 'Unknown'
    default:
      return 'Summary'
  }
}

export function reviewSummaryHeadline(summary: ReviewSummary) {
  const verdict = summary.review_verdict?.trim()
  if (verdict) return verdict
  return reviewSummaryStatusLabel(summary.summary_status)
}

export function shouldRenderReviewSummaryCard(summary?: ReviewSummary | null) {
  return Boolean(summary)
}
