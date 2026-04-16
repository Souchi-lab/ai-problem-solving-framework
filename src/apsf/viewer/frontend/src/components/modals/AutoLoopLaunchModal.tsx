import { useState } from 'react'
import type { AssignmentSummary, SpecialistVisibility } from '../../types'

const BUILD_BACKEND_OPTIONS = [
  { label: 'Claude', script: 'apsf-claude-build.ps1' },
  { label: 'Codex', script: 'apsf-codex-build.ps1' },
] as const

export function AutoLoopLaunchModal({
  taxonomy,
  runName,
  phase,
  assignment,
  specialist,
  starting,
  onClose,
  onChangeAssignment,
  onStart,
}: {
  taxonomy: string
  runName: string
  phase: string
  assignment: AssignmentSummary | null
  specialist: SpecialistVisibility | null
  starting: boolean
  onClose: () => void
  onChangeAssignment: () => void
  onStart: (buildScript: string) => Promise<void>
}) {
  const [buildScript, setBuildScript] = useState<string>(BUILD_BACKEND_OPTIONS[0].script)

  return (
    <div className="fixed inset-0 z-[110] flex items-center justify-center bg-black/70 p-4 backdrop-blur-sm">
      <div className="w-full max-w-2xl rounded-2xl border border-zinc-800 bg-zinc-950 shadow-2xl shadow-black/60">
        <div className="flex items-start justify-between gap-4 border-b border-zinc-800 px-5 py-4">
          <div>
            <div className="text-lg font-bold text-zinc-100">Start Auto-Loop</div>
            <div className="mt-1 text-sm text-zinc-400">
              Confirm the current assignment before launching the loop. If the specialist or role is wrong, change it first.
            </div>
            <div className="mt-2 font-mono text-[10px] uppercase tracking-[0.2em] text-zinc-500">
              {taxonomy} / {runName}
            </div>
          </div>
          <button onClick={onClose} className="rounded border border-zinc-700 bg-zinc-900 px-3 py-1.5 text-xs font-semibold text-zinc-300 hover:border-zinc-500 hover:text-white">
            Close
          </button>
        </div>

        <div className="space-y-4 p-5">
          <div className="rounded border border-cyan-500/20 bg-cyan-500/5 p-3 text-xs text-cyan-100">
            Current phase: <span className="font-mono">{phase || 'unknown'}</span>
          </div>
          <div className="grid gap-3 md:grid-cols-3">
            <div className="rounded border border-zinc-800 bg-black/20 p-3 text-xs">
              <div className="text-[10px] uppercase tracking-wide text-zinc-500">Agent</div>
              <div className="mt-1 font-semibold text-zinc-100">{assignment?.role || 'unset'}</div>
            </div>
            <div className="rounded border border-zinc-800 bg-black/20 p-3 text-xs">
              <div className="text-[10px] uppercase tracking-wide text-zinc-500">Execution Type</div>
              <div className="mt-1 text-zinc-400">{assignment?.execution.execution_type || 'unset'}</div>
            </div>
            <div className="rounded border border-zinc-800 bg-black/20 p-3 text-xs">
              <div className="text-[10px] uppercase tracking-wide text-zinc-500">Provider / Model</div>
              <div className="mt-1 text-zinc-200">{assignment?.model.provider || 'unset'}</div>
              <div className="font-mono text-[10px] text-zinc-400">{assignment?.model.model || 'unset'}</div>
            </div>
            <div className={`rounded border bg-black/20 p-3 text-xs ${specialist?.has_gap ? 'border-red-500/30' : 'border-zinc-800'}`}>
              <div className="text-[10px] uppercase tracking-wide text-zinc-500">Specialist</div>
              <div className="mt-1 font-semibold text-zinc-100">{specialist?.specialist_code || '(generic)'}</div>
              <div className={specialist?.has_gap ? 'mt-1 text-red-300' : 'mt-1 text-zinc-400'}>
                {specialist?.has_gap ? 'Gap detected' : specialist?.mode || 'not_applicable'}
              </div>
            </div>
          </div>

          {/* Build Backend selector */}
          <div className="rounded border border-zinc-800 bg-black/20 p-3">
            <div className="mb-2 text-[10px] uppercase tracking-wide text-zinc-500">Build Backend</div>
            <div className="flex gap-2">
              {BUILD_BACKEND_OPTIONS.map((opt) => (
                <button
                  key={opt.script}
                  type="button"
                  onClick={() => setBuildScript(opt.script)}
                  className={`rounded border px-3 py-1.5 text-[11px] font-semibold transition-colors ${
                    buildScript === opt.script
                      ? 'border-cyan-500/50 bg-cyan-500/15 text-cyan-100'
                      : 'border-zinc-700 bg-zinc-900 text-zinc-400 hover:border-zinc-600 hover:text-zinc-200'
                  }`}
                >
                  {opt.label}
                </button>
              ))}
            </div>
            <div className="mt-1.5 font-mono text-[9px] text-zinc-600">{buildScript}</div>
          </div>
        </div>

        <div className="flex justify-end gap-3 border-t border-zinc-800 px-5 py-4">
          <button
            type="button"
            onClick={onChangeAssignment}
            disabled={starting}
            className="rounded border border-amber-500/40 bg-amber-500/10 px-4 py-2 text-sm font-semibold text-amber-100 hover:bg-amber-500/20 disabled:border-zinc-800 disabled:bg-zinc-900 disabled:text-zinc-500"
          >
            Change Assignment
          </button>
          <button
            type="button"
            onClick={() => void onStart(buildScript)}
            disabled={starting}
            className="rounded border border-cyan-500/30 bg-cyan-500/15 px-4 py-2 text-sm font-semibold text-cyan-50 hover:bg-cyan-500/20 disabled:border-zinc-800 disabled:bg-zinc-900 disabled:text-zinc-500"
          >
            {starting ? 'Starting...' : 'Start Auto-Loop'}
          </button>
        </div>
      </div>
    </div>
  )
}

export default AutoLoopLaunchModal
