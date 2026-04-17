import type { MatrixRow, OperatorAction, CodexBridgeResult, ActionExecutionRecord } from '../../types'
import { PhaseBadge, PriorityBadge, CodexStatusBadge } from '../badges'

const CODEX_PRESET_RULES = {
  'finish-after-build': {
    label: 'Finish After Build',
    description: 'Ask Codex to identify the minimum remaining work before review/close.',
    allowedPhases: new Set(['BUILD_NEEDED', 'REVIEW_NEEDED']),
  },
  'review-and-close': {
    label: 'Review And Close',
    description: 'Ask Codex to assess closure quality and close-out gaps.',
    allowedPhases: new Set(['REVIEW_NEEDED', 'IMPROVE_NEEDED', 'TRANSCRIPT_RECOMMENDED']),
  },
} as const

const ACTIVE_PHASES = new Set(['PLAN_NEEDED', 'BUILD_NEEDED', 'REVIEW_NEEDED', 'IMPROVE_NEEDED', 'RESULT_NEEDED'])

function getCodexPresetsForPhase(phase: string) {
  return (Object.entries(CODEX_PRESET_RULES) as Array<[CodexBridgeResult['preset_id'], (typeof CODEX_PRESET_RULES)[keyof typeof CODEX_PRESET_RULES]]>)
    .filter(([, rule]) => rule.allowedPhases.has(phase))
}

interface ManagementTabProps {
  operatorFilter: 'active' | 'recent' | 'all'
  setOperatorFilter: (value: 'active' | 'recent' | 'all') => void
  matrixRows: MatrixRow[]
  recentExecutions: ActionExecutionRecord[]
  searchTerm: string
  targetDetail: { name: string } | null
  detail: { name: string }
  selectedRun: string | null
  fetchDetail: (taxonomy: string, runName: string) => Promise<void>
  executeMatrixAction: (row: MatrixRow, action: OperatorAction) => Promise<void>
  isRunExecuting: (taxonomy: string, runName: string) => boolean
  executingActionForRun: (taxonomy: string, runName: string) => string | null
  codexLoadingPreset: CodexBridgeResult['preset_id'] | null
  codexTargetKey: string | null
  codexError: string | null
  codexResult: CodexBridgeResult | null
  invokeCodexPreset: (presetId: CodexBridgeResult['preset_id'], taxonomy: string, runName: string) => Promise<void>
}

