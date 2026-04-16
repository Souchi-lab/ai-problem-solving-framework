import { useEffect, useState } from 'react'
import type { SpecialistCandidatesData, CreateSpecialistResult } from '../../types'

export function SpecialistSelectionModal({
  taxonomy,
  runName,
  candidatesData,
  initialCode,
  createResult,
  onClose,
  onConfirm,
  onCreateNew,
}: {
  taxonomy: string
  runName: string
  candidatesData: SpecialistCandidatesData
  initialCode?: string | null
  createResult?: CreateSpecialistResult | null
  onClose: () => void
  onConfirm: (code: string) => Promise<void>
  onCreateNew: (suggestedCode?: string) => void
}) {
  const [selectedCode, setSelectedCode] = useState(initialCode ?? candidatesData.current_code ?? '')
  const [confirming, setConfirming] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    setSelectedCode(initialCode ?? candidatesData.current_code ?? '')
  }, [initialCode, candidatesData.current_code])

  const selected =
    candidatesData.candidates.find((candidate) => candidate.code === selectedCode) ??
    candidatesData.candidates.find((candidate) => candidate.is_recommended) ??
    candidatesData.candidates[candidatesData.candidates.length - 1]
  const selectedIsGeneric = !selected?.code

  const handleConfirm = async () => {
    setConfirming(true)
    setError(null)
    try {
      await onConfirm(selected?.code ?? '')
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to assign specialist')
    } finally {
      setConfirming(false)
    }
  }

  return (
    <div className="fixed inset-0 z-[110] flex items-center justify-center bg-black/70 p-4 backdrop-blur-sm">
      <div className="flex max-h-[88vh] w-full max-w-6xl flex-col overflow-hidden rounded-2xl border border-zinc-800 bg-zinc-950 shadow-2xl shadow-black/60">
        <div className="flex items-start justify-between gap-4 border-b border-zinc-800 px-5 py-4">
          <div>
            <div className="text-lg font-bold text-zinc-100">
              {candidatesData.phase === 'IMPROVE_NEEDED' ? 'Select Specialist' : `Select ${candidatesData.role} Specialist`}
            </div>
            <div className="mt-1 text-sm text-zinc-400">
              {candidatesData.phase === 'PLAN_NEEDED' || candidatesData.phase === 'BUILD_NEEDED' || candidatesData.phase === 'REVIEW_NEEDED'
                ? `Inspect the ${candidatesData.role} library for ${candidatesData.phase}, then assign an existing specialist, use generic explicitly, or branch into specialist authoring.`
                : 'Inspect the current library, then assign an existing specialist, use generic explicitly, or branch into specialist authoring.'}
            </div>
            <div className="mt-2 font-mono text-[10px] uppercase tracking-[0.2em] text-zinc-500">
              {taxonomy} / {runName}
            </div>
          </div>
          <button onClick={onClose} className="rounded border border-zinc-700 bg-zinc-900 px-3 py-1.5 text-xs font-semibold text-zinc-300 hover:border-zinc-500 hover:text-white">
            Close
          </button>
        </div>

        {createResult && (
          <div className="border-b border-emerald-500/20 bg-emerald-500/10 px-5 py-3 text-sm text-emerald-100">
            <div>
              Specialist created successfully: <span className="font-mono">{createResult.specialist_code}</span> at{' '}
              <span className="font-mono text-emerald-200/80">{createResult.relative_path}</span>.
            </div>
            <div className="mt-1 text-emerald-200/90">
              Registry updated. Next step: assign this specialist to the current run if you want to use it now.
            </div>
          </div>
        )}

        <div className="grid min-h-0 flex-1 gap-0 lg:grid-cols-[minmax(18rem,24rem)_1fr]">
          <div className="overflow-y-auto border-b border-zinc-800 p-4 lg:border-b-0 lg:border-r">
            <div className="mb-3 text-[10px] font-bold uppercase tracking-[0.2em] text-zinc-500">Candidates</div>
            <div className="space-y-2">
              {candidatesData.candidates.map((candidate) => {
                const selectedState = selected?.code === candidate.code
                const isGeneric = !candidate.code
                return (
                  <button
                    key={`${candidate.code || 'generic'}-${candidate.name}`}
                    type="button"
                    onClick={() => setSelectedCode(candidate.code)}
                    className={`w-full rounded border p-3 text-left transition-colors ${
                      selectedState
                        ? 'border-cyan-400/40 bg-cyan-500/10 text-cyan-50'
                        : isGeneric
                          ? 'border-amber-500/25 bg-amber-500/5 text-amber-50 hover:border-amber-400/40 hover:bg-amber-500/10'
                          : 'border-zinc-800 bg-zinc-900/40 text-zinc-200 hover:border-zinc-700 hover:bg-zinc-900/70'
                    }`}
                  >
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-[11px] font-semibold">{candidate.code || 'GENERIC'}</span>
                      <span className="text-[11px] text-zinc-400">{isGeneric ? 'Use Generic For This Run' : candidate.name}</span>
                      {candidate.is_recommended && (
                        <span className="rounded border border-emerald-500/30 bg-emerald-500/10 px-1 py-0.5 text-[9px] font-bold uppercase tracking-wide text-emerald-300">
                          recommended
                        </span>
                      )}
                      {candidate.is_current && (
                        <span className="rounded border border-indigo-500/30 bg-indigo-500/10 px-1 py-0.5 text-[9px] font-bold uppercase tracking-wide text-indigo-300">
                          current
                        </span>
                      )}
                    </div>
                    <div className="mt-1 text-[10px] text-zinc-500">{candidate.use_when}</div>
                  </button>
                )
              })}
            </div>
          </div>

          <div className="min-h-0 overflow-y-auto p-5">
            {selected ? (
              <div className="space-y-4">
                <div className="rounded border border-zinc-800 bg-zinc-900/40 p-4">
                  <div className="flex items-center gap-2">
                    <div className="font-mono text-sm font-semibold text-zinc-100">{selected.code || 'GENERIC'}</div>
                    <div className="text-sm text-zinc-400">{selectedIsGeneric ? 'Use Generic For This Run' : selected.name}</div>
                  </div>
                  <div className="mt-2 grid gap-3 text-xs text-zinc-300 lg:grid-cols-2">
                    <div>
                      <div className="text-[10px] font-bold uppercase tracking-[0.2em] text-zinc-500">Path</div>
                      <div className="mt-1 font-mono text-zinc-300">{selected.path || '(generic fallback)'}</div>
                    </div>
                    <div>
                      <div className="text-[10px] font-bold uppercase tracking-[0.2em] text-zinc-500">Reason</div>
                      <div className="mt-1 text-zinc-300">{selected.reason}</div>
                    </div>
                  </div>
                </div>

                <div className="grid gap-3 lg:grid-cols-3">
                  <div className="rounded border border-zinc-800 bg-black/20 p-4">
                    <div className="text-[10px] font-bold uppercase tracking-[0.2em] text-zinc-500">Scope</div>
                    <div className="mt-2 text-sm text-zinc-200">{selected.scope || 'No scope summary available.'}</div>
                  </div>
                  <div className="rounded border border-zinc-800 bg-black/20 p-4">
                    <div className="text-[10px] font-bold uppercase tracking-[0.2em] text-zinc-500">Use When</div>
                    <div className="mt-2 text-sm text-zinc-200">{selected.use_when || 'No use-when summary available.'}</div>
                  </div>
                  <div className="rounded border border-zinc-800 bg-black/20 p-4">
                    <div className="text-[10px] font-bold uppercase tracking-[0.2em] text-zinc-500">Out Of Scope</div>
                    <div className="mt-2 text-sm text-zinc-200">{selected.out_of_scope || 'No out-of-scope summary available.'}</div>
                  </div>
                </div>

                <div className="rounded border border-zinc-800 bg-black/20 p-4">
                  <div className="text-[10px] font-bold uppercase tracking-[0.2em] text-zinc-500">Evaluation Criteria</div>
                  <div className="mt-2 text-sm text-zinc-200">{selected.evaluation_criteria || 'No evaluation summary available.'}</div>
                </div>

                {error && <div className="rounded border border-red-500/30 bg-red-500/10 px-3 py-2 text-sm text-red-200">{error}</div>}

                <div className="flex flex-wrap justify-between gap-3">
                  <button
                    type="button"
                    onClick={() => onCreateNew(selected.code || undefined)}
                    className="rounded border border-fuchsia-500/30 bg-fuchsia-500/15 px-4 py-2 text-sm font-semibold text-fuchsia-100 hover:bg-fuchsia-500/25"
                  >
                    Create New Specialist Library Asset
                  </button>
                  <div className="flex gap-3">
                    <button
                      type="button"
                      onClick={onClose}
                      className="rounded border border-zinc-700 bg-zinc-900 px-4 py-2 text-sm font-semibold text-zinc-300 hover:border-zinc-500 hover:text-white"
                    >
                      Cancel
                    </button>
                    <button
                      type="button"
                      disabled={confirming}
                      onClick={() => void handleConfirm()}
                      className="rounded border border-emerald-500/40 bg-emerald-500/15 px-4 py-2 text-sm font-semibold text-emerald-100 hover:bg-emerald-500/25 disabled:opacity-50"
                    >
                      {confirming ? 'Assigning...' : selectedIsGeneric ? 'Use Generic For This Run' : `Assign ${selected.code}`}
                    </button>
                  </div>
                </div>
              </div>
            ) : (
              <div className="flex h-full items-center justify-center text-sm text-zinc-500">Select a specialist candidate to inspect its details.</div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default SpecialistSelectionModal
