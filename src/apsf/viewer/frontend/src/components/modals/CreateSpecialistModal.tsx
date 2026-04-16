import { useEffect, useRef, useState, type ChangeEvent } from 'react'
import type { CreateSpecialistResult } from '../../types'
import {
  deriveSpecialistPathPreview,
  slugifySpecialistName,
  defaultSpecialistTitle,
  buildSpecialistMarkdownTemplate,
  parseSpecialistMarkdownImport,
  validateImportedSpecialistDraft,
} from '../../utils/specialist'
import { CopyButton } from '../../components/badges'

const API_BASE = '/api'

export function CreateSpecialistModal({
  taxonomy,
  runName,
  role,
  suggestedCode,
  onClose,
  onCreated,
}: {
  taxonomy: string
  runName: string
  role: 'Planner' | 'Builder' | 'Critic'
  suggestedCode?: string | null
  onClose: () => void
  onCreated: (result: CreateSpecialistResult) => Promise<void>
}) {
  const [specialistCode, setSpecialistCode] = useState(suggestedCode ?? '')
  const [slug, setSlug] = useState('')
  const [title, setTitle] = useState('')
  const [scope, setScope] = useState('')
  const [useWhen, setUseWhen] = useState('')
  const [outOfScope, setOutOfScope] = useState('')
  const [evaluationCriteria, setEvaluationCriteria] = useState('')
  const [importMarkdown, setImportMarkdown] = useState('')
  const [importStatus, setImportStatus] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const importFileRef = useRef<HTMLInputElement | null>(null)

  useEffect(() => {
    setSpecialistCode(suggestedCode ?? '')
  }, [suggestedCode])

  const pathPreview = deriveSpecialistPathPreview(role, specialistCode, slug)
  const templateMarkdown = buildSpecialistMarkdownTemplate({
    role,
    specialistCode,
    title,
    scope,
    useWhen,
    outOfScope,
    evaluationCriteria,
  })
  const formComplete = [
    specialistCode,
    slug,
    title,
    scope,
    useWhen,
    outOfScope,
    evaluationCriteria,
  ].every((value) => value.trim() !== '')

  const applyTemplateDefaults = () => {
    setTitle((current) => current || defaultSpecialistTitle(role))
    setSlug((current) => current || slugifySpecialistName(defaultSpecialistTitle(role)))
    setScope((current) => current || 'Focus on the specialist-specific responsibility boundary and primary decision lens.')
    setUseWhen((current) => current || 'Use this specialist when the run clearly benefits from its dedicated operating lens.')
    setOutOfScope((current) => current || 'Do not broaden into adjacent work that belongs to another specialist or the generic role prompt.')
    setEvaluationCriteria((current) => current || 'Output should stay role-aligned, concrete, scoped, and easy to review.')
    setImportStatus('Loaded starter template defaults into the form.')
  }

  const applyImportedMarkdown = (markdown: string) => {
    const parsed = parseSpecialistMarkdownImport(markdown, role)
    if ('error' in parsed) {
      setImportStatus(parsed.error ?? `Could not parse a specialist markdown template for ${role}.`)
      return
    }
    if (parsed.specialistCode) setSpecialistCode(parsed.specialistCode)
    if (parsed.title) setTitle(parsed.title)
    if (parsed.slug) setSlug(parsed.slug)
    if (parsed.scope) setScope(parsed.scope)
    if (parsed.useWhen) setUseWhen(parsed.useWhen)
    if (parsed.outOfScope) setOutOfScope(parsed.outOfScope)
    if (parsed.evaluationCriteria) setEvaluationCriteria(parsed.evaluationCriteria)
    const validation = validateImportedSpecialistDraft(parsed, role)
    setImportStatus(validation.message)
  }

  const handleImportFile = async (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return
    try {
      const content = await file.text()
      setImportMarkdown(content)
      applyImportedMarkdown(content)
    } catch {
      setImportStatus('Failed to read the selected markdown file.')
    } finally {
      event.target.value = ''
    }
  }

  const copyTemplateMarkdown = async () => {
    try {
      await navigator.clipboard.writeText(templateMarkdown)
      setImportStatus('Copied markdown template to clipboard.')
    } catch {
      setImportStatus('Failed to copy markdown template.')
    }
  }

  const handleCreate = async () => {
    setSaving(true)
    setError(null)
    try {
      const resp = await fetch(`${API_BASE}/runs/${taxonomy}/${encodeURIComponent(runName)}/specialists/create`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          role,
          specialist_code: specialistCode,
          slug,
          title,
          scope,
          use_when: useWhen,
          out_of_scope: outOfScope,
          evaluation_criteria: evaluationCriteria,
        }),
      })
      const data = (await resp.json()) as CreateSpecialistResult | { detail?: string }
      if (!resp.ok) throw new Error((data as { detail?: string }).detail || `HTTP ${resp.status}`)
      await onCreated(data as CreateSpecialistResult)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to create specialist')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="fixed inset-0 z-[115] flex items-center justify-center bg-black/75 p-4 backdrop-blur-sm">
      <div className="max-h-[88vh] w-full max-w-3xl overflow-y-auto rounded-2xl border border-zinc-800 bg-zinc-950 shadow-2xl shadow-black/60">
        <div className="border-b border-zinc-800 px-5 py-4">
          <div className="text-lg font-bold text-zinc-100">Create New {role} Specialist</div>
          <div className="mt-1 text-sm text-zinc-400">
            Create a reusable library asset. This does not assign it to the run until you confirm assignment separately.
          </div>
          <div className="mt-2 text-xs text-amber-200/90">
            Create only. Existing specialist codes and files cannot be overwritten here.
          </div>
        </div>

        <div className="space-y-4 p-5">
          <div className="rounded border border-emerald-500/20 bg-emerald-500/5 p-4">
            <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
              <div>
                <div className="text-[10px] font-bold uppercase tracking-[0.2em] text-emerald-300">Markdown Helpers</div>
                <div className="mt-1 text-sm text-zinc-300">
                  Start from a template or prefill the form from markdown. This does not import or overwrite a library asset.
                </div>
              </div>
              <div className="flex flex-wrap gap-2">
                <button
                  type="button"
                  onClick={applyTemplateDefaults}
                  className="rounded border border-emerald-500/30 bg-emerald-500/10 px-3 py-1.5 text-xs font-semibold text-emerald-100 hover:bg-emerald-500/20"
                >
                  Load Template Defaults
                </button>
                <button
                  type="button"
                  onClick={() => importFileRef.current?.click()}
                  className="rounded border border-cyan-500/30 bg-cyan-500/10 px-3 py-1.5 text-xs font-semibold text-cyan-100 hover:bg-cyan-500/20"
                >
                  Prefill From .md File
                </button>
                <button
                  type="button"
                  onClick={() => void copyTemplateMarkdown()}
                  className="rounded border border-fuchsia-500/30 bg-fuchsia-500/10 px-3 py-1.5 text-xs font-semibold text-fuchsia-100 hover:bg-fuchsia-500/20"
                >
                  Copy Markdown Template
                </button>
              </div>
            </div>

            <input
              ref={importFileRef}
              type="file"
              accept=".md,text/markdown"
              onChange={(e) => void handleImportFile(e)}
              className="hidden"
            />

            <div className="grid gap-4 lg:grid-cols-2">
              <label className="block">
                <div className="mb-2 text-[10px] font-bold uppercase tracking-[0.2em] text-zinc-500">Prefill From Markdown</div>
                <textarea
                  value={importMarkdown}
                  onChange={(e) => setImportMarkdown(e.target.value)}
                  className="min-h-40 w-full rounded border border-zinc-700 bg-zinc-900 px-3 py-2 font-mono text-xs text-zinc-100"
                  placeholder="Paste specialist markdown here to prefill the form. Review role/code/slug before creating."
                />
                <div className="mt-2 flex flex-wrap gap-2">
                  <button
                    type="button"
                    onClick={() => applyImportedMarkdown(importMarkdown)}
                    disabled={importMarkdown.trim() === ''}
                    className="rounded border border-cyan-500/30 bg-cyan-500/10 px-3 py-1.5 text-xs font-semibold text-cyan-100 hover:bg-cyan-500/20 disabled:opacity-50"
                  >
                    Apply Markdown Prefill
                  </button>
                  <button
                    type="button"
                    onClick={() => setImportMarkdown(templateMarkdown)}
                    className="rounded border border-zinc-700 bg-zinc-900 px-3 py-1.5 text-xs font-semibold text-zinc-300 hover:border-zinc-500 hover:text-white"
                  >
                    Send Template To Import Box
                  </button>
                </div>
              </label>

              <div className="rounded border border-zinc-800 bg-black/20 p-3">
                <div className="mb-2 flex items-center justify-between gap-3">
                  <div className="text-[10px] font-bold uppercase tracking-[0.2em] text-zinc-500">Markdown Template Preview</div>
                  <CopyButton text={templateMarkdown} />
                </div>
                <pre className="max-h-56 overflow-auto whitespace-pre-wrap rounded bg-zinc-950/70 p-3 font-mono text-[11px] text-zinc-300">{templateMarkdown}</pre>
              </div>
            </div>

            {importStatus && (
              <div className={`mt-3 rounded border px-3 py-2 text-xs ${
                importStatus.includes('valid for')
                  ? 'border-emerald-500/30 bg-emerald-500/10 text-emerald-100'
                  : importStatus.includes('validation issues')
                    ? 'border-amber-500/30 bg-amber-500/10 text-amber-100'
                    : 'border-zinc-700 bg-black/20 text-zinc-300'
              }`}>
                {importStatus}
              </div>
            )}
          </div>

          <div className="grid gap-4 md:grid-cols-3">
            <label className="block">
              <div className="mb-2 text-[10px] font-bold uppercase tracking-[0.2em] text-zinc-500">Code</div>
              <input value={specialistCode} onChange={(e) => setSpecialistCode(e.target.value)} className="w-full rounded border border-zinc-700 bg-zinc-900 px-3 py-2 text-sm text-zinc-100" placeholder={role === 'Planner' ? 'P-13' : role === 'Builder' ? 'B-08' : 'C-09'} />
            </label>
            <label className="block">
              <div className="mb-2 text-[10px] font-bold uppercase tracking-[0.2em] text-zinc-500">Slug</div>
              <input value={slug} onChange={(e) => setSlug(e.target.value)} className="w-full rounded border border-zinc-700 bg-zinc-900 px-3 py-2 text-sm text-zinc-100" placeholder="workflow-integrity-critic" />
            </label>
            <label className="block">
              <div className="mb-2 text-[10px] font-bold uppercase tracking-[0.2em] text-zinc-500">Title</div>
              <input value={title} onChange={(e) => setTitle(e.target.value)} className="w-full rounded border border-zinc-700 bg-zinc-900 px-3 py-2 text-sm text-zinc-100" placeholder="Workflow Integrity Critic" />
            </label>
          </div>

          <div className="rounded border border-cyan-500/20 bg-cyan-500/5 p-4 text-sm">
            <div className="text-[10px] font-bold uppercase tracking-[0.2em] text-cyan-300">Write Preview</div>
            <div className="mt-2 text-zinc-200">{pathPreview || 'Enter role-aligned code and slug to preview the backend-derived library path.'}</div>
            <div className="mt-2 text-xs text-zinc-500">Backend derives the final path from role + code + slug. The UI does not write arbitrary file paths.</div>
          </div>

          <label className="block">
            <div className="mb-2 text-[10px] font-bold uppercase tracking-[0.2em] text-zinc-500">Scope</div>
            <textarea value={scope} onChange={(e) => setScope(e.target.value)} className="min-h-24 w-full rounded border border-zinc-700 bg-zinc-900 px-3 py-2 text-sm text-zinc-100" />
          </label>

          <label className="block">
            <div className="mb-2 text-[10px] font-bold uppercase tracking-[0.2em] text-zinc-500">Use This Specialist When</div>
            <textarea value={useWhen} onChange={(e) => setUseWhen(e.target.value)} className="min-h-24 w-full rounded border border-zinc-700 bg-zinc-900 px-3 py-2 text-sm text-zinc-100" />
          </label>

          <div className="grid gap-4 md:grid-cols-2">
            <label className="block">
              <div className="mb-2 text-[10px] font-bold uppercase tracking-[0.2em] text-zinc-500">Out Of Scope</div>
              <textarea value={outOfScope} onChange={(e) => setOutOfScope(e.target.value)} className="min-h-28 w-full rounded border border-zinc-700 bg-zinc-900 px-3 py-2 text-sm text-zinc-100" />
            </label>
            <label className="block">
              <div className="mb-2 text-[10px] font-bold uppercase tracking-[0.2em] text-zinc-500">Evaluation Criteria</div>
              <textarea value={evaluationCriteria} onChange={(e) => setEvaluationCriteria(e.target.value)} className="min-h-28 w-full rounded border border-zinc-700 bg-zinc-900 px-3 py-2 text-sm text-zinc-100" />
            </label>
          </div>

          {error && <div className="rounded border border-red-500/30 bg-red-500/10 px-3 py-2 text-sm text-red-200">{error}</div>}

          <div className="flex justify-end gap-3">
            <button onClick={onClose} className="rounded border border-zinc-700 bg-zinc-900 px-4 py-2 text-sm font-semibold text-zinc-300 hover:border-zinc-500 hover:text-white">
              Cancel
            </button>
            <button
              disabled={!formComplete || saving}
              onClick={() => void handleCreate()}
              className="rounded border border-fuchsia-500/40 bg-fuchsia-500/15 px-4 py-2 text-sm font-semibold text-fuchsia-100 hover:bg-fuchsia-500/25 disabled:opacity-50"
            >
              {saving ? 'Creating...' : 'Create Specialist'}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

export default CreateSpecialistModal
