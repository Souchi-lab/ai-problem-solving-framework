import { ChevronRight, FileText, Terminal } from 'lucide-react'
import type { RunDetail } from '../types'
import {
  PhaseBadge,
  PriorityBadge,
  WorkflowProgress,
  SatisfiabilityWarning,
  CopyButton,
} from './badges'
import { parseSatisfiabilityReason } from '../utils/formatting'

interface RunLineageEntry {
  name: string
  label: string
  displayName: string
  phase: string
  nextRole: string
  hasChildren: boolean
  isParent: boolean
  isSelected: boolean
}

interface WorkspaceHeaderProps {
  detail: RunDetail
  targetDetail: RunDetail | null
  sidebarOpen: boolean
  setSidebarOpen: (open: boolean) => void
  workspaceTab: 'detail' | 'management' | 'activity' | 'agent-os'
  setWorkspaceTab: (tab: 'detail' | 'management' | 'activity' | 'agent-os') => void
  currentViewOpen: boolean
  setCurrentViewOpen: React.Dispatch<React.SetStateAction<boolean>>
  selectedTaxonomy: string | null
  targetRun: string | null
  openAgentOSWorkspace: (taxonomy?: string | null, runName?: string | null) => void
  openArtifactReferenceModal: (preferredArtifact?: string) => void
  fetchTargetDetail: (taxonomy: string, runName: string) => Promise<void>
}

