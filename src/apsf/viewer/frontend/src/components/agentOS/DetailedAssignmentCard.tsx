import type { RunDetail, SpecialistCandidatesData } from '../../types'
import { PhaseBadge, AssignmentModeBadge } from '../badges'

interface DetailedAssignmentCardProps {
  targetDetail: RunDetail | null
  detail: RunDetail
  specialistCandidates: SpecialistCandidatesData | null
  selectedTaxonomy: string | null
  targetRun: string | null
  openSpecialistSelectionModal: (initialCode?: string) => Promise<void>
}

export function DetailedAssignmentCard({
  targetDetail,
  detail,
  specialistCandidates,
  selectedTaxonomy,
  targetRun,
  openSpecialistSelectionModal,
}: DetailedAssignmentCardProps) {
  const assignmentDetail = targetDetail ?? detail
  if (!assignmentDetail) return null
  const assignment = assignmentDetail.assignment_summary
  const specialist = assignmentDetail.specialist_visibility
  return (
    <div className="rounded border border-emerald-500/20 bg-emerald-500/5 p-4">
      <div className="mb-3 flex items-center justify-between gap-3">
        <div>
          <div className="text-[11px] font-bold uppercase tracking-[0.2em] text-emerald-300">Assignment</div>
          <div className="mt-1 text-[10px] text-zinc-500">Current phase selection for agent, provider/model, and specialist.</div>
        </div>
        <PhaseBadge phase={assignmentDetail.phase} />
      </div>
      <div className="grid gap-3 lg:grid-cols-3">
        <div className="rounded border border-zinc-800 bg-black/20 p-3 text-xs">
          <div className="mb-2 flex items-center justify-between gap-2">
            <div className="text-[10px] font-bold uppercase tracking-[0.2em] text-zinc-500">Agent</div>
            <AssignmentModeBadge mode={assignment.execution.mode} />
          </div>
          <div className="text-[11px] text-zinc-500 uppercase tracking-wide">Role</div>
          <div className="mt-0.5 font-semibold text-zinc-100">{assignment.role || '—'}</div>
          <div className="mt-2 text-[11px] text-zinc-500 uppercase tracking-wide">Execution</div>
          <div className="mt-0.5 text-zinc-200">{assignment.execution.execution_type}</div>
          <div className="mt-2 text-[11px] text-zinc-500 uppercase tracking-wide">Target</div>
          <div className="mt-0.5 font-mono text-[11px] text-zinc-200">{assignment.execution.target || '—'}</div>
          {assignment.execution.workspace && (
            <>
              <div className="mt-2 text-[11px] text-zinc-500 uppercase tracking-wide">Workspace</div>
              <div className="mt-0.5 font-mono text-[11px] text-zinc-400">{assignment.execution.workspace}</div>
            </>
          )}
          <div className="mt-2 text-[10px] text-zinc-500">{assignment.execution.reason}</div>
        </div>

        <div className="rounded border border-zinc-800 bg-black/20 p-3 text-xs">
          <div className="mb-2 flex items-center justify-between gap-2">
            <div className="text-[10px] font-bold uppercase tracking-[0.2em] text-zinc-500">Provider</div>
            <AssignmentModeBadge mode={assignment.model.mode} />
          </div>
          <div className="text-[11px] text-zinc-500 uppercase tracking-wide">Provider</div>
          <div className="mt-0.5 font-semibold text-zinc-100">{assignment.model.provider || '—'}</div>
          <div className="mt-2 text-[11px] text-zinc-500 uppercase tracking-wide">Model</div>
          <div className="mt-0.5 font-mono text-[11px] text-zinc-200">{assignment.model.model || '—'}</div>
          <div className="mt-2 text-[10px] text-zinc-500">{assignment.model.reason}</div>
        </div>

        <div className={`rounded border bg-black/20 p-3 text-xs ${specialist.has_gap ? 'border-red-500/30' : 'border-zinc-800'}`}>
          <div className="mb-2 flex items-center justify-between gap-2">
            <div className="text-[10px] font-bold uppercase tracking-[0.2em] text-zinc-500">Specialist</div>
            <AssignmentModeBadge mode={specialist.mode} />
          </div>
          <div className="text-[11px] text-zinc-500 uppercase tracking-wide">Code</div>
          <div className="mt-0.5 font-semibold text-zinc-100">{specialist.specialist_code || '(generic)'}</div>
          <div className="mt-2 text-[11px] text-zinc-500 uppercase tracking-wide">Gap</div>
          <div className={`mt-0.5 font-semibold ${specialist.has_gap ? 'text-red-300' : 'text-zinc-300'}`}>{specialist.has_gap ? 'Yes' : 'No'}</div>
          <div className="mt-2 text-[10px] text-zinc-500">{specialist.reason}</div>
          {specialistCandidates && selectedTaxonomy && targetRun && (
            <div className="mt-3 space-y-2">
              <button
                type="button"
                onClick={() => void openSpecialistSelectionModal(specialist.specialist_code || specialistCandidates.current_code || '')}
                className="w-full rounded border border-amber-500/40 bg-amber-500/10 px-3 py-2 text-[11px] font-semibold text-amber-100 hover:bg-amber-500/20"
              >
                Select Specialist
              </button>
              {detail && targetRun !== detail.name && (
                <div className="rounded border border-indigo-500/30 bg-indigo-500/10 px-3 py-2 text-[10px] text-indigo-100">
                  Targeting child run: <span className="font-mono">{targetRun}</span>
                </div>
              )}
              <div className="text-[10px] text-zinc-500">
                Inspect the current library, assign an existing specialist, use generic explicitly, or branch into new specialist authoring.
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
