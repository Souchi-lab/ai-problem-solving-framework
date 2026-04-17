import type { RunDetail, RunHistory, OperatorAction } from '../../types'
import {
  PhaseBadge,
  ReworkBadge,
  PriorityBadge,
  SatisfiabilityWarning,
} from '../badges'
import { parseSatisfiabilityReason } from '../../utils/formatting'

const IMPROVE_DECISION_ACTION_IDS = ['accept-improve', 'phase-primary', 'rerun-plan', 'rerun-build', 'rerun-review']

const REVIEW_FILES = ['plan_review.md', 'build_review.md', 'review_review.md', 'improve_review.md']

interface DetailTabProps {
  detail: RunDetail
  targetDetail: RunDetail | null
  history: RunHistory | null
  historyRun: string | null
  activeTargetName: string
  activeDetailPhase: string | null
  recommendedActionId: string | null
  selectedTaxonomy: string | null
  renderOperatorAction: (
    action: OperatorAction,
    mode: 'manual' | 'executable',
    taxonomy: string,
    runName: string,
  ) => React.ReactNode
}

export function DetailTab({
  detail,
  targetDetail,
  history,
  historyRun,
  activeTargetName,
  activeDetailPhase,
  recommendedActionId,
  selectedTaxonomy,
  renderOperatorAction,
}: DetailTabProps) {
  const childRuns = detail?.children ?? []
  const targetReworkCount = REVIEW_FILES.filter((n) => (targetDetail?.artifacts ?? detail?.artifacts ?? []).some((a) => a.name === n && a.exists)).length
  const detailActions = targetDetail?.operator_actions ?? []
  const sortedDetailActions = [...detailActions].sort((a, b) => {
    if (a.id === recommendedActionId) return -1
    if (b.id === recommendedActionId) return 1
    if (a.primary && !b.primary) return -1
    if (!a.primary && b.primary) return 1
    return 0
  })
  const executableActions = sortedDetailActions.filter((action) => action.execution_type !== 'human')
  const humanActions = sortedDetailActions.filter((action) => action.execution_type === 'human')
  const improveDecisionActions = activeDetailPhase === 'IMPROVE_NEEDED'
    ? IMPROVE_DECISION_ACTION_IDS
        .map((id) => sortedDetailActions.find((action) => action.id === id) ?? null)
        .filter((action): action is OperatorAction => action !== null)
    : []
  const improveDecisionActionIdSet = new Set(improveDecisionActions.map((action) => action.id))
  const regularExecutableActions = executableActions.filter((action) => !improveDecisionActionIdSet.has(action.id))
  const regularHumanActions = humanActions.filter((action) => !improveDecisionActionIdSet.has(action.id))
  return (
    <div className="space-y-4">
      <div className="grid gap-4 xl:grid-cols-2">
        <div className="rounded border border-zinc-800 bg-zinc-900/40 p-4">
          <div className="mb-2 text-[11px] font-bold uppercase tracking-[0.2em] text-zinc-500">Current Target</div>
          <div className="flex flex-col items-start gap-2">
            <div className="flex flex-wrap items-center gap-2">
              <PhaseBadge phase={targetDetail?.phase ?? detail.phase} />
              <PriorityBadge priority={targetDetail?.priority ?? detail.priority} />
            </div>
            {targetReworkCount > 0 && <ReworkBadge count={targetReworkCount} />}
          </div>
          <div className="mt-3 text-sm font-semibold text-zinc-100">{targetDetail?.name ?? detail.name}</div>
          <div className="mt-1 text-xs text-zinc-400">Next: {targetDetail?.next_role ?? detail.next_role}</div>
          {(() => {
            const parsed = parseSatisfiabilityReason(targetDetail?.decision_reason ?? detail.decision_reason)
            return parsed.primary ? (
              <p className="mt-3 text-sm text-zinc-400">{parsed.primary}</p>
            ) : null
          })()}
          <SatisfiabilityWarning reason={targetDetail?.decision_reason ?? detail.decision_reason} />
          {(targetDetail?.human_blocker?.active ?? detail.human_blocker?.active ?? false) && (
            <div className="mt-3 rounded border border-amber-500/30 bg-amber-500/10 p-3">
              <div className="flex flex-wrap items-center gap-2">
                <span className="rounded border border-amber-400/40 bg-amber-500/15 px-2 py-0.5 text-[10px] font-bold uppercase tracking-[0.16em] text-amber-100">
                  Human Blocker
                </span>
                {((targetDetail?.human_blocker?.source ?? detail.human_blocker?.source)) && (
                  <span className="text-[10px] text-amber-200/80">
                    source: {targetDetail?.human_blocker?.source ?? detail.human_blocker?.source}
                  </span>
                )}
              </div>
              <div className="mt-2 text-xs text-zinc-200">
                {targetDetail?.human_blocker?.summary ?? detail.human_blocker?.summary}
              </div>
              {((targetDetail?.human_blocker?.actions ?? detail.human_blocker?.actions ?? []).length > 0) && (
                <div className="mt-2 space-y-1">
                  {(targetDetail?.human_blocker?.actions ?? detail.human_blocker?.actions ?? []).slice(0, 3).map((action, index) => (
                    <div key={`${action}-${index}`} className="text-[11px] text-zinc-300">
                      {action}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>

        <div className="rounded border border-zinc-800 bg-zinc-900/40 p-4">
          <div className="mb-2 text-[11px] font-bold uppercase tracking-[0.2em] text-zinc-500">Topology Summary</div>
          <div className="flex flex-wrap items-center gap-2">
            <span className="rounded border border-emerald-500/30 bg-emerald-500/10 px-2 py-0.5 text-[10px] font-bold text-emerald-300">
              parent
            </span>
            <span className="rounded border border-indigo-500/30 bg-indigo-500/10 px-2 py-0.5 text-[10px] font-bold text-indigo-300">
              {childRuns.length} child run{childRuns.length === 1 ? '' : 's'}
            </span>
            {activeTargetName !== detail.name && (
              <span className="rounded border border-indigo-500/30 bg-indigo-500/10 px-2 py-0.5 text-[10px] font-bold text-indigo-300">
                viewing child
              </span>
            )}
          </div>
          <div className="mt-3 text-xs text-zinc-400">
            Parent and child runs are now selectable from the lineage list above. The active run stays highlighted there with its phase and next role.
          </div>
          {childRuns.length === 0 && (
            <div className="mt-3 text-xs text-zinc-500">No child runs for this target.</div>
          )}
        </div>
      </div>

      {history && (history.latest_execution || history.latest_rerun_comment) && (
        <div className="rounded border border-emerald-500/20 bg-emerald-500/5 p-4">
          <div className="mb-3 text-[11px] font-bold uppercase tracking-[0.2em] text-emerald-300">Latest Persisted Activity</div>
          <div className="mb-3 text-[11px] text-zinc-400">
            Showing history for <span className="font-mono text-zinc-200">{historyRun ?? activeTargetName ?? detail.name}</span>
          </div>
          <div className="grid gap-3 xl:grid-cols-2">
            {history.latest_execution ? (
              <div className="rounded border border-zinc-800 bg-black/20 p-3">
                <div className="mb-1 text-[10px] font-bold uppercase tracking-[0.2em] text-zinc-500">Execution</div>
                <div className="flex items-center gap-2">
                  <span className="rounded bg-zinc-900 px-2 py-0.5 text-[10px] font-bold text-zinc-300">{history.latest_execution.action_id}</span>
                  <PhaseBadge phase={history.latest_execution.result_status} />
                </div>
                <div className="mt-2 text-xs text-zinc-400">{history.latest_execution.triggered_at}</div>
                {(history.latest_execution.result_status === 'PARTIAL' || history.latest_execution.result_status === 'FAILED') && history.latest_execution.stdout_summary && (
                  <div className="mt-2 rounded border border-amber-500/20 bg-black/40 p-2">
                    <div className="mb-1 text-[9px] font-bold uppercase tracking-[0.15em] text-amber-400/70">Last Output</div>
                    <pre className="whitespace-pre-wrap font-mono text-[10px] leading-relaxed text-zinc-300 line-clamp-4">{history.latest_execution.stdout_summary.split('\n').slice(-4).join('\n')}</pre>
                  </div>
                )}
              </div>
            ) : (
              <div className="rounded border border-zinc-800 bg-black/20 p-3 text-xs text-zinc-500">No execution history yet.</div>
            )}

            {history.latest_rerun_comment ? (
              <div className="rounded border border-zinc-800 bg-black/20 p-3">
                <div className="mb-1 text-[10px] font-bold uppercase tracking-[0.2em] text-zinc-500">Rerun Comment</div>
                <div className="text-xs text-zinc-400">{history.latest_rerun_comment.comment_artifact}</div>
                <div className="mt-2 line-clamp-3 whitespace-pre-wrap text-xs text-zinc-300">{history.latest_rerun_comment.comment_body}</div>
              </div>
            ) : (
              <div className="rounded border border-zinc-800 bg-black/20 p-3 text-xs text-zinc-500">No rerun comment history yet.</div>
            )}
          </div>
        </div>
      )}

      {improveDecisionActions.length > 0 && selectedTaxonomy && targetDetail && (
        <div className="space-y-3">
          <div className="text-[11px] font-bold uppercase tracking-[0.2em] text-zinc-500">Judge Decision Paths</div>
          <div className="rounded border border-fuchsia-500/20 bg-fuchsia-500/5 px-3 py-2 text-[11px] text-zinc-300">
            Accept, return to Plan, and return to Build stay visible here even when Judge Advisory recommends only one path.
          </div>
          {improveDecisionActions.map((action) =>
            renderOperatorAction(
              action,
              action.execution_type === 'human' ? 'manual' : 'executable',
              selectedTaxonomy,
              targetDetail.name,
            ),
          )}
        </div>
      )}

      {regularExecutableActions.length > 0 && selectedTaxonomy && targetDetail && (
        <div className="space-y-3">
          <div className="text-[11px] font-bold uppercase tracking-[0.2em] text-zinc-500">
            {recommendedActionId ? 'Recommended And More Actions' : 'More Actions'}
          </div>
          {recommendedActionId && (
            <div className="rounded border border-emerald-500/20 bg-emerald-500/5 px-3 py-2 text-[11px] text-zinc-300">
              Judge Advisory recommends the first action in this list.
            </div>
          )}
          {regularExecutableActions.map((action) => renderOperatorAction(action, 'executable', selectedTaxonomy, targetDetail.name))}
        </div>
      )}

      {regularHumanActions.length > 0 && selectedTaxonomy && targetDetail && (
        <div className="space-y-3">
          <div className="pt-2 text-[11px] font-bold uppercase tracking-[0.2em] text-zinc-500">Run Manual Steps</div>
          {regularHumanActions.map((action) => renderOperatorAction(action, 'manual', selectedTaxonomy, targetDetail.name))}
        </div>
      )}
    </div>
  )
}
