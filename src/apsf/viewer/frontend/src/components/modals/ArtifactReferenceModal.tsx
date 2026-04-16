import { FileText } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import type { ArtifactPreview } from '../../types'
import { getArtifactDisplayMeta, buildArtifactReferenceGroups } from '../../utils/artifacts'

export function ArtifactReferenceModal({
  artifacts,
  selectedArtifact,
  artifactContent,
  runName,
  onClose,
  onSelect,
}: {
  artifacts: ArtifactPreview[]
  selectedArtifact: string | null
  artifactContent: string
  runName: string
  onClose: () => void
  onSelect: (name: string) => void
}) {
  const sections = buildArtifactReferenceGroups(artifacts)
  const selectedMeta = selectedArtifact ? getArtifactDisplayMeta(selectedArtifact) : null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4 backdrop-blur-sm" onClick={onClose}>
      <div className="flex h-[85vh] w-full max-w-6xl overflow-hidden rounded-2xl border border-zinc-800 bg-zinc-950 shadow-2xl shadow-black/60" onClick={(e) => e.stopPropagation()}>
        <aside className="flex w-full max-w-sm shrink-0 flex-col border-r border-zinc-800 bg-zinc-950/95">
          <div className="border-b border-zinc-800 px-5 py-4">
            <div className="text-[10px] font-bold uppercase tracking-[0.24em] text-zinc-500">Artifact Reference</div>
            <div className="mt-1 truncate text-sm font-semibold text-zinc-100" title={runName}>{runName}</div>
          </div>
          <div className="min-h-0 flex-1 overflow-y-auto px-3 py-3">
            <div className="space-y-4">
              {sections.map((section) => (
                <div key={section.key} className="space-y-2">
                  <div className="flex items-center gap-2 px-2">
                    <div className="flex h-6 w-6 items-center justify-center rounded border border-indigo-500/30 bg-indigo-500/10 text-[11px] font-bold text-indigo-200">
                      {section.key}
                    </div>
                    <div className="text-[11px] font-bold uppercase tracking-[0.18em] text-zinc-500">{section.label}</div>
                  </div>
                  <div className="space-y-1">
                    {section.artifacts.map((artifact) => {
                      const meta = getArtifactDisplayMeta(artifact.name)
                      const selected = selectedArtifact === artifact.name
                      return (
                        <button
                          key={artifact.name}
                          type="button"
                          onClick={() => onSelect(artifact.name)}
                          className={`w-full rounded-xl border px-3 py-2.5 text-left transition-colors ${
                            selected
                              ? 'border-indigo-300/70 bg-indigo-500/20 text-indigo-50'
                              : 'border-zinc-800 bg-zinc-900/40 text-zinc-200 hover:border-zinc-700 hover:bg-zinc-900/70'
                          }`}
                        >
                          <div className="flex items-start gap-3">
                            <div className={`mt-0.5 rounded border p-1.5 ${selected ? 'border-indigo-300/40 bg-indigo-400/15 text-indigo-100' : 'border-zinc-700 bg-zinc-900 text-zinc-400'}`}>
                              <FileText size={13} />
                            </div>
                            <div className="min-w-0 flex-1">
                              <div className={`truncate text-sm ${selected ? 'font-semibold text-white' : 'font-medium text-zinc-100'}`}>{meta.title}</div>
                              <div className={`mt-0.5 truncate text-[11px] ${selected ? 'text-indigo-200/70' : 'text-zinc-500'}`}>{meta.subtitle}</div>
                            </div>
                          </div>
                        </button>
                      )
                    })}
                  </div>
                </div>
              ))}
              {sections.length === 0 && (
                <div className="rounded-xl border border-dashed border-zinc-800 px-4 py-6 text-center text-xs text-zinc-500">
                  No artifact documents are available for this run.
                </div>
              )}
            </div>
          </div>
        </aside>

        <section className="flex min-w-0 flex-1 flex-col">
          <div className="flex items-start justify-between gap-4 border-b border-zinc-800 px-5 py-4">
            <div className="min-w-0">
              <div className="text-[10px] font-bold uppercase tracking-[0.24em] text-zinc-500">
                {selectedMeta ? `${selectedMeta.group} / ${selectedMeta.title}` : 'Artifact'}
              </div>
              <div className="mt-1 truncate text-sm font-semibold text-zinc-100">{selectedArtifact ?? 'No artifact selected'}</div>
            </div>
            <button onClick={onClose} className="rounded border border-zinc-700 px-3 py-1 text-xs text-zinc-300 hover:border-zinc-500 hover:text-white">
              Close
            </button>
          </div>
          <div className="min-h-0 flex-1 overflow-y-auto px-6 py-5">
            {selectedArtifact ? (
              <div className="prose prose-invert prose-zinc max-w-none">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>{artifactContent}</ReactMarkdown>
              </div>
            ) : (
              <div className="flex h-full items-center justify-center text-sm text-zinc-500">Select an artifact to preview.</div>
            )}
          </div>
        </section>
      </div>
    </div>
  )
}

export default ArtifactReferenceModal
