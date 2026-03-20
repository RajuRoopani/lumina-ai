import { useState, useCallback, useRef } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { HistorySidebar } from './components/HistorySidebar'
import { UploadModal } from './components/UploadModal'
import { ReportViewer } from './components/ReportViewer'
import { ChatPanel } from './components/ChatPanel'
import { VisualizeInput } from './components/VisualizeInput'
import { api } from './api/client'

/** Shared SSE stream reader — returns the opened reportId on success */
async function readStream(
  res: Response,
  onProgress: (msg: string) => void,
  onError: (msg: string) => void,
): Promise<string | undefined> {
  if (!res.body) { onError('No response stream'); return }
  const reader = res.body.getReader()
  const decoder = new TextDecoder()
  let reportId: string | undefined
  try {
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      const text = decoder.decode(value, { stream: true })
      for (const line of text.split('\n')) {
        if (!line.startsWith('data: ')) continue
        try {
          const payload = JSON.parse(line.slice(6))
          if (payload.event === 'progress') onProgress(payload.data)
          if (payload.event === 'done')     reportId = payload.data.id
          if (payload.event === 'error')    onError(`Error: ${payload.data}`)
        } catch { /* skip malformed */ }
      }
      if (reportId) break
    }
  } finally {
    reader.releaseLock()
  }
  return reportId
}

