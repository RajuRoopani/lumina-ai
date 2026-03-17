import { useState, useCallback } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '../api/client'
import type { ChatMessage } from '../types'

export function useChat(reportId: string | undefined) {
  const qc = useQueryClient()
  const [streaming, setStreaming] = useState(false)
  const [streamingText, setStreamingText] = useState('')

  const { data: messages = [] } = useQuery({
    queryKey: ['chat', reportId],
    queryFn: () => api.chat.getMessages(reportId!),
    enabled: !!reportId,
  })

  const sendMessage = useCallback(async (
    message: string,
    onAction?: (action: Record<string, unknown>) => void,
  ) => {
    if (!reportId) return
    setStreaming(true)
    setStreamingText('')

    const res = await api.chat.streamMessage(reportId, message)
    if (!res.body) { setStreaming(false); return }

    const reader = res.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    try {
      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() ?? ''
        for (const line of lines) {
          if (!line.startsWith('data: ')) continue
          try {
            const payload = JSON.parse(line.slice(6))
            if (payload.type === 'chunk') setStreamingText(t => t + payload.text)
            if (payload.type === 'action' && onAction) onAction(payload.action)
            if (payload.type === 'done') {
              setStreaming(false)
              setStreamingText('')
              qc.invalidateQueries({ queryKey: ['chat', reportId] })
            }
          } catch { /* skip malformed */ }
        }
      }
      // Flush remaining buffer (handles streams without trailing newline)
      if (buffer.startsWith('data: ')) {
        try {
          const payload = JSON.parse(buffer.slice(6))
          if (payload.type === 'chunk') setStreamingText(t => t + payload.text)
          if (payload.type === 'action' && onAction) onAction(payload.action)
          if (payload.type === 'done') {
            setStreaming(false)
            setStreamingText('')
            qc.invalidateQueries({ queryKey: ['chat', reportId] })
          }
        } catch { /* skip */ }
      }
    } catch (err) {
      console.error('SSE stream error:', err)
    } finally {
      setStreaming(false)
      reader.releaseLock()
    }
  }, [reportId, qc])

  return { messages, streaming, streamingText, sendMessage }
}
