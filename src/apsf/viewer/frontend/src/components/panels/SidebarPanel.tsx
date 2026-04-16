import { Activity, ChevronLeft, Pin, Search, Settings } from 'lucide-react'
import type { RunSummary } from '../../types'
import {
  PhaseBadge,
  ReworkBadge,
  CountBadge,
  PriorityBadge,
} from '../badges'

interface TaxonomySection {
  taxonomy: string
  label: string
  pinned: boolean
  open: boolean
  runs: RunSummary[]
}

interface SidebarPanelProps {
  searchTerm: string
  setSearchTerm: (value: string) => void
  humanBlockerFilter: 'all' | 'blocked'
  setHumanBlockerFilter: (value: 'all' | 'blocked') => void
  isLoadingRuns: boolean
  runsError: string | null
  filteredRuns: RunSummary[]
  taxonomySections: TaxonomySection[]
  selectedRun: string | null
  fetchRuns: () => void
  setIsLoadingRuns: (value: boolean) => void
  fetchDetail: (taxonomy: string, runName: string) => Promise<void>
  toggleOpenTaxonomy: (taxonomy: string) => void
  togglePinnedTaxonomy: (taxonomy: string) => void
  setSidebarOpen: (value: boolean) => void
  setViewerConfigModalOpen: (value: boolean) => void
}

