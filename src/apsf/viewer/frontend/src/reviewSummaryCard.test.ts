import test from 'node:test'
import assert from 'node:assert/strict'

import {
  reviewSummaryCardTone,
  reviewSummaryHeadline,
  reviewSummaryStatusLabel,
  shouldRenderReviewSummaryCard,
  type ReviewSummary,
} from './reviewSummaryCard.ts'

function makeSummary(overrides: Partial<ReviewSummary> = {}): ReviewSummary {
  return {
    available: true,
    summary_status: 'unknown',
    critical_count: 0,
    major_count: 0,
    minor_count: 0,
    review_verdict: null,
    counts_note: null,
    next_actions: [],
    source_artifact: 'review.md',
    ...overrides,
  }
}

test('shouldRenderReviewSummaryCard hides null summaries', () => {
  assert.equal(shouldRenderReviewSummaryCard(null), false)
  assert.equal(shouldRenderReviewSummaryCard(undefined), false)
  assert.equal(shouldRenderReviewSummaryCard(makeSummary()), true)
})

test('reviewSummaryStatusLabel returns readable labels for all supported states', () => {
  assert.equal(reviewSummaryStatusLabel('blocking'), 'Blocking')
  assert.equal(reviewSummaryStatusLabel('revise'), 'Revise')
  assert.equal(reviewSummaryStatusLabel('adopt'), 'Adopt')
  assert.equal(reviewSummaryStatusLabel('unknown'), 'Unknown')
})

test('reviewSummaryCardTone maps statuses to distinct shells', () => {
  assert.match(reviewSummaryCardTone('blocking').shell, /amber/)
  assert.match(reviewSummaryCardTone('revise').shell, /rose/)
  assert.match(reviewSummaryCardTone('adopt').shell, /emerald/)
  assert.match(reviewSummaryCardTone('unknown').shell, /sky/)
})

test('reviewSummaryHeadline prefers verdict over duplicated status label', () => {
  assert.equal(reviewSummaryHeadline(makeSummary({ summary_status: 'revise', review_verdict: 'Conditional Pass' })), 'Conditional Pass')
  assert.equal(reviewSummaryHeadline(makeSummary({ summary_status: 'revise', review_verdict: null })), 'Revise')
})
