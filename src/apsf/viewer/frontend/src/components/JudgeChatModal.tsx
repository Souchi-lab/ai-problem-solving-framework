import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import type { OperatorAction } from '../types'

interface JudgeChatModalProps {
  activeTargetName: string
  judgeChatMessages: Array<{ role: 'user' | 'assistant'; content: string }>
  judgeChatInput: string
  judgeChatLoading: boolean
  suggestedJudgeAction: OperatorAction | null
  setJudgeChatOpen: (open: boolean) => void
  setJudgeChatInput: (input: string) => void
  setRerunComments: React.Dispatch<React.SetStateAction<Record<string, string>>>
  sendJudgeChatMessage: () => Promise<void>
}

export function JudgeChatModal({
  activeTargetName,
  judgeChatMessages,
  judgeChatInput,
  judgeChatLoading,
  suggestedJudgeAction,
  setJudgeChatOpen,
  setJudgeChatInput,
  setRerunComments,
  sendJudgeChatMessage,
}: JudgeChatModalProps) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4">
      <div className="flex h-[75vh] w-full max-w-2xl flex-col rounded-lg border border-fuchsia-500/30 bg-zinc-950 shadow-2xl">
        <div className="flex items-center justify-between border-b border-zinc-800 px-4 py-3">
          <div>
            <div className="text-[11px] uppercase tracking-wide text-fuchsia-300">Judge AI Assistant</div>
            <div className="text-[13px] font-semibold text-zinc-100">{activeTargetName}</div>
          </div>
          <button type="button" onClick={() => setJudgeChatOpen(false)} className="rounded p-1 text-zinc-400 hover:bg-zinc-800 hover:text-zinc-100">
            ✕
          </button>
        </div>
        <div className="flex-1 overflow-y-auto p-4 space-y-3">
          {judgeChatMessages.map((msg, i) => (
            <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className={`max-w-[85%] rounded-lg px-3 py-2 text-[12px] leading-relaxed ${msg.role === 'user' ? 'bg-fuchsia-500/20 text-fuchsia-100' : 'bg-zinc-800 text-zinc-200'}`}>
                <ReactMarkdown remarkPlugins={[remarkGfm]}>{msg.content}</ReactMarkdown>
              </div>
            </div>
          ))}
          {judgeChatLoading && (
            <div className="flex justify-start">
              <div className="rounded-lg bg-zinc-800 px-3 py-2 text-[12px] text-zinc-400">考え中...</div>
            </div>
          )}
        </div>
        {judgeChatMessages.length > 0 && judgeChatMessages[judgeChatMessages.length - 1].role === 'assistant' && suggestedJudgeAction && (
          <div className="border-t border-zinc-800 px-4 py-2">
            <button
              type="button"
              onClick={() => {
                const lastAI = judgeChatMessages[judgeChatMessages.length - 1].content
                setRerunComments((c) => ({ ...c, [suggestedJudgeAction.id]: lastAI }))
                setJudgeChatOpen(false)
              }}
              className="text-[11px] text-fuchsia-300 underline hover:text-fuchsia-100"
            >
              最後の AI メッセージをコメント欄に貼り付ける
            </button>
          </div>
        )}
        <div className="border-t border-zinc-800 p-3 flex gap-2">
          <textarea
            className="flex-1 resize-none rounded border border-zinc-700 bg-zinc-900 px-3 py-2 text-[12px] text-zinc-100 placeholder-zinc-500 focus:border-fuchsia-500/50 focus:outline-none"
            rows={2}
            placeholder="Judge として決定・質問を入力..."
            value={judgeChatInput}
            onChange={(e) => setJudgeChatInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault()
                void sendJudgeChatMessage()
              }
            }}
          />
          <button
            type="button"
            onClick={() => void sendJudgeChatMessage()}
            disabled={judgeChatLoading || !judgeChatInput.trim()}
            className="rounded border border-fuchsia-500/30 bg-fuchsia-500/15 px-4 text-[12px] font-semibold text-fuchsia-200 disabled:opacity-40 hover:bg-fuchsia-500/25"
          >
            送信
          </button>
        </div>
      </div>
    </div>
  )
}
