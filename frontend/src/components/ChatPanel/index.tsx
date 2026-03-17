import React, { useState, useRef, useEffect, useCallback } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { useChat } from '../../hooks/useChat'
import { api } from '../../api/client'
import type { ChatMessage } from '../../types'

const QUICK_ACTIONS = [
  'Summarize key points',
  'List all risks',
  'Expand architecture section',
  'Add a comparison table',
  'What are the main components?',
]

interface Props {
  reportId: string | undefined
  onNewReport?: (reportId: string) => void
}

// ── Lightweight markdown → HTML renderer ─────────────────────────────────────
function renderMarkdown(raw: string): string {
  let s = raw

  // Fenced code blocks
  s = s.replace(/```(\w*)\n?([\s\S]*?)```/g, (_m, lang: string, code: string) => {
    const escaped = code.trim()
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    const langLabel = lang
      ? `<span style="display:block;color:#484f58;font-size:10px;margin-bottom:6px;font-family:'JetBrains Mono',monospace">${lang}</span>`
      : ''
    return `<pre style="background:#1c2128;border:1px solid #30363d;border-radius:6px;padding:12px 14px;overflow-x:auto;margin:8px 0;font-family:'JetBrains Mono','Fira Code',monospace;font-size:11.5px;line-height:1.6;color:#e6edf3;white-space:pre">${langLabel}${escaped}</pre>`
  })

  // Inline code
  s = s.replace(/`([^`\n]+)`/g, (_m, code: string) => {
    const escaped = code.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    return `<code style="font-family:'JetBrains Mono',monospace;font-size:11px;background:rgba(110,118,129,.25);padding:1px 5px;border-radius:3px;color:#e6edf3">${escaped}</code>`
  })

  // Bold
  s = s.replace(/\*\*([^*\n]+)\*\*/g, '<strong style="color:#e6edf3;font-weight:600">$1</strong>')
  // Italic
  s = s.replace(/\*([^*\n]+)\*/g, '<em style="color:#8b949e">$1</em>')

  // Headers
  s = s.replace(/^### (.+)$/gm, '<div style="font-size:11px;font-weight:700;color:#d2a8ff;margin:10px 0 4px;text-transform:uppercase;letter-spacing:.5px">$1</div>')
  s = s.replace(/^## (.+)$/gm, '<div style="font-size:12px;font-weight:700;color:#388bfd;margin:10px 0 5px">$1</div>')
  s = s.replace(/^# (.+)$/gm, '<div style="font-size:13px;font-weight:700;color:#e6edf3;margin:10px 0 5px">$1</div>')

  // Blockquote
  s = s.replace(/^> (.+)$/gm, '<div style="border-left:2px solid #388bfd;padding:3px 8px;background:rgba(56,139,253,.06);margin:4px 0;font-size:11.5px;color:#8b949e">$1</div>')

  // Bullet lists — collect consecutive lines
  s = s.replace(/((?:^[-*] .+\n?)+)/gm, (block) => {
    const items = block.replace(/^[-*] (.+)$/gm, '<li>$1</li>').trim()
    return `<ul style="padding-left:16px;margin:6px 0;list-style:disc">${items}</ul>`
  })
  // Numbered lists
  s = s.replace(/((?:^\d+\. .+\n?)+)/gm, (block) => {
    const items = block.replace(/^\d+\. (.+)$/gm, '<li>$1</li>').trim()
    return `<ol style="padding-left:16px;margin:6px 0">${items}</ol>`
  })

  // li styling
  s = s.replace(/<li>/g, '<li style="margin:2px 0;color:#cdd9e5;font-size:12px">')

  // Double newlines → paragraph breaks, single → <br>
  s = s.replace(/\n\n+/g, '<br/><br/>')
  s = s.replace(/\n/g, '<br/>')

  return s
}

// ── Message bubble ────────────────────────────────────────────────────────────
function MessageBubble({ m }: { m: ChatMessage }) {
  const isUser = m.role === 'user'
  return (
    <div className={`rounded-lg p-2 text-xs leading-relaxed ${
      isUser ? 'bg-[#0d1117] text-[#8b949e] ml-2' : 'bg-[#0f1a2e] border border-[#388bfd]/30 text-[#cdd9e5]'
    }`}>
      {isUser
        ? <span>{m.content}</span>
        : <span dangerouslySetInnerHTML={{ __html: renderMarkdown(m.content) }} />
      }
      {m.action && (
        <div className="mt-1.5 text-[10px] text-[#3fb950] border-t border-[#21262d] pt-1">
          ✓ {m.action === 'section_update' ? 'Section updated in report' : 'New report created'}
        </div>
      )}
    </div>
  )
}

// ── Main component ────────────────────────────────────────────────────────────
export function ChatPanel({ reportId, onNewReport }: Props) {
  const [tab, setTab] = useState<'chat' | 'annotations'>('chat')
  const [input, setInput] = useState('')
  const [updateFlash, setUpdateFlash] = useState<string | null>(null)
  const bottomRef = useRef<HTMLDivElement>(null)
  const panelRef = useRef<HTMLDivElement>(null)
  const qc = useQueryClient()

  // Resize — mutate DOM directly during drag for zero-jank performance
  const isDragging = useRef(false)
  const dragStartX = useRef(0)
  const dragStartW = useRef(256)

  const { messages, streaming, streamingText, sendMessage } = useChat(reportId)

  // ── Resize drag ────────────────────────────────────────────────────────────
  const onDragStart = useCallback((e: React.MouseEvent) => {
    if (!panelRef.current) return
    isDragging.current = true
    dragStartX.current = e.clientX
    dragStartW.current = panelRef.current.offsetWidth
    document.body.style.cursor = 'col-resize'
    document.body.style.userSelect = 'none'
    e.preventDefault()
  }, [])

  useEffect(() => {
    const onMove = (e: MouseEvent) => {
      if (!isDragging.current || !panelRef.current) return
      const delta = dragStartX.current - e.clientX
      const newW = Math.max(180, Math.min(520, dragStartW.current + delta))
      panelRef.current.style.width = newW + 'px'
    }
    const onUp = () => {
      if (!isDragging.current) return
      isDragging.current = false
      document.body.style.cursor = ''
      document.body.style.userSelect = ''
    }
    document.addEventListener('mousemove', onMove)
    document.addEventListener('mouseup', onUp)
    return () => {
      document.removeEventListener('mousemove', onMove)
      document.removeEventListener('mouseup', onUp)
    }
  }, [])

  // ── Action handler ─────────────────────────────────────────────────────────
  const handleAction = useCallback((action: Record<string, unknown>) => {
    if (action.action === 'section_update' && reportId) {
      const sectionId = action.section_id as string
      const html = action.html as string
      const summary = (action.summary as string) || `"${sectionId}" updated`

      api.reports.updateSection(reportId, sectionId, html)
        .then(() => {
          // Re-fetch report so ReportViewer re-renders the iframe with the updated section
          qc.invalidateQueries({ queryKey: ['report', reportId] })
          setUpdateFlash(summary)
          setTimeout(() => setUpdateFlash(null), 4000)
        })
        .catch(err => {
          console.error('Section update failed:', err)
          setUpdateFlash(`Error: ${err.message}`)
          setTimeout(() => setUpdateFlash(null), 4000)
        })
    }
  }, [reportId, qc])

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
    <div ref={panelRef} className="flex flex-row flex-shrink-0" style={{ width: 256 }}>
      {/* Drag handle */}
      <div
        onMouseDown={onDragStart}
        className="w-1 flex-shrink-0 cursor-col-resize hover:bg-[#388bfd]/60 bg-[#21262d] transition-colors"
        title="Drag to resize"
      />

      {/* Panel body */}
      <div className="flex-1 flex flex-col bg-[#161b22] border-l border-[#21262d] min-w-0">
        {/* Tab bar */}
        <div className="flex border-b border-[#21262d] flex-shrink-0">
          {(['chat', 'annotations'] as const).map(t => (
            <button key={t} onClick={() => setTab(t)}
              className={`flex-1 py-2 text-xs capitalize transition-colors ${
                tab === t ? 'text-[#e6edf3] border-b-2 border-[#388bfd]' : 'text-[#8b949e] hover:text-[#e6edf3]'
              }`}>{t === 'chat' ? '✦ Lumina AI' : '📌 Notes'}</button>
          ))}
        </div>

        {/* Update flash */}
        {updateFlash && (
          <div className="mx-2 mt-1.5 px-2 py-1 rounded text-[10px] bg-[#0d2b1a] border border-[#3fb950]/40 text-[#3fb950]">
            ✓ {updateFlash}
          </div>
        )}

        {!reportId && (
          <div className="flex-1 flex items-center justify-center text-[#484f58] text-xs text-center p-4">
            Generate a report to start chatting
          </div>
        )}

        {reportId && tab === 'chat' && (
          <>
            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-2 space-y-2 min-h-0">
              {messages.length === 0 && !streaming && (
                <div className="text-[#484f58] text-xs text-center pt-4">
                  Ask anything about this document
                </div>
              )}
              {messages.map((m: ChatMessage) => <MessageBubble key={m.id} m={m} />)}
              {streaming && streamingText && (
                <div className="bg-[#0f1a2e] border border-[#388bfd]/30 rounded-lg p-2 text-xs text-[#cdd9e5] leading-relaxed">
                  <span dangerouslySetInnerHTML={{ __html: renderMarkdown(streamingText) }} />
                  <span className="animate-pulse">▌</span>
                </div>
              )}
              <div ref={bottomRef} />
            </div>

            {/* Input area */}
            <div className="p-2 border-t border-[#21262d] space-y-1.5 flex-shrink-0">
              <div className="flex flex-wrap gap-1">
                {QUICK_ACTIONS.slice(0, 3).map(a => (
                  <button key={a} onClick={() => setInput(a)}
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
    </div>
  )
}
