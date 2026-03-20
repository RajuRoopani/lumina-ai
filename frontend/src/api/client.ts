import type { Document, Report, ReportMeta, ChatMessage } from '../types'

const BASE = '/api'

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const headers: Record<string, string> = { ...init?.headers as Record<string, string> }
  if (init?.body) headers['Content-Type'] = 'application/json'
  const res = await fetch(`${BASE}${path}`, { ...init, headers })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail ?? 'Request failed')
  }
  return res.json()
}

async function deleteRequest(path: string): Promise<void> {
  const res = await fetch(`${BASE}${path}`, { method: 'DELETE' })
  if (!res.ok && res.status !== 204) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail ?? 'Delete failed')
  }
}

export const api = {
  documents: {
    list: () => request<Document[]>('/documents'),
    get: (id: string) => request<Document>(`/documents/${id}`),
    fetchUrl: (url: string) => request<Document>('/documents/fetch-url', {
      method: 'POST', body: JSON.stringify({ url }),
    }),
    paste: (content: string, filename?: string) =>
      request<Document>('/documents/paste', {
        method: 'POST', body: JSON.stringify({ content, filename }),
      }),
    delete: (id: string) => deleteRequest(`/documents/${id}`),
    uploadFiles: async (files: File[]): Promise<Document[]> => {
      const form = new FormData()
      files.forEach(f => form.append('files', f))
      const res = await fetch(`${BASE}/documents/upload`, { method: 'POST', body: form })
      if (!res.ok) throw new Error(await res.text())
      return res.json()
    },
  },
  reports: {
    list: () => request<ReportMeta[]>('/reports'),
    get: (id: string) => request<Report>(`/reports/${id}`),
    delete: (id: string) => deleteRequest(`/reports/${id}`),
    exportUrl: (id: string) => `${BASE}/reports/${id}/export`,
    shareUrl: (id: string) => `/share/${id}`,
    generateStream: (documentIds: string[]) =>
      fetch(`${BASE}/reports/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ document_ids: documentIds }),
      }),
    updateSection: (reportId: string, sectionId: string, html: string) =>
      request<Report>(`/reports/${reportId}/section`, {
        method: 'PATCH',
        body: JSON.stringify({ section_id: sectionId, html }),
      }),
  },
  visualize: {
    generateStream: (query: string) =>
      fetch(`${BASE}/visualize/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query }),
      }),
  },
  chat: {
    getMessages: (reportId: string) => request<ChatMessage[]>(`/chat/${reportId}/messages`),
    streamMessage: (reportId: string, message: string) =>
      fetch(`${BASE}/chat/${reportId}/stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message }),
      }),
    compareStream: (documentIds: string[], prompt: string) =>
      fetch(`${BASE}/chat/compare`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ document_ids: documentIds, prompt }),
      }),
  },
}
