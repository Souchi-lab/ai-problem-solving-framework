import type { RunDetail, AssignmentSummary, SpecialistVisibility } from '../../types'
import { AssignmentModeBadge } from '../badges'

interface AssignmentCardProps {
  activeAssignment: AssignmentSummary | null
  activeSpecialist: SpecialistVisibility | null
  selectedTaxonomy: string | null
  targetRun: string | null
  detail: RunDetail
  isActiveRunBusy: boolean
  openSpecialistSelectionForPhase: (phase: string) => Promise<void>
}

export function AssignmentCard({
  activeAssignment,
  activeSpecialist,
  selectedTaxonomy,
  targetRun,
  detail,
  isActiveRunBusy,
  openSpecialistSelectionForPhase,
}: AssignmentCardProps) {
  return (
    <div className="rounded border border-zinc-800 bg-zinc-900/40 p-4">
      <div className="mb-2 flex items-center justify-between gap-2">
        <div>
          <div className="text-[11px] font-bold uppercase tracking-[0.2em] text-zinc-400">Assignment</div>
          <div className="mt-1 text-[10px] text-zinc-500">Phase, provider, specialist in one pass.</div>
        </div>
        {activeAssignment && <AssignmentModeBadge mode={activeAssignment.execution.mode} />}
      </div>
      {activeAssignment && activeSpecialist ? (
        <div className="space-y-2 text-xs">
          <div className="rounded border border-zinc-800 bg-black/20 p-2">
            <div className="text-[10px] uppercase tracking-wide text-zinc-500">Agent</div>
            <div className="mt-0.5 font-semibold text-zinc-100">{activeAssignment.role || 'unset'}</div>
            <div className="mt-1 text-zinc-400">{activeAssignment.execution.execution_type || 'unset'}</div>
          </div>
          <div className="rounded border border-zinc-800 bg-black/20 p-2">
            <div className="text-[10px] uppercase tracking-wide text-zinc-500">Provider / Model</div>
            <div className="mt-0.5 text-zinc-200">{activeAssignment.model.provider || 'unset'}</div>
            <div className="font-mono text-[10px] text-zinc-400">{activeAssignment.model.model || 'unset'}</div>
          </div>
          <div className={`rounded border bg-black/20 p-2 ${activeSpecialist.has_gap ? 'border-red-500/30' : 'border-zinc-800'}`}>
            <div className="text-[10px] uppercase tracking-wide text-zinc-500">Specialist</div>
            <div className="mt-0.5 font-semibold text-zinc-100">{activeSpecialist.specialist_code || '(generic)'}</div>
            <div className={activeSpecialist.has_gap ? 'text-red-300' : 'text-zinc-400'}>
              {activeSpecialist.has_gap ? 'Gap detected' : 'No gap'}
            </div>
          </div>
          {selectedTaxonomy && targetRun && (
            <div className="space-y-2 rounded border border-amber-500/20 bg-amber-500/5 p-2">
              <div className="text-[10px] uppercase tracking-wide text-zinc-500">Change Assignment</div>
              <div className="flex gap-1.5">
                {(['Planner', 'Builder', 'Critic'] as const).map((role) => {
                  const phase = role === 'Planner' ? 'PLAN_NEEDED' : role === 'Builder' ? 'BUILD_NEEDED' : 'REVIEW_NEEDED'
                  return (
                    <button
                      key={role}
                      type="button"
                      onClick={() => void openSpecialistSelectionForPhase(phase)}
                      disabled={isActiveRunBusy}
                      className="flex-1 rounded border border-amber-500/40 bg-amber-500/10 px-2 py-1.5 text-[11px] font-semibold text-amber-100 hover:bg-amber-500/20 disabled:border-zinc-800 disabled:bg-zinc-900 disabled:text-zinc-500"
                    >
                      {role}
                    </button>
                  )
                })}
              </div>
              {detail && targetRun !== detail.name && (
                <div className="rounded border border-indigo-500/30 bg-indigo-500/10 px-3 py-2 text-[10px] text-indigo-100">
                  Targeting child run: <span className="font-mono">{targetRun}</span>
                </div>
              )}
              {isActiveRunBusy && (
                <div className="rounded border border-yellow-500/20 bg-yellow-500/5 px-3 py-2 text-[10px] text-yellow-100">
                  Specialist changes are blocked while this run is executing.
                </div>
              )}
            </div>
          )}
        </div>
      ) : (
        <div className="text-xs text-zinc-500">Assignment summary unavailable.</div>
      )}
    </div>
  )
}