export function ManagementTab({
  operatorFilter,
  setOperatorFilter,
  matrixRows,
  recentExecutions,
  searchTerm,
  targetDetail,
  detail,
  selectedRun,
  fetchDetail,
  executeMatrixAction,
  isRunExecuting,
  executingActionForRun,
  codexLoadingPreset,
  codexTargetKey,
  codexError,
  codexResult,
  invokeCodexPreset,
}: ManagementTabProps) {
  const recentRunNames = new Set(recentExecutions.map((job) => job.run_name))
  const operatorRows = matrixRows
    .filter((row) => row.name.toLowerCase().includes(searchTerm.toLowerCase()))
    .filter((row) => operatorFilter === 'all' ? true : operatorFilter === 'recent' ? recentRunNames.has(row.name) : ACTIVE_PHASES.has(row.phase))
    .slice(0, 10)
  return (
    <div className="space-y-4">
      <div className="rounded border border-zinc-800 bg-zinc-900/40 p-4">
        <div className="mb-3 flex items-center justify-between gap-3">
          <div>
            <div className="text-[11px] font-bold uppercase tracking-[0.2em] text-zinc-500">Execution Matrix</div>
            <div className="mt-1 text-xs text-zinc-400">Operator shortcuts for top-level runs.</div>
          </div>
          <div className="flex items-center gap-2">
            {(['active', 'recent', 'all'] as const).map((filter) => (
              <button
                key={filter}
                onClick={() => setOperatorFilter(filter)}
                className={`rounded border px-2.5 py-1 text-[10px] font-bold uppercase ${operatorFilter === filter ? 'border-indigo-400 bg-indigo-500/20 text-indigo-100' : 'border-zinc-700 bg-zinc-900 text-zinc-400'}`}
              >
                {filter}
              </button>
            ))}
          </div>
        </div>
        {targetDetail && targetDetail.name !== detail.name && (
          <div className="mb-3 rounded border border-amber-500/30 bg-amber-500/10 px-3 py-2 text-xs text-amber-100">
            Execution Matrix runs parent-level commands. Current child target: <span className="font-mono">{targetDetail.name}</span>. Use Run Detail actions for child runs.
          </div>
        )}
        <div className="space-y-3">
          {operatorRows.map((row) => (
            <div key={row.name} className="rounded border border-zinc-800 bg-black/20 p-3">
              <div className="mb-2 flex items-center justify-between gap-2">
                <div className="min-w-0">
                  <div className="truncate text-[11px] text-zinc-500">{row.taxonomy}</div>
                  <div className="truncate text-sm font-semibold text-zinc-100" title={row.name}>{row.name}</div>
                </div>
                <div className="flex items-center gap-1">
                  <PhaseBadge phase={row.phase} />
                  <PriorityBadge priority={row.priority} />
                  {selectedRun === row.name && (
                    <span className="rounded border border-indigo-500/30 bg-indigo-500/10 px-1.5 py-0.5 text-[10px] font-bold text-indigo-200">
                      SELECTED PARENT
                    </span>
                  )}
                </div>
              </div>
              <div className="mb-3 flex items-center justify-between gap-3">
                <div className="text-xs text-zinc-500">Open the parent run in Agent OS, or operate directly from this top-level card.</div>
                <button
                  onClick={() => void fetchDetail(row.taxonomy, row.name)}
                  className="rounded border border-zinc-700 bg-zinc-950 px-2.5 py-1 text-[10px] font-bold text-zinc-200"
                >
                  Open Parent
                </button>
              </div>
              <div className="grid grid-cols-4 gap-2">
                {[
                  { label: 'Plan', action: row.plan_action },
                  { label: 'Build', action: row.build_action },
                  { label: 'Review', action: row.review_action },
                  { label: 'Rerun', action: row.rerun_action },
                ].map(({ label, action }) => {
                  const typedAction = action as OperatorAction | null | undefined
                  const isRunning = executingActionForRun(row.taxonomy, row.name) === typedAction?.id
                  return (
                    <button
                      key={`${row.name}-${label}`}
                      onClick={() => typedAction && void executeMatrixAction(row, typedAction)}
                      disabled={!typedAction || !typedAction.enabled || isRunExecuting(row.taxonomy, row.name)}
                      className={`rounded border px-2 py-1.5 text-[11px] font-bold ${
                        isRunning
                          ? 'animate-pulse border-red-400 bg-red-500/25 text-red-50'
                          : typedAction?.primary
                            ? 'border-indigo-500/40 bg-indigo-500/15 text-indigo-200 disabled:border-zinc-800 disabled:bg-zinc-900 disabled:text-zinc-600'
                            : 'border-zinc-700 bg-zinc-950 text-zinc-300 disabled:border-zinc-800 disabled:bg-zinc-900 disabled:text-zinc-600'
                      }`}
                    >
                      {isRunning ? 'Running...' : label}
                    </button>
                  )
                })}
              </div>

              <div className="mt-3 rounded border border-cyan-500/20 bg-cyan-500/5 p-3">
                <div className="mb-2 flex items-center justify-between gap-3">
                  <div className="text-[10px] font-bold uppercase tracking-[0.2em] text-cyan-300">Codex Advisory</div>
                  <div className="text-[10px] text-zinc-500">per run</div>
                </div>

                {getCodexPresetsForPhase(row.phase).length > 0 ? (
                  <div className="flex flex-wrap gap-2">
                    {getCodexPresetsForPhase(row.phase).map(([presetId, preset]) => (
                      <button
                        key={`${row.name}-${presetId}`}
                        onClick={() => void invokeCodexPreset(presetId, row.taxonomy, row.name)}
                        disabled={codexLoadingPreset !== null || isRunExecuting(row.taxonomy, row.name)}
                        className="rounded border border-cyan-500/30 bg-zinc-950/80 px-3 py-1.5 text-left text-[11px] font-bold text-cyan-200 disabled:border-zinc-800 disabled:bg-zinc-900 disabled:text-zinc-500"
                        title={preset.description}
                      >
                        {codexLoadingPreset === presetId && codexTargetKey === `${row.taxonomy}:${row.name}` ? 'Running...' : preset.label}
                      </button>
                    ))}
                  </div>
                ) : (
                  <div className="text-xs text-zinc-500">No advisory preset for this phase.</div>
                )}

                {codexTargetKey === `${row.taxonomy}:${row.name}` && codexError && (
                  <div className="mt-3 rounded border border-red-500/30 bg-red-500/10 p-3 text-xs text-red-200">
                    {codexError}
                  </div>
                )}

                {codexTargetKey === `${row.taxonomy}:${row.name}` && codexResult && (
                  <div className="mt-3 rounded border border-zinc-800 bg-zinc-950/70 p-3">
                    <div className="mb-2 flex items-center justify-between gap-3">
                      <div className="text-xs font-semibold text-zinc-200">{CODEX_PRESET_RULES[codexResult.preset_id].label}</div>
                      <CodexStatusBadge status={codexResult.status} />
                    </div>
                    <div className="text-sm text-zinc-200">{codexResult.summary}</div>
                    {codexResult.next_steps.length > 0 && (
                      <ul className="mt-3 list-disc space-y-1 pl-5 text-xs text-zinc-300">
                        {codexResult.next_steps.map((step, index) => (
                          <li key={`${row.name}-${codexResult.preset_id}-${index}`}>{step}</li>
                        ))}
                      </ul>
                    )}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

    </div>
  )
}
