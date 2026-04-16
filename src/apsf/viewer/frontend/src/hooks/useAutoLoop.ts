import { useCallback, useRef, useState } from 'react'
import type { AutoLoopStatus, ModalConfig } from '../types'

const API_BASE = '/api'

export function useAutoLoop(setModalConfig: (config: ModalConfig | null) => void) {
  const [autoLoopStatus, setAutoLoopStatus] = useState<AutoLoopStatus | null>(null)
  const [autoLoopLoading, setAutoLoopLoading] = useState(false)
  const [autoLoopMutating, setAutoLoopMutating] = useState<'start' | 'stop' | 'cancel' | null>(null)
  const [loopStopToast, setLoopStopToast] = useState<{ stopReason: string | null; lastExit: number | null } | null>(null)
  const prevAutoLoopRunningRef = useRef<boolean | null>(null)

  const loadAutoLoopStatus = useCallback(async (taxonomy: string, runName: string) => {
    setAutoLoopLoading(true)
    try {
      const resp = await fetch(`${API_BASE}/runs/${taxonomy}/${encodeURIComponent(runName)}/auto-loop-status`)
      if (!resp.ok) {
        throw new Error(`Failed to load auto-loop status (${resp.status})`)
      }
      const data = await resp.json()
      const next: AutoLoopStatus = {
        running: Boolean(data.running),
        stop_pending: Boolean(data.stop_pending),
        stop_reason: typeof data.stop_reason === 'string' ? data.stop_reason : undefined,
        last_exit: typeof data.last_exit === 'number' ? data.last_exit : undefined,
      }
      // Detect running → stopped transition and fire toast
      if (prevAutoLoopRunningRef.current === true && !next.running) {
        setLoopStopToast({
          stopReason: next.stop_reason ?? null,
          lastExit: next.last_exit ?? null,
        })
      }
      prevAutoLoopRunningRef.current = next.running
      setAutoLoopStatus(next)
    } catch {
      setAutoLoopStatus(null)
    } finally {
      setAutoLoopLoading(false)
    }
  }, [])

  const startAutoLoop = useCallback(async (taxonomy: string, runName: string, buildScript?: string) => {
    setAutoLoopMutating('start')
    try {
      const resp = await fetch(`${API_BASE}/runs/${taxonomy}/${encodeURIComponent(runName)}/start-auto-loop`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(buildScript ? { build_script: buildScript } : {}),
      })
      const data = await resp.json().catch(() => ({}))
      if (!resp.ok) {
        throw new Error(typeof data.detail === 'string' ? data.detail : `Failed to start auto-loop (${resp.status})`)
      }
      await loadAutoLoopStatus(taxonomy, runName)
    } catch (error) {
      setModalConfig({
        title: 'Failed to Start Auto-Loop',
        message: error instanceof Error ? error.message : 'Failed to start auto-loop.',
        onConfirm: () => setModalConfig(null),
      })
    } finally {
      setAutoLoopMutating(null)
    }
  }, [loadAutoLoopStatus, setModalConfig])

  const requestAutoLoopStop = useCallback(async (taxonomy: string, runName: string) => {
    setAutoLoopMutating('stop')
    try {
      const resp = await fetch(`${API_BASE}/runs/${taxonomy}/${encodeURIComponent(runName)}/request-stop`, { method: 'POST' })
      const data = await resp.json().catch(() => ({}))
      if (!resp.ok) {
        throw new Error(typeof data.detail === 'string' ? data.detail : `Failed to request stop (${resp.status})`)
      }
      await loadAutoLoopStatus(taxonomy, runName)
    } catch (error) {
      setModalConfig({
        title: 'Failed to Request Auto-Loop Stop',
        message: error instanceof Error ? error.message : 'Failed to request auto-loop stop.',
        onConfirm: () => setModalConfig(null),
      })
    } finally {
      setAutoLoopMutating(null)
    }
  }, [loadAutoLoopStatus, setModalConfig])

  const cancelAutoLoopStop = useCallback(async (taxonomy: string, runName: string) => {
    setAutoLoopMutating('cancel')
    try {
      const resp = await fetch(`${API_BASE}/runs/${taxonomy}/${encodeURIComponent(runName)}/request-stop`, { method: 'DELETE' })
      const data = await resp.json().catch(() => ({}))
      if (!resp.ok) {
        throw new Error(typeof data.detail === 'string' ? data.detail : `Failed to cancel stop (${resp.status})`)
      }
      await loadAutoLoopStatus(taxonomy, runName)
    } catch (error) {
      setModalConfig({
        title: 'Failed to Cancel Stop Request',
        message: error instanceof Error ? error.message : 'Failed to cancel stop request.',
        onConfirm: () => setModalConfig(null),
      })
    } finally {
      setAutoLoopMutating(null)
    }
  }, [loadAutoLoopStatus, setModalConfig])

  return {
    autoLoopStatus,
    setAutoLoopStatus,
    autoLoopLoading,
    autoLoopMutating,
    loopStopToast,
    setLoopStopToast,
    loadAutoLoopStatus,
    startAutoLoop,
    requestAutoLoopStop,
    cancelAutoLoopStop,
  }
}
