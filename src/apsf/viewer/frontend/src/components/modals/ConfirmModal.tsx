import { useState } from 'react'
import type { ModalConfig } from '../../types'

export function ConfirmModal({ config, onCancel }: { config: ModalConfig; onCancel: () => void }) {
  const [inputValue, setInputValue] = useState(config.inputDefaultValue ?? '')
  const confirmToneClass =
    config.tone === 'danger'
      ? 'bg-red-600 hover:bg-red-500 shadow-red-500/20'
      : 'bg-emerald-600 hover:bg-emerald-500 shadow-emerald-500/20'
  const confirmDisabled = Boolean(config.inputRequired && inputValue.trim() === '')

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/60 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="w-full max-w-md scale-in-center rounded-xl border border-zinc-800 bg-zinc-900 p-6 shadow-2xl">
        <h3 className="mb-2 text-lg font-bold text-zinc-100">{config.title}</h3>
        <p className="mb-4 whitespace-pre-wrap text-sm text-zinc-400">{config.message}</p>
        {config.inputLabel && (
          <div className="mb-6">
            <label className="mb-2 block text-xs font-semibold uppercase tracking-[0.2em] text-zinc-500">
              {config.inputLabel}
            </label>
            <textarea
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              className="min-h-24 w-full rounded border border-zinc-700 bg-zinc-950 px-3 py-2 text-sm text-zinc-200 outline-none transition-colors focus:border-zinc-500"
              placeholder={config.inputPlaceholder}
            />
          </div>
        )}
        <div className="flex justify-end gap-3">
          <button
            onClick={onCancel}
            className="rounded-lg bg-zinc-800 px-4 py-2 text-sm font-semibold text-zinc-300 hover:bg-zinc-700 hover:text-white transition-colors"
          >
            {config.cancelLabel ?? 'Cancel'}
          </button>
          <button
            onClick={() => void config.onConfirm(inputValue)}
            disabled={confirmDisabled}
            className={`rounded-lg px-4 py-2 text-sm font-semibold text-white shadow-lg transition-all active:scale-95 disabled:cursor-not-allowed disabled:bg-zinc-800 disabled:text-zinc-500 ${confirmToneClass}`}
            id="modal-confirm-button"
          >
            {config.confirmLabel ?? 'Execute'}
          </button>
        </div>
      </div>
    </div>
  )
}

export default ConfirmModal
