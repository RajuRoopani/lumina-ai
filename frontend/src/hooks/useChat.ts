import { useState, useCallback } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '../api/client'
import type { ChatMessage } from '../types'

export function useChat(reportId: string | undefined) {
  const qc = useQueryClient()
  const [streaming, setStreaming] = useState(false)
  const [streamingText, setStreamingText] = useState('')
  // Optimistic user message shown immediately on send, before server round-trip
  const [pendingUserMsg, setPendingUserMsg] = useState<ChatMessage | null>(null)

  const { data: serverMessages = [] } = useQuery({
    queryKey: ['chat', reportId],
    queryFn: () => api.chat.getMessages(reportId!),
    enabled: !!reportId,
  })

  // Merge optimistic user message with server messages (avoids blank flash)
  const messages: ChatMessage[] = pendingUserMsg
    ? [...serverMessages.filter(m => m.id !== pendingUserMsg.id), pendingUserMsg]
    : serverMessages

  const sendMessage = useCallback(async (
    message: string,
    onAction?: (action: Record<string, unknown>) => void,
  ) => {
    if (!reportId) return

    // Show user message immediately
    const tempId = `pending-${Date.now()}`
    setPendingUserMsg({
      id: tempId,
      report_id: reportId,
      role: 'user',
      content: message,
      action: undefined,
      action_data: {},
      created_at: new Date().toISOString(),
    })

    setStreaming(true)
    setStreamingText('')

    const res = await api.chat.streamMessage(reportId, message)
    if (!res.body) {
      setStreaming(false)
      setPendingUserMsg(null)
      return
    }

    const reader = res.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    const processPayload = (payload: Record<string, unknown>) => {
      if (payload.type === 'chunk') setStreamingText(t => t + (payload.text as string))
      if (payload.type === 'action' && onAction) onAction(payload.action as Record<string, unknown>)
      if (payload.type === 'done') {
        // Invalidate first, then clear optimistic state — prevents blank flash
        qc.invalidateQueries({ queryKey: ['chat', reportId] }).then(() => {
          setPendingUserMsg(null)
          setStreamingText('')
          setStreaming(false)
        })
      }
    }

    try {
      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() ?? ''
        for (const line of lines) {
          if (!line.startsWith('data: ')) continue
          try { processPayload(JSON.parse(line.slice(6))) } catch { /* skip malformed */ }
        }
      }
      // Flush remaining buffer
      if (buffer.startsWith('data: ')) {
        try { processPayload(JSON.parse(buffer.slice(6))) } catch { /* skip */ }
      }
    } catch (err) {
      console.error('SSE stream error:', err)
      setPendingUserMsg(null)
      setStreaming(false)
    } finally {
      reader.releaseLock()
    }
  }, [reportId, qc])

  return { messages, streaming, streamingText, sendMessage }
}
