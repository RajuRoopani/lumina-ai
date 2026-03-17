import React, { useState, useRef, useEffect, useCallback } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { useChat } from '../../hooks/useChat'
import { api } from '../../api/client'
import type { ChatMessage } from '../../types'

const QUICK_ACTIONS = [
  'Summarize key points',
  'List all risks',
  'Add a sequence diagram',
  'Expand architecture section',
  'Compare and propose improvements',
]

interface Props {
  reportId: string | undefined
  onSectionUpdate?: (sectionId: string, html: string) => void
  onNewReport?: (reportId: string) => void
  iframeRef?: React.RefObject<HTMLIFrameElement | null>
}

export function ChatPanel({ reportId, onSectionUpdate, onNewReport, iframeRef }: Props) {
  const [tab, setTab] = useState<'chat' | 'annotations'>('chat')
  const [input, setInput] = useState('')
  const bottomRef = useRef<HTMLDivElement>(null)
  const qc = useQueryClient()

  const { messages, streaming, streamingText, sendMessage } = useChat(reportId)

  const handleAction = useCallback((action: Record<string, unknown>) => {
    if (action.action === 'section_update' && onSectionUpdate) {
      // Note: target origin must be '*' because srcdoc iframes have opaque (null) origin
      const iframeWindow = iframeRef?.current?.contentWindow
      iframeWindow?.postMessage({
        type: 'UPDATE_SECTION',
        sectionId: action.section_id,
        html: action.html,
      }, '*')
      // Persist to backend
      if (reportId) {
        api.reports.updateSection(reportId, action.section_id as string, action.html as string)
          .then(() => qc.invalidateQueries({ queryKey: ['report', reportId] }))
      }
    }
    if (action.action === 'new_report' && onNewReport && action.html && reportId) {
      // Save as new report then switch to it. Use current report's doc IDs.
      api.chat.compareStream([reportId], 'Use the AI-generated proposal HTML as the new report')
        .then(async res => {
          if (!res.body) return
          const reader = res.body.getReader()
          const decoder = new TextDecoder()
          while (true) {
            const { done, value } = await reader.read()
            if (done) break
            for (const line of decoder.decode(value, { stream: true }).split('\n')) {
              if (!line.startsWith('data: ')) continue
              try {
                const p = JSON.parse(line.slice(6))
                if (p.event === 'done') onNewReport(p.data.id)
              } catch { /* skip */ }
            }
          }
        })
    }
  }, [reportId, onSectionUpdate, onNewReport, iframeRef, qc])

  const handleSend = async () => {
    if (!input.trim() || !reportId || streaming) return
    const msg = input.trim()
    setInput('')
    await sendMessage(msg, handleAction)
  }

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, streamingText])

  return (
    <div className="w-56 flex-shrink-0 flex flex-col bg-[#161b22] border-l border-[#21262d]">
      <div className="flex border-b border-[#21262d]">
        {(['chat', 'annotations'] as const).map(t => (
          <button key={t} onClick={() => setTab(t)}
            className={`flex-1 py-2 text-xs capitalize transition-colors ${
              tab === t ? 'text-[#e6edf3] border-b-2 border-[#388bfd]' : 'text-[#8b949e] hover:text-[#e6edf3]'
            }`}>{t === 'chat' ? '🤖 AI Chat' : '📌 Notes'}</button>
        ))}
      </div>

      {!reportId && (
        <div className="flex-1 flex items-center justify-center text-[#484f58] text-xs text-center p-4">
          Generate a report to start chatting
        </div>
      )}

      {reportId && tab === 'chat' && (
        <>
          <div className="flex-1 overflow-y-auto p-2 space-y-2">
            {messages.length === 0 && !streaming && (
              <div className="text-[#484f58] text-xs text-center pt-4">
                Ask anything about this document
              </div>
            )}
            {messages.map((m: ChatMessage) => (
              <div key={m.id} className={`rounded-lg p-2 text-xs leading-relaxed ${
                m.role === 'user'
                  ? 'bg-[#0d1117] text-[#8b949e] ml-2'
                  : 'bg-[#0f1a2e] border border-[#388bfd]/30 text-[#cdd9e5]'
              }`}>
                {m.content}
              </div>
            ))}
            {streaming && streamingText && (
              <div className="bg-[#0f1a2e] border border-[#388bfd]/30 rounded-lg p-2 text-xs text-[#cdd9e5] leading-relaxed">
                {streamingText}
                <span className="animate-pulse">▌</span>
              </div>
            )}
            <div ref={bottomRef} />
          </div>

          <div className="p-2 border-t border-[#21262d] space-y-2">
            <div className="flex flex-wrap gap-1">
              {QUICK_ACTIONS.slice(0, 3).map(a => (
                <button key={a} onClick={() => { setInput(a); }}
                  className="text-[9px] bg-[#1c2128] hover:bg-[#2d333b] border border-[#30363d] rounded px-1.5 py-0.5 text-[#8b949e] transition-colors">
                  {a}
                </button>
              ))}
            </div>
            <div className="flex gap-1">
              <textarea
                value={input}
                onChange={e => setInput(e.target.value)}
                onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend() } }}
                placeholder="Ask or request changes..."
                rows={2}
                className="flex-1 bg-[#0d1117] border border-[#30363d] rounded-lg px-2 py-1.5 text-xs text-[#e6edf3] focus:outline-none focus:border-[#388bfd] resize-none"
              />
              <button onClick={handleSend} disabled={!input.trim() || streaming}
                className="self-end bg-[#388bfd] hover:bg-[#58a6ff] disabled:opacity-40 text-white rounded-lg px-2 py-1.5 text-xs transition-colors">
                ↑
              </button>
            </div>
          </div>
        </>
      )}

      {reportId && tab === 'annotations' && (
        <div className="flex-1 flex items-center justify-center text-[#484f58] text-xs text-center p-4">
          Click a section heading in the report to add a note
        </div>
      )}
    </div>
  )
}
