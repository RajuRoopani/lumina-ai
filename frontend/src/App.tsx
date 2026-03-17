import { useState, useCallback, useRef } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { HistorySidebar } from './components/HistorySidebar'
import { UploadModal } from './components/UploadModal'
import { ReportViewer } from './components/ReportViewer'
import { ChatPanel } from './components/ChatPanel'
import { api } from './api/client'

export default function App() {
  const qc = useQueryClient()
  const iframeRef = useRef<HTMLIFrameElement | null>(null)
  const [showUpload, setShowUpload] = useState(false)
  const [selectedDocIds, setSelectedDocIds] = useState<Set<string>>(new Set())
  const [activeReportId, setActiveReportId] = useState<string | undefined>()
  const [generating, setGenerating] = useState(false)
  const [genProgress, setGenProgress] = useState('')

  const handleDocSelect = (id: string, checked: boolean) => {
    setSelectedDocIds(prev => {
      const next = new Set(prev)
      checked ? next.add(id) : next.delete(id)
      return next
    })
  }

  const hadError = useRef(false)

  const handleGenerateReport = useCallback(async () => {
    if (!selectedDocIds.size) return
    setGenerating(true)
    hadError.current = false
    setGenProgress('Starting...')
    const reader_holder: { reader?: ReadableStreamDefaultReader } = {}
    try {
      const res = await api.reports.generateStream(Array.from(selectedDocIds))
      if (!res.body) {
        hadError.current = true
        setGenProgress('Error: No response stream')
        return
      }
      const reader = res.body.getReader()
      reader_holder.reader = reader
      const decoder = new TextDecoder()
      let streamDone = false
      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        const text = decoder.decode(value, { stream: true })
        for (const line of text.split('\n')) {
          if (!line.startsWith('data: ')) continue
          try {
            const payload = JSON.parse(line.slice(6))
            if (payload.event === 'progress') setGenProgress(payload.data)
            if (payload.event === 'done') {
              setActiveReportId(payload.data.id)
              setSelectedDocIds(new Set())
              qc.invalidateQueries({ queryKey: ['reports'] })
              streamDone = true
            }
            if (payload.event === 'error') {
              hadError.current = true
              setGenProgress(`Error: ${payload.data}`)
            }
          } catch { /* skip malformed */ }
        }
        if (streamDone) break
      }
    } catch (err) {
      hadError.current = true
      console.error('Report generation error:', err)
      setGenProgress('Generation failed')
    } finally {
      reader_holder.reader?.releaseLock()
      setGenerating(false)
      if (!hadError.current) setGenProgress('')
    }
  }, [selectedDocIds, qc])

  return (
    <div className="flex h-screen overflow-hidden bg-[#0d1117] text-[#e6edf3]">
      <HistorySidebar
        selectedDocIds={selectedDocIds}
        onDocSelect={handleDocSelect}
        onReportOpen={setActiveReportId}
        onGenerateReport={handleGenerateReport}
        onUploadClick={() => setShowUpload(true)}
        activeReportId={activeReportId}
      />

      <main className="flex-1 flex overflow-hidden">
        {generating && (
          <div className="flex-1 flex flex-col items-center justify-center gap-4">
            <div className="text-[#388bfd] text-2xl animate-spin">⟳</div>
            <div className="text-[#8b949e] text-sm">{genProgress}</div>
          </div>
        )}
        {!generating && activeReportId && (
          <ReportViewer reportId={activeReportId} iframeRef={iframeRef} />
        )}
        {!generating && !activeReportId && (
          <div className="flex-1 flex flex-col items-center justify-center gap-4 text-center">
            <div className="text-5xl">📄</div>
            <h1 className="text-xl font-semibold text-[#e6edf3]">DocViz</h1>
            <p className="text-[#8b949e] text-sm max-w-xs">
              Upload documents, select one or more, then click<br />
              <span className="text-[#388bfd]">Generate Report</span> to create a rich visual analysis.
            </p>
            <button onClick={() => setShowUpload(true)}
              className="bg-[#238636] hover:bg-[#2ea043] text-white text-sm rounded-lg px-4 py-2 transition-colors">
              + Add Your First Document
            </button>
          </div>
        )}
      </main>

      <ChatPanel
        reportId={activeReportId}
        onNewReport={setActiveReportId}
        iframeRef={iframeRef}
      />

      {showUpload && <UploadModal onClose={() => setShowUpload(false)} />}
    </div>
  )
}
