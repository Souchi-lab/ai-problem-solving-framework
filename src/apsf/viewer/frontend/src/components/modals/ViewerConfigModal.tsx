import { useEffect, useState } from 'react'
import type { ViewerConfig } from '../../types'

export function ViewerConfigModal({
  config,
  savingKey,
  onClose,
  onUpdate,
}: {
  config: ViewerConfig | null
  savingKey: string | null
  onClose: () => void
  onUpdate: (patch: Partial<Pick<ViewerConfig, 'execution_mode' | 'cli_tool_mode' | 'build_max_turns' | 'run_detail_refresh_ms'>>) => Promise<void>
}) {
  const [maxTurnsInput, setMaxTurnsInput] = useState<string>('')
  useEffect(() => {
    if (config?.build_max_turns !== undefined) setMaxTurnsInput(String(config.build_max_turns))
  }, [config?.build_max_turns])
  const sourceLabel = (source?: ViewerConfig['execution_mode_source']) => {
    if (source === 'env') return 'Env override'
    if (source === 'viewer_config') return 'viewer.config.json'
    return 'Default'
  }

  const boolLabel = (value?: boolean) => (value ? 'Configured' : 'Not set')

  return (
    <div className="fixed inset-0 z-[112] flex items-center justify-center bg-black/75 p-4 backdrop-blur-sm">
      <div className="w-full max-w-4xl rounded-2xl border border-zinc-800 bg-zinc-950 shadow-2xl shadow-black/60">
        <div className="flex items-start justify-between gap-4 border-b border-zinc-800 px-5 py-4">
          <div>
            <div className="text-lg font-bold text-zinc-100">Viewer Config</div>
            <div className="mt-1 text-sm text-zinc-400">
              Edit global execution policy here and inspect which config source is currently effective.
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded border border-zinc-700 bg-zinc-900 px-3 py-1.5 text-xs font-semibold text-zinc-300 hover:border-zinc-500 hover:text-white"
          >
            Close
          </button>
        </div>

        <div className="space-y-4 p-5">
          <div className="grid gap-4 xl:grid-cols-2">
            <div className="rounded border border-zinc-800 bg-black/20 p-4">
              <div className="mb-2 flex items-center justify-between gap-2">
                <div>
                  <div className="text-[10px] uppercase tracking-wide text-zinc-500">Execution Mode</div>
                  <div className="mt-0.5 text-sm text-zinc-200">{config?.execution_mode === 'provider' ? 'API' : 'CLI'}</div>
                </div>
                {savingKey?.startsWith('execution:') && <span className="text-[10px] text-sky-200">Saving...</span>}
              </div>
              <div className="mb-2 text-[10px] text-zinc-500">Source: {sourceLabel(config?.execution_mode_source)}</div>
              <div className="grid grid-cols-2 gap-2">
                {([
                  ['wrapper', 'CLI'],
                  ['provider', 'API'],
                ] as const).map(([mode, label]) => (
                  <button
                    key={mode}
                    type="button"
                    onClick={() => void onUpdate({ execution_mode: mode })}
                    disabled={!config || config.execution_mode === mode || savingKey !== null}
                    className={`rounded border px-3 py-2 text-[11px] font-semibold transition-colors ${
                      config?.execution_mode === mode
                        ? 'border-sky-400/50 bg-sky-500/20 text-sky-50'
                        : 'border-zinc-700 bg-zinc-900/70 text-zinc-300 hover:border-sky-500/40 hover:text-zinc-100'
                    } disabled:cursor-not-allowed disabled:border-zinc-800 disabled:bg-zinc-900 disabled:text-zinc-500`}
                  >
                    {label}
                  </button>
                ))}
              </div>
            </div>

            <div className="rounded border border-zinc-800 bg-black/20 p-4">
              <div className="mb-2 flex items-center justify-between gap-2">
                <div>
                  <div className="text-[10px] uppercase tracking-wide text-zinc-500">Available CLI</div>
                  <div className="mt-0.5 text-sm text-zinc-200">
                    {config?.cli_tool_mode === 'claude' ? 'Claude' : config?.cli_tool_mode === 'codex' ? 'Codex' : 'Both'}
                  </div>
                </div>
                {savingKey?.startsWith('cli:') && <span className="text-[10px] text-sky-200">Saving...</span>}
              </div>
              <div className="mb-2 text-[10px] text-zinc-500">
                `act`: {config?.act_wrapper_backend || '-'} ({sourceLabel(config?.act_wrapper_backend_source)}) · `build`: {config?.build_wrapper_backend || '-'} ({sourceLabel(config?.build_wrapper_backend_source)})
              </div>
              <div className="grid grid-cols-3 gap-2">
                {([
                  ['claude', 'Claude'],
                  ['codex', 'Codex'],
                  ['both', 'Both'],
                ] as const).map(([mode, label]) => (
                  <button
                    key={mode}
                    type="button"
                    onClick={() => void onUpdate({ cli_tool_mode: mode })}
                    disabled={!config || config.cli_tool_mode === mode || savingKey !== null}
                    className={`rounded border px-3 py-2 text-[11px] font-semibold transition-colors ${
                      config?.cli_tool_mode === mode
                        ? 'border-sky-400/50 bg-sky-500/20 text-sky-50'
                        : 'border-zinc-700 bg-zinc-900/70 text-zinc-300 hover:border-sky-500/40 hover:text-zinc-100'
                    } disabled:cursor-not-allowed disabled:border-zinc-800 disabled:bg-zinc-900 disabled:text-zinc-500`}
                  >
                    {label}
                  </button>
                ))}
              </div>
              <div className="mt-2 text-[10px] text-zinc-500">
                Both = `act` prefers Codex, tool-enabled `build` prefers Claude.
              </div>
            </div>
          </div>

          <div className="rounded border border-zinc-800 bg-black/20 p-4">
            <div className="mb-2 flex items-center justify-between gap-2">
              <div>
                <div className="text-[10px] uppercase tracking-wide text-zinc-500">Build Max Turns</div>
                <div className="mt-0.5 text-sm text-zinc-200">{config?.build_max_turns ?? 10} turns</div>
              </div>
              {savingKey === 'build_max_turns' && <span className="text-[10px] text-sky-200">Saving...</span>}
            </div>
            <div className="mb-2 text-[10px] text-zinc-500">Max agentic turns passed to the build wrapper as <span className="font-mono">-MaxTurns</span>. Default: 10. Range: 1–50.</div>
            <div className="flex items-center gap-2">
              <input
                type="number"
                min={1}
                max={50}
                step={1}
                value={maxTurnsInput}
                onChange={(e) => setMaxTurnsInput(e.target.value)}
                onBlur={() => {
                  const v = parseInt(maxTurnsInput, 10)
                  if (!isNaN(v) && v >= 1 && v <= 50 && v !== config?.build_max_turns) {
                    void onUpdate({ build_max_turns: v })
                  }
                }}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    const v = parseInt(maxTurnsInput, 10)
                    if (!isNaN(v) && v >= 1 && v <= 50 && v !== config?.build_max_turns) {
                      void onUpdate({ build_max_turns: v })
                    }
                  }
                }}
                disabled={savingKey !== null}
                className="w-24 rounded border border-zinc-700 bg-zinc-900 px-2 py-1.5 text-sm text-zinc-200 focus:border-sky-500 focus:outline-none disabled:cursor-not-allowed disabled:text-zinc-500"
              />
              <span className="text-[10px] text-zinc-500">Enter or blur to save</span>
            </div>
          </div>

          <div className="grid gap-4 xl:grid-cols-3">
            <div className="rounded border border-zinc-800 bg-black/20 p-4 text-xs">
              <div className="mb-2 text-[10px] uppercase tracking-wide text-zinc-500">Config Files</div>
              <div className="space-y-2 text-zinc-300">
                <div>
                  <div className="text-[10px] uppercase tracking-wide text-zinc-500">Viewer Config</div>
                  <div className="mt-0.5 break-all font-mono text-[11px] text-zinc-200">{config?.config_path || '-'}</div>
                  <div className="mt-0.5 text-[10px] text-zinc-500">{config ? (config.config_exists ? 'Present' : 'Missing') : '-'}</div>
                </div>
                <div>
                  <div className="text-[10px] uppercase tracking-wide text-zinc-500">Dotenv</div>
                  <div className="mt-0.5 break-all font-mono text-[11px] text-zinc-200">{config?.dotenv_path || '-'}</div>
                  <div className="mt-0.5 text-[10px] text-zinc-500">{config ? (config.dotenv_exists ? 'Present' : 'Missing') : '-'}</div>
                </div>
                <div>
                  <div className="text-[10px] uppercase tracking-wide text-zinc-500">Settings Module</div>
                  <div className="mt-0.5 break-all font-mono text-[11px] text-zinc-200">{config?.settings_path || '-'}</div>
                </div>
              </div>
            </div>

            <div className="rounded border border-zinc-800 bg-black/20 p-4 text-xs">
              <div className="mb-2 text-[10px] uppercase tracking-wide text-zinc-500">Framework Paths</div>
              <div className="space-y-2 text-zinc-300">
                <div>
                  <div className="text-[10px] uppercase tracking-wide text-zinc-500">Root</div>
                  <div className="mt-0.5 break-all font-mono text-[11px] text-zinc-200">{config?.framework_root || '-'}</div>
                </div>
                <div>
                  <div className="text-[10px] uppercase tracking-wide text-zinc-500">Runs</div>
                  <div className="mt-0.5 break-all font-mono text-[11px] text-zinc-200">{config?.runs_dir || '-'}</div>
                </div>
                <div>
                  <div className="text-[10px] uppercase tracking-wide text-zinc-500">Template</div>
                  <div className="mt-0.5 break-all font-mono text-[11px] text-zinc-200">{config?.template_dir || '-'}</div>
                </div>
              </div>
            </div>

            <div className="rounded border border-zinc-800 bg-black/20 p-4 text-xs">
              <div className="mb-2 text-[10px] uppercase tracking-wide text-zinc-500">Provider Defaults</div>
              <div className="space-y-2 text-zinc-300">
                <div>
                  <div className="text-[10px] uppercase tracking-wide text-zinc-500">OpenAI</div>
                  <div className="mt-0.5 font-mono text-[11px] text-zinc-200">{config?.default_openai_model || '-'}</div>
                  <div className="mt-0.5 text-[10px] text-zinc-500">API key: {boolLabel(config?.openai_api_key_configured)}</div>
                </div>
                <div>
                  <div className="text-[10px] uppercase tracking-wide text-zinc-500">Anthropic</div>
                  <div className="mt-0.5 font-mono text-[11px] text-zinc-200">{config?.default_anthropic_model || '-'}</div>
                  <div className="mt-0.5 text-[10px] text-zinc-500">API key: {boolLabel(config?.anthropic_api_key_configured)}</div>
                </div>
                <div>
                  <div className="text-[10px] uppercase tracking-wide text-zinc-500">Gemini</div>
                  <div className="mt-0.5 font-mono text-[11px] text-zinc-200">{config?.default_gemini_model || '-'}</div>
                  <div className="mt-0.5 text-[10px] text-zinc-500">API key: {boolLabel(config?.gemini_api_key_configured)}</div>
                </div>
              </div>
            </div>
          </div>

          <div className="rounded border border-zinc-800 bg-black/20 p-4 text-[11px] text-zinc-400">
            Viewer policy lives in `viewer.config.json` or `APSF_VIEWER_*` env vars. Provider defaults and API keys come from `.env` / process env via `Settings`. Run-local overrides still live in each run's `execution-assignment.md` and `model-assignment.md`.
          </div>
        </div>
      </div>
    </div>
  )
}

export default ViewerConfigModal
