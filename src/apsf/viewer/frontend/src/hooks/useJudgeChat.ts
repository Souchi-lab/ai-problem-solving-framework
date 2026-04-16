import { useState } from 'react'
import type { JudgeRecommendation } from '../types'

const API_BASE = '/api'

interface JudgeChatParams {
  selectedTaxonomy: string | null
  activeTargetName: string
  activeDetailPhase: string | null
  activeJudgeRecommendation: JudgeRecommendation | null
}

export function useJudgeChat({
  selectedTaxonomy,
  activeTargetName,
  activeDetailPhase,
  activeJudgeRecommendation,
}: JudgeChatParams) {
  const [judgeChatMessages, setJudgeChatMessages] = useState<Array<{ role: 'user' | 'assistant'; content: string }>>([])
  const [judgeChatInput, setJudgeChatInput] = useState('')
  const [judgeChatLoading, setJudgeChatLoading] = useState(false)

  const sendJudgeChatMessage = async () => {
    if (!judgeChatInput.trim() || judgeChatLoading || !selectedTaxonomy || !activeTargetName) return
    const userMessage = { role: 'user' as const, content: judgeChatInput.trim() }
    const newMessages = [...judgeChatMessages, userMessage]
    setJudgeChatMessages(newMessages)
    setJudgeChatInput('')
    setJudgeChatLoading(true)
    try {
      const resp = await fetch(`${API_BASE}/runs/${selectedTaxonomy}/${encodeURIComponent(activeTargetName)}/judge-chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ messages: newMessages }),
      })
      const text = await resp.text()
      if (!resp.ok) {
        let detail = text
        try { detail = JSON.parse(text).detail ?? text } catch { /* use raw text */ }
        throw new Error(detail)
      }
      const data = JSON.parse(text)
      setJudgeChatMessages([...newMessages, { role: 'assistant', content: data.reply }])
    } catch (error) {
      setJudgeChatMessages([...newMessages, { role: 'assistant', content: `Error: ${error instanceof Error ? error.message : 'Unknown error'}` }])
    } finally {
      setJudgeChatLoading(false)
    }
  }

  const openJudgeChat = (setJudgeChatOpen: (open: boolean) => void) => {
    if (judgeChatMessages.length === 0) {
      const phaseLine = activeDetailPhase ? `Current phase: ${activeDetailPhase}.` : ''
      const recommendationLine = activeJudgeRecommendation
        ? `Suggested return: ${activeJudgeRecommendation.suggested_action_label || activeJudgeRecommendation.decision}.`
        : 'No judge advisory is loaded yet.'
      setJudgeChatMessages([
        {
          role: 'assistant',
          content: `Judge support is ready. ${phaseLine} ${recommendationLine} Ask about next action, tradeoffs, or what to write in the return comment.`.trim(),
        },
      ])
    }
    setJudgeChatOpen(true)
  }

  return {
    judgeChatMessages,
    setJudgeChatMessages,
    judgeChatInput,
    setJudgeChatInput,
    judgeChatLoading,
    sendJudgeChatMessage,
    openJudgeChat,
  }
}
