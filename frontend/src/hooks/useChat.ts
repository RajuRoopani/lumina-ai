import { useState, useCallback, useEffect, useRef } from 'react'
import { useQuery } from '@tanstack/react-query'
import { api } from '../api/client'
import type { ChatMessage } from '../types'

export function useChat(reportId: string | undefined) {
  const [streaming, setStreaming] = useState(false)
  const [streamingText, setStreamingText] = useState('')
  // Local message list — seeded from server, then updated in-place
  const [localMessages, setLocalMessages] = useState<ChatMessage[]>([])
  const initializedRef = useRef<string | undefined>(undefined)

  const { data: serverMessages } = useQuery({
    queryKey: ['chat', reportId],
    queryFn: () => api.chat.getMessages(reportId!),
    enabled: !!reportId,
  })

  // Seed local messages from server when reportId changes or initial load
  useEffect(() => {
    if (serverMessages && reportId !== initializedRef.current) {
      setLocalMessages(serverMessages)
      initializedRef.current = reportId
    } else if (serverMessages && localMessages.length === 0) {
      setLocalMessages(serverMessages)
    }
  }, [serverMessages, reportId]) // eslint-disable-line react-hooks/exhaustive-deps

  // Reset when reportId changes
  useEffect(() => {
    if (reportId !== initializedRef.current) {
      setLocalMessages([])
      setStreamingText('')
      setStreaming(false)
      initializedRef.current = reportId
    }
  }, [reportId])

  const sendMessage = useCallback(async (
    message: string,
    onAction?: (action: Record<string, unknown>) => void,
  ) => {
    if (!reportId) return

    const tempUserId = `u-${Date.now()}`
    const userMsg: ChatMessage = {
      id: tempUserId,
      report_id: reportId,
      role: 'user',
      content: message,
      action_data: {},
      created_at: new Date().toISOString(),
    }

    // Append user message immediately — never removed until replaced by server version
    setLocalMessages(prev => [...prev, userMsg])
    setStreaming(true)
    setStreamingText('')

    const res = await api.chat.streamMessage(reportId, message)
    if (!res.body) {
      setStreaming(false)
      return
    }

    const reader = res.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''
    let fullText = ''

    const processPayload = (payload: Record<string, unknown>) => {
      if (payload.type === 'chunk') {
        const chunk = payload.text as string
        fullText += chunk
        setStreamingText(fullText)
      }
      if (payload.type === 'action' && onAction) {
        onAction(payload.action as Record<string, unknown>)
      }
      if (payload.type === 'done') {
        // Append final AI message to local list, clear streaming indicator
        const aiMsg: ChatMessage = {
          id: `a-${Date.now()}`,
          report_id: reportId,
          role: 'assistant',
          content: fullText,
          action_data: {},
          created_at: new Date().toISOString(),
        }
        setLocalMessages(prev => [...prev, aiMsg])
        setStreamingText('')
        setStreaming(false)
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
          try { processPayload(JSON.parse(line.slice(6))) } catch { /* skip */ }
        }
      }
      if (buffer.startsWith('data: ')) {
        try { processPayload(JSON.parse(buffer.slice(6))) } catch { /* skip */ }
      }
    } catch (err) {
      console.error('SSE stream error:', err)
      setStreaming(false)
    } finally {
      reader.releaseLock()
    }
  }, [reportId])

  return { messages: localMessages, streaming, streamingText, sendMessage }
}