export function SidebarPanel({
  searchTerm,
  setSearchTerm,
  humanBlockerFilter,
  setHumanBlockerFilter,
  isLoadingRuns,
  runsError,
  filteredRuns,
  taxonomySections,
  selectedRun,
  fetchRuns,
  setIsLoadingRuns,
  fetchDetail,
  toggleOpenTaxonomy,
  togglePinnedTaxonomy,
  setSidebarOpen,
  setViewerConfigModalOpen,
}: SidebarPanelProps) {
  return (
    <aside className="w-72 min-w-[18rem] shrink-0 border-r border-zinc-800 p-4 overflow-y-auto xl:w-80">
      <div className="mb-4 flex items-center gap-2">
        <Activity size={20} className="text-indigo-400" />
        <h1 className="flex-1 text-lg font-bold">APSF Viewer</h1>
        <button
          type="button"
          onClick={() => setViewerConfigModalOpen(true)}
          className="rounded border border-zinc-700 bg-zinc-900 p-1.5 text-zinc-300 hover:bg-zinc-800 hover:text-white"
          aria-label="Viewer Config"
          title="Viewer Config"
        >
          <Settings size={16} />
        </button>
        <button
          type="button"
          onClick={() => setSidebarOpen(false)}
          className="rounded border border-zinc-700 bg-zinc-900 p-1.5 text-zinc-300 hover:bg-zinc-800"
          aria-label="Hide run list"
          title="Hide run list"
        >
          <ChevronLeft size={16} />
        </button>
      </div>
      <div className="relative mb-4">
        <Search size={16} className="absolute left-3 top-2.5 text-zinc-500" />
        <input
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="w-full rounded border border-zinc-800 bg-zinc-900 py-2 pl-9 pr-3 text-sm"
          placeholder="Search runs..."
        />
      </div>
      <div className="mb-4 flex flex-wrap gap-2">
        {(['all', 'blocked'] as const).map((filter) => (
          <button
            key={filter}
            type="button"
            onClick={() => setHumanBlockerFilter(filter)}
            className={`rounded border px-2.5 py-1 text-[10px] font-bold uppercase ${
              humanBlockerFilter === filter
                ? 'border-amber-400 bg-amber-500/20 text-amber-100'
                : 'border-zinc-700 bg-zinc-900 text-zinc-400'
            }`}
          >
            {filter === 'all' ? 'All Runs' : 'Human Blockers'}
          </button>
        ))}
      </div>
      <div className="space-y-3">
        {isLoadingRuns ? (
          Array.from({ length: 8 }).map((_, i) => (
            <div key={i} className="h-24 w-full animate-pulse rounded border border-zinc-800 bg-zinc-900/20" />
          ))
        ) : runsError ? (
          <div className="rounded border border-red-500/30 bg-red-500/10 p-4 text-sm text-red-200">
            <div className="font-semibold">Failed to load runs</div>
            <div className="mt-1 text-xs text-red-200/80">{runsError}</div>
            <button
              onClick={() => {
                setIsLoadingRuns(true)
                void fetchRuns()
              }}
              className="mt-3 rounded border border-red-400/40 bg-red-500/10 px-3 py-1.5 text-xs font-bold text-red-100"
            >
              Retry
            </button>
          </div>
        ) : filteredRuns.length === 0 ? (
          <div className="py-12 text-center text-xs text-zinc-600">No runs found.</div>
        ) : (
          taxonomySections.map((section) => (
            <section key={section.taxonomy} className={`rounded-xl border ${section.pinned ? 'border-indigo-500/30 bg-indigo-500/5' : 'border-zinc-800 bg-zinc-950/30'}`}>
              <div className="flex items-center justify-between gap-2 px-3 py-2.5">
                <button
                  type="button"
                  onClick={() => toggleOpenTaxonomy(section.taxonomy)}
                  className="min-w-0 flex-1 text-left"
                >
                  <div className="flex items-center gap-2">
                    <span className={`rounded border px-1.5 py-0.5 text-[10px] font-bold uppercase ${section.pinned ? 'border-indigo-400/40 bg-indigo-500/20 text-indigo-100' : 'border-zinc-700 bg-zinc-900 text-zinc-400'}`}>
                      {section.taxonomy}
                    </span>
                    <span className="truncate text-[11px] font-bold uppercase tracking-[0.16em] text-zinc-400">{section.label}</span>
                  </div>
                  <div className="mt-1 text-[10px] text-zinc-600">
                    {section.runs.length} run{section.runs.length === 1 ? '' : 's'}{section.pinned ? ' / pinned' : ''}
                  </div>
                </button>
                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={() => togglePinnedTaxonomy(section.taxonomy)}
                    className={`rounded border p-1.5 ${section.pinned ? 'border-indigo-400/40 bg-indigo-500/20 text-indigo-100' : 'border-zinc-700 bg-zinc-900 text-zinc-500 hover:text-zinc-200'}`}
                    title={section.pinned ? 'Unpin taxonomy' : 'Pin taxonomy'}
                    aria-label={section.pinned ? 'Unpin taxonomy' : 'Pin taxonomy'}
                  >
                    <Pin size={12} />
                  </button>
                  <button
                    type="button"
                    onClick={() => toggleOpenTaxonomy(section.taxonomy)}
                    className="rounded border border-zinc-700 bg-zinc-900 px-2 py-1 text-[10px] font-semibold text-zinc-400"
                  >
                    {section.open ? 'Hide' : 'Show'}
                  </button>
                </div>
              </div>
              {section.open && (
                <div className="space-y-2 border-t border-zinc-800/80 px-2 pb-2 pt-2">
                  {section.runs.map((run) => (
                    <button
                      key={`${run.taxonomy}-${run.name}`}
                      onClick={() => void fetchDetail(run.taxonomy, run.name)}
                      className={`w-full rounded-lg border p-3 text-left ${selectedRun === run.name ? 'border-indigo-500/40 bg-indigo-500/10' : 'border-zinc-800 bg-zinc-900/40 hover:bg-zinc-900'}`}
                    >
                      <div className="mb-2 break-words text-sm font-medium">{run.name}</div>
                      <div className="mb-2 text-[11px] text-zinc-500">Next: {run.next_role}</div>
                      <div className="flex flex-wrap items-center gap-1">
                        <PhaseBadge phase={run.phase} />
                        <PriorityBadge priority={run.priority} />
                        <CountBadge count={run.child_count} />
                        <ReworkBadge count={[run.has_plan_review, run.has_build_review, run.has_review_review, run.has_improve_review].filter(Boolean).length} />
                        {run.human_blocker_active && (
                          <span className="rounded border border-amber-500/40 bg-amber-500/15 px-1.5 py-0.5 text-[10px] font-bold text-amber-200">
                            HUMAN BLOCKER
                          </span>
                        )}
                      </div>
                    </button>
                  ))}
                </div>
              )}
            </section>
          ))
        )}
      </div>
    </aside>
  )
}
