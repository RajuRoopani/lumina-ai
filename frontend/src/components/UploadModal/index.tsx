import { useState, useRef, useCallback, useEffect } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { api } from '../../api/client'

interface Props { onClose: () => void }

export function UploadModal({ onClose }: Props) {
  const qc = useQueryClient()
  const [tab, setTab] = useState<'file' | 'url' | 'paste'>('file')
  const [url, setUrl] = useState('')
  const [paste, setPaste] = useState('')
  const [dragOver, setDragOver] = useState(false)
  const [status, setStatus] = useState<'idle' | 'uploading' | 'done' | 'error'>('idle')
  const [error, setError] = useState('')
  const fileRef = useRef<HTMLInputElement>(null)
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const dragCounterRef = useRef(0)

  useEffect(() => {
    return () => {
      if (timeoutRef.current) clearTimeout(timeoutRef.current)
    }
  }, [])

  const handleFiles = useCallback(async (files: FileList | null) => {
    if (!files?.length) return
    setStatus('uploading')
    try {
      await api.documents.uploadFiles(Array.from(files))
      qc.invalidateQueries({ queryKey: ['documents'] })
      setStatus('done')
      timeoutRef.current = setTimeout(onClose, 800)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Upload failed')
      setStatus('error')
    }
  }, [qc, onClose])

  const handleUrl = async () => {
    if (!url.trim()) return
    try {
      const parsed = new URL(url.trim())
      if (!['http:', 'https:'].includes(parsed.protocol)) {
        setError('Only http:// and https:// URLs are allowed')
        setStatus('error')
        return
      }
    } catch {
      setError('Please enter a valid URL')
      setStatus('error')
      return
    }
    setStatus('uploading')
    try {
      await api.documents.fetchUrl(url.trim())
      qc.invalidateQueries({ queryKey: ['documents'] })
      setStatus('done')
      timeoutRef.current = setTimeout(onClose, 800)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Fetch failed')
      setStatus('error')
    }
  }

  const handlePaste = async () => {
    if (!paste.trim()) return
    setStatus('uploading')
    try {
      await api.documents.paste(paste.trim())
      qc.invalidateQueries({ queryKey: ['documents'] })
      setStatus('done')
      timeoutRef.current = setTimeout(onClose, 800)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Save failed')
      setStatus('error')
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60" onClick={onClose}>
      <div className="bg-[#161b22] border border-[#30363d] rounded-xl w-[480px] p-5 shadow-2xl"
           onClick={e => e.stopPropagation()}>
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-[#e6edf3] font-semibold">Add Document</h2>
          <button onClick={onClose} aria-label="Close" className="text-[#8b949e] hover:text-[#e6edf3]">✕</button>
        </div>

        <div className="flex gap-1 mb-4 bg-[#0d1117] rounded-lg p-1">
          {(['file', 'url', 'paste'] as const).map(t => (
            <button key={t} onClick={() => { setTab(t); setStatus('idle'); setError('') }}
              className={`flex-1 py-1.5 text-xs rounded-md transition-colors capitalize ${
                tab === t ? 'bg-[#21262d] text-[#e6edf3]' : 'text-[#8b949e] hover:text-[#e6edf3]'
              }`}>{t === 'file' ? '📁 Upload File' : t === 'url' ? '🔗 URL' : '📋 Paste'}</button>
          ))}
        </div>

        {tab === 'file' && (
          <div
            onDragEnter={e => { e.preventDefault(); dragCounterRef.current++; setDragOver(true) }}
            onDragLeave={e => { e.preventDefault(); dragCounterRef.current--; if (dragCounterRef.current === 0) setDragOver(false) }}
            onDragOver={e => e.preventDefault()}
            onDrop={e => {
              e.preventDefault()
              dragCounterRef.current = 0
              setDragOver(false)
              handleFiles(e.dataTransfer.files)
            }}
            onClick={() => fileRef.current?.click()}
            className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
              dragOver ? 'border-[#388bfd] bg-[#0f1a2e]' : 'border-[#30363d] hover:border-[#388bfd]'
            }`}
          >
            <div className="text-3xl mb-2">📄</div>
            <div className="text-[#8b949e] text-sm">Drop files here or click to browse</div>
            <div className="text-[#484f58] text-xs mt-1">PDF, DOCX, MD, TXT, PNG, JPG — max 50MB</div>
            <input ref={fileRef} type="file" multiple className="hidden"
              accept=".pdf,.docx,.md,.txt,.png,.jpg,.jpeg,.gif,.webp"
              onChange={e => handleFiles(e.target.files)} />
          </div>
        )}

        {tab === 'url' && (
          <div className="space-y-2">
            <input value={url} onChange={e => setUrl(e.target.value)}
              placeholder="https://example.com/doc or Confluence URL..."
              className="w-full bg-[#0d1117] border border-[#30363d] rounded-lg px-3 py-2 text-[#e6edf3] text-sm focus:outline-none focus:border-[#388bfd]" />
            <button onClick={handleUrl} disabled={status === 'uploading'}
              className="w-full bg-[#238636] hover:bg-[#2ea043] disabled:opacity-50 text-white text-sm rounded-lg py-2 transition-colors">
              {status === 'uploading' ? 'Fetching...' : 'Fetch & Parse'}
            </button>
          </div>
        )}

        {tab === 'paste' && (
          <div className="space-y-2">
            <textarea value={paste} onChange={e => setPaste(e.target.value)} rows={8}
              placeholder="Paste any text, markdown, or document content..."
              className="w-full bg-[#0d1117] border border-[#30363d] rounded-lg px-3 py-2 text-[#e6edf3] text-sm font-mono focus:outline-none focus:border-[#388bfd] resize-none" />
            <button onClick={handlePaste} disabled={status === 'uploading'}
              className="w-full bg-[#238636] hover:bg-[#2ea043] disabled:opacity-50 text-white text-sm rounded-lg py-2 transition-colors">
              {status === 'uploading' ? 'Saving...' : 'Save Document'}
            </button>
          </div>
        )}

        {status === 'done' && <div className="mt-3 text-[#3fb950] text-sm text-center">✓ Document added successfully</div>}
        {status === 'error' && <div className="mt-3 text-[#f78166] text-sm text-center">{error}</div>}
      </div>
    </div>
  )
}