export function WorkspaceHeader({
  detail,
  targetDetail,
  sidebarOpen,
  setSidebarOpen,
  workspaceTab,
  setWorkspaceTab,
  currentViewOpen,
  setCurrentViewOpen,
  selectedTaxonomy,
  targetRun,
  openAgentOSWorkspace,
  openArtifactReferenceModal,
  fetchTargetDetail,
}: WorkspaceHeaderProps) {
  const artifacts = targetDetail?.artifacts ?? detail.artifacts
  const childRuns = detail.children ?? []
  const runLineage: RunLineageEntry[] = [
    { name: detail.name, label: 'Parent', displayName: detail.name, phase: detail.phase, nextRole: detail.next_role, hasChildren: childRuns.length > 0, isParent: true, isSelected: targetRun === detail.name },
    ...childRuns.map((child) => ({ name: child.name, label: 'Child', displayName: child.child_name, phase: child.phase, nextRole: child.next_role, hasChildren: child.has_children, isParent: false, isSelected: targetRun === child.name })),
  ]

  return (
    <div className="sticky top-0 z-20 -mx-4 mb-4 border-b border-zinc-800 bg-zinc-950/95 px-4 pb-4 backdrop-blur">
      <div className="flex items-start justify-between gap-3">
        {!sidebarOpen && (
          <button
            type="button"
            onClick={() => setSidebarOpen(true)}
            className="mt-0.5 rounded border border-zinc-700 bg-zinc-900 p-1.5 text-zinc-300 hover:bg-zinc-800"
            aria-label="Show run list"
            title="Show run list"
          >
            <ChevronRight size={16} />
          </button>
        )}
        <div className="min-w-0 flex-1">
          <div className="mb-2 flex flex-wrap items-center gap-2">
            <PhaseBadge phase={targetDetail?.phase ?? detail.phase} />
            <PriorityBadge priority={targetDetail?.priority ?? detail.priority} />
            {targetDetail && targetDetail.name !== detail.name && (
              <span className="flex items-center gap-1 rounded bg-indigo-500/25 border border-indigo-500/40 px-1.5 py-0.5 font-bold text-indigo-100 text-[10px]">
                <Terminal size={10} />
                CHILD
              </span>
            )}
          </div>
          <div className="flex flex-col min-w-0">
            <span className="mb-0.5 truncate leading-tight text-xs text-zinc-500" title={targetDetail?.name ?? detail.name}>
              {(targetDetail?.name ?? detail.name).split('_')[0]}
            </span>
            <h2 className="truncate text-base font-bold leading-snug">
              {(targetDetail?.name ?? detail.name).split('_').slice(1).join('_') || (targetDetail?.name ?? detail.name)}
            </h2>
          </div>
        </div>
      </div>

      <WorkflowProgress
        phase={targetDetail?.phase ?? detail.phase}
        hasPlanReview={artifacts.some((a) => a.name === 'plan_review.md' && a.exists)}
        hasBuildReview={artifacts.some((a) => a.name === 'build_review.md' && a.exists)}
        hasReviewReview={artifacts.some((a) => a.name === 'review_review.md' && a.exists)}
        hasImproveReview={artifacts.some((a) => a.name === 'improve_review.md' && a.exists)}
        compact
      />

      {workspaceTab !== 'agent-os' && (
        <div className="mt-3 rounded border border-indigo-500/30 bg-indigo-500/10 p-3">
          <div className="mb-2 flex items-center justify-between">
            <div className="flex items-center gap-2 text-indigo-300">
              <Terminal size={14} />
              <span className="text-xs font-bold uppercase">
                Primary Command
                {targetDetail && (
                  <span className="ml-2 rounded bg-zinc-800 px-1.5 py-0.5 text-[10px] text-zinc-300">
                    {targetDetail.name === detail.name ? 'PARENT' : targetDetail.name.split('/').slice(-1)[0]}
                  </span>
                )}
              </span>
            </div>
            <CopyButton text={targetDetail?.operator_command ?? ''} />
          </div>
          <div className="whitespace-pre-wrap break-words rounded bg-black/30 p-2 font-mono text-xs line-clamp-2">{targetDetail?.operator_command ?? ''}</div>
        </div>
      )}

      <div className="overflow-hidden">
        <div className="mt-2 flex flex-wrap items-center gap-2 text-xs text-zinc-400">
          <span>Next: {targetDetail?.next_role ?? detail.next_role}</span>
          {targetDetail && targetDetail.name !== detail.name && (
            <span className="flex items-center gap-1 rounded bg-indigo-500/25 border border-indigo-500/40 px-2 py-0.5 font-bold text-indigo-100 shadow-[0_0_10px_rgba(99,102,241,0.2)]">
              <Terminal size={10} />
              VIEWING CHILD
            </span>
          )}
        </div>
        {(() => {
          const parsed = parseSatisfiabilityReason(targetDetail?.decision_reason ?? detail.decision_reason)
          return parsed.primary ? (
            <p className="mt-2 text-sm text-zinc-500 line-clamp-2">{parsed.primary}</p>
          ) : null
        })()}
        <SatisfiabilityWarning reason={targetDetail?.decision_reason ?? detail.decision_reason} />
      </div>

      {runLineage.length > 1 && (
        <div className="mt-3 space-y-2 border-t border-zinc-800/70 pt-3">
          <div className="flex items-center justify-between gap-3">
            <div className="text-[10px] font-semibold uppercase tracking-[0.16em] text-zinc-600">Run Lineage</div>
            <button
              type="button"
              onClick={() => setCurrentViewOpen((open) => !open)}
              className="rounded border border-zinc-800 bg-zinc-900/60 px-2 py-1 text-[10px] font-semibold text-zinc-400"
            >
              {currentViewOpen ? 'Hide' : 'Show'}
            </button>
          </div>
          {currentViewOpen && (
            <div className="space-y-2">
              {runLineage.map((entry) => (
                <button
                  key={entry.name}
                  onClick={() => {
                    setCurrentViewOpen(false)
                    void fetchTargetDetail(detail.taxonomy, entry.name)
                  }}
                  className={`w-full rounded-xl border px-3 py-3 text-left ${
                    entry.isSelected
                      ? 'border-indigo-500/40 bg-indigo-500/10 text-indigo-100'
                      : 'border-zinc-800 bg-zinc-900/60 text-zinc-300 hover:bg-zinc-900'
                  }`}
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0">
                      <div className="flex flex-wrap items-center gap-2">
                        <span className={`rounded border px-1.5 py-0.5 text-[10px] font-bold uppercase ${entry.isParent ? 'border-emerald-500/30 bg-emerald-500/10 text-emerald-200' : 'border-indigo-500/30 bg-indigo-500/10 text-indigo-200'}`}>
                          {entry.label}
                        </span>
                        {entry.isSelected && (
                          <span className="rounded border border-indigo-400/40 bg-indigo-500/15 px-1.5 py-0.5 text-[10px] font-bold uppercase text-indigo-100">
                            Viewing
                          </span>
                        )}
                      </div>
                      <div className="mt-2 truncate text-sm font-semibold text-zinc-100">{entry.displayName}</div>
                      <div className="mt-1 flex flex-wrap items-center gap-2 text-[11px] text-zinc-500">
                        <span>{entry.phase}</span>
                        <span className="opacity-40">/</span>
                        <span>{entry.nextRole}</span>
                        {entry.hasChildren && (
                          <>
                            <span className="opacity-40">/</span>
                            <span>has children</span>
                          </>
                        )}
                      </div>
                    </div>
                    <div className="shrink-0 flex flex-col items-end gap-1">
                      <PhaseBadge phase={entry.phase} />
                    </div>
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>
      )}

      <div className="mt-3 flex flex-wrap items-center gap-2 border-t border-zinc-800/70 pt-3">
        <button
          onClick={() => openAgentOSWorkspace(selectedTaxonomy, targetRun)}
          className={`rounded border px-3 py-1.5 text-xs font-bold transition-all duration-200 ${workspaceTab === 'agent-os' ? 'border-emerald-400 bg-emerald-500/20 text-emerald-100' : 'border-zinc-700 bg-zinc-900 text-zinc-300 hover:bg-zinc-800'}`}
        >
          Agent OS
        </button>
        <button
          onClick={() => setWorkspaceTab('detail')}
          className={`rounded border px-3 py-1.5 text-xs font-bold transition-all duration-200 ${workspaceTab === 'detail' ? 'border-indigo-400 bg-indigo-500/20 text-indigo-100' : 'border-zinc-700 bg-zinc-900 text-zinc-300 hover:bg-zinc-800'}`}
        >
          Run Detail
        </button>
        <button
          onClick={() => setWorkspaceTab('management')}
          className={`rounded border px-3 py-1.5 text-xs font-bold transition-all duration-200 ${workspaceTab === 'management' ? 'border-indigo-400 bg-indigo-500/20 text-indigo-100' : 'border-zinc-700 bg-zinc-900 text-zinc-300 hover:bg-zinc-800'}`}
        >
          Run Management
        </button>
        <button
          onClick={() => setWorkspaceTab('activity')}
          className={`rounded border px-3 py-1.5 text-xs font-bold transition-all duration-200 ${workspaceTab === 'activity' ? 'border-indigo-400 bg-indigo-500/20 text-indigo-100' : 'border-zinc-700 bg-zinc-900 text-zinc-300 hover:bg-zinc-800'}`}
        >
          Activity
        </button>
        {artifacts.some((artifact) => artifact.exists) && (
          <button
            type="button"
            onClick={() => openArtifactReferenceModal()}
            className="ml-auto inline-flex items-center gap-2 rounded border border-indigo-500/30 bg-indigo-500/10 px-3 py-1.5 text-xs font-bold text-indigo-100 transition-colors hover:bg-indigo-500/20"
          >
            <FileText size={14} />
            Artifacts
          </button>
        )}
      </div>
    </div>
  )
}
