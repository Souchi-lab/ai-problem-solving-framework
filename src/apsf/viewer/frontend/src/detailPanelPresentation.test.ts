import test from 'node:test'
import assert from 'node:assert/strict'

import {
  judgeAdvisoryEyebrow,
  judgeAdvisoryFooter,
  shouldShowJudgeAdvisoryFullDetail,
  shouldShowReturnTargetPreview,
} from './detailPanelPresentation.ts'

test('judge advisory is demoted when review summary is present', () => {
  assert.equal(judgeAdvisoryEyebrow(true), 'Decision Detail')
  assert.equal(shouldShowJudgeAdvisoryFullDetail(true), false)
})

test('judge advisory keeps full metrics when no review summary is present', () => {
  assert.equal(judgeAdvisoryEyebrow(false), 'Judge Advisory')
  assert.equal(shouldShowJudgeAdvisoryFullDetail(false), true)
})

test('return target preview is hidden for human-owned blockers', () => {
  assert.equal(
    shouldShowReturnTargetPreview({ hasReviewSummary: true, hasSuggestedReturnPhase: true, humanOwnedBlocker: true }),
    false,
  )
  assert.equal(
    shouldShowReturnTargetPreview({ hasReviewSummary: true, hasSuggestedReturnPhase: true, humanOwnedBlocker: false }),
    true,
  )
})

test('judge advisory footer uses workflow-oriented wording when summary exists', () => {
  assert.match(judgeAdvisoryFooter(true), /workflow summary/i)
  assert.match(judgeAdvisoryFooter(false), /judge still decides/i)
})
