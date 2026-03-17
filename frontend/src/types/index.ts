export interface Document {
  id: string
  filename: string
  source_type: 'pdf' | 'docx' | 'url' | 'markdown' | 'text' | 'image'
  source_url?: string
  file_path?: string
  extracted_text: string
  created_at: string
}

export interface ReportMeta {
  id: string
  title: string
  document_ids: string[]
  signature_color: string
  created_at: string
}

export interface Report extends ReportMeta {
  html_content: string
}

export interface ChatMessage {
  id: string
  report_id: string
  role: 'user' | 'assistant' | 'annotation'
  content: string
  action?: string
  action_data: Record<string, unknown>
  created_at: string
}

export interface SseProgressEvent { event: 'progress'; data: string }
export interface SseDoneEvent { event: 'done'; data: { id: string; title: string } }
export interface SseErrorEvent { event: 'error'; data: string }
export type SseEvent = SseProgressEvent | SseDoneEvent | SseErrorEvent