export default function App() {
  const qc = useQueryClient()
  const iframeRef = useRef<HTMLIFrameElement | null>(null)

  const [showUpload, setShowUpload]     = useState(false)
  const [selectedDocIds, setSelectedDocIds] = useState<Set<string>>(new Set())
  const [activeReportId, setActiveReportId] = useState<string | undefined>()

  // Shared loading state for both report generation + visualization
  const [busy, setBusy]         = useState(false)
  const [busyMsg, setBusyMsg]   = useState('')
  const hadError = useRef(false)

  // Which "home" tab is shown when no report is active
  const [homeTab, setHomeTab] = useState<'docs' | 'visualize'>('docs')

  const handleDocSelect = (id: string, checked: boolean) => {
    setSelectedDocIds(prev => {
      const next = new Set(prev)
      checked ? next.add(id) : next.delete(id)
      return next
    })
  }

  const handleGenerateReport = useCallback(async () => {
    if (!selectedDocIds.size) return
    setBusy(true)
    hadError.current = false
    setBusyMsg('Starting…')
    try {
      const res = await api.reports.generateStream(Array.from(selectedDocIds))
      const id = await readStream(
        res,
        msg => setBusyMsg(msg),
        msg => { hadError.current = true; setBusyMsg(msg) },
      )
      if (id) {
        setActiveReportId(id)
        setSelectedDocIds(new Set())
        qc.invalidateQueries({ queryKey: ['reports'] })
      }
    } catch (err) {
      hadError.current = true
      setBusyMsg('Generation failed')
    } finally {
      setBusy(false)
      if (!hadError.current) setBusyMsg('')
    }
  }, [selectedDocIds, qc])

  const handleVisualize = useCallback(async (query: string) => {
    setBusy(true)
    hadError.current = false
    setBusyMsg(`✦ Building visualization…`)
    try {
      const res = await api.visualize.generateStream(query)
      const id = await readStream(
        res,
        msg => setBusyMsg(msg),
        msg => { hadError.current = true; setBusyMsg(msg) },
      )
      if (id) {
        setActiveReportId(id)
        qc.invalidateQueries({ queryKey: ['reports'] })
      }
    } catch (err) {
      hadError.current = true
      setBusyMsg('Visualization failed')
    } finally {
      setBusy(false)
      if (!hadError.current) setBusyMsg('')
    }
  }, [qc])

  return (
    <div className="flex h-screen overflow-hidden bg-[#0d1117] text-[#e6edf3]">
      <HistorySidebar
        selectedDocIds={selectedDocIds}
        onDocSelect={handleDocSelect}
        onReportOpen={setActiveReportId}
        onGenerateReport={handleGenerateReport}
        onUploadClick={() => setShowUpload(true)}
        activeReportId={activeReportId}
        onActiveReportDeleted={() => setActiveReportId(undefined)}
        onNavigateHome={() => setActiveReportId(undefined)}
      />

      <main className="flex-1 flex overflow-hidden">
        {/* Busy spinner (report gen or visualization) */}
        {busy && (
          <div className="flex-1 flex flex-col items-center justify-center gap-5">
            <div className="relative w-12 h-12">
              <div className="absolute inset-0 rounded-full border-2 border-[#388bfd]/20" />
              <div className="absolute inset-0 rounded-full border-2 border-t-[#388bfd] animate-spin" />
              <div className="absolute inset-0 flex items-center justify-center text-[#388bfd] text-lg">✦</div>
            </div>
            <div className="text-[#8b949e] text-sm max-w-xs text-center leading-relaxed">{busyMsg}</div>
          </div>
        )}

        {/* Active report viewer */}
        {!busy && activeReportId && (
          <ReportViewer reportId={activeReportId} iframeRef={iframeRef} />
        )}

        {/* Home screen — tabs: Docs | Visualize */}
        {!busy && !activeReportId && (
          <div className="flex-1 flex flex-col overflow-hidden">
            {/* Tab bar */}
            <div className="flex items-center gap-1 px-6 pt-5 pb-0 border-b border-[#21262d]">
              <button
                onClick={() => setHomeTab('docs')}
                className={`px-4 py-2 text-sm font-medium rounded-t-lg transition-colors ${
                  homeTab === 'docs'
                    ? 'text-[#e6edf3] border-b-2 border-[#388bfd] -mb-px'
                    : 'text-[#8b949e] hover:text-[#c9d1d9]'
                }`}
              >
                📄 Documents
              </button>
              <button
                onClick={() => setHomeTab('visualize')}
                className={`px-4 py-2 text-sm font-medium rounded-t-lg transition-colors flex items-center gap-1.5 ${
                  homeTab === 'visualize'
                    ? 'text-[#388bfd] border-b-2 border-[#388bfd] -mb-px'
                    : 'text-[#8b949e] hover:text-[#c9d1d9]'
                }`}
              >
                <span className="text-xs">✦</span> Visualize
              </button>
            </div>

            {/* Docs tab */}
            {homeTab === 'docs' && (
              <div className="flex-1 flex flex-col items-center justify-center gap-4 text-center px-8">
                <div className="text-5xl">✦</div>
                <h1 className="text-2xl font-bold text-[#e6edf3] tracking-tight">Lumina</h1>
                <p className="text-[#8b949e] text-xs font-medium uppercase tracking-widest mb-1">AI Document Intelligence</p>
                <p className="text-[#8b949e] text-sm max-w-xs">
                  Upload documents, select one or more, then click{' '}
                  <span className="text-[#388bfd]">Generate Report</span> to create a rich visual analysis.
                </p>
                <button
                  onClick={() => setShowUpload(true)}
                  className="bg-[#238636] hover:bg-[#2ea043] text-white text-sm rounded-lg px-4 py-2 transition-colors"
                >
                  + Add Your First Document
                </button>
                <button
                  onClick={() => setHomeTab('visualize')}
                  className="text-xs text-[#484f58] hover:text-[#388bfd] transition-colors mt-2"
                >
                  Or try ✦ Visualize — explain any concept with beautiful diagrams →
                </button>
              </div>
            )}

            {/* Visualize tab */}
            {homeTab === 'visualize' && (
              <VisualizeInput onStart={handleVisualize} disabled={busy} />
            )}
          </div>
        )}
      </main>

      <ChatPanel
        reportId={activeReportId}
        onNewReport={setActiveReportId}
      />

      {showUpload && <UploadModal onClose={() => setShowUpload(false)} />}
    </div>
  )
}
