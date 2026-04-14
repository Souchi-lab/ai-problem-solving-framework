export interface AdvisoryPresentationInput {
  hasReviewSummary: boolean
  hasSuggestedReturnPhase: boolean
  humanOwnedBlocker: boolean
}

export function judgeAdvisoryEyebrow(hasReviewSummary: boolean) {
  return hasReviewSummary ? 'Decision Detail' : 'Judge Advisory'
}

export function shouldShowJudgeAdvisoryFullDetail(hasReviewSummary: boolean) {
  return !hasReviewSummary
}

export function shouldShowReturnTargetPreview(input: AdvisoryPresentationInput) {
  return input.hasSuggestedReturnPhase && !input.humanOwnedBlocker
}

export function judgeAdvisoryFooter(hasReviewSummary: boolean) {
  return hasReviewSummary
    ? 'Decision detail only. Use this after the workflow summary to confirm the specific reroute or acceptance context.'
    : 'Advisory only. Judge still decides, records the decision in improve.md, reflects the findings, and then returns the run when needed.'
}
