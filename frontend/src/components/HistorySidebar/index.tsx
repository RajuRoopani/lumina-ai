import { useState } from 'react'
import { useDocuments } from '../../hooks/useDocuments'
import { useReports } from '../../hooks/useReports'
import type { Document, ReportMeta } from '../../types'

const SOURCE_ICON: Record<string, string> = {
  pdf: '📄', docx: '📃', url: '🔗', markdown: '📝', text: '📋', image: '🖼️',
}

interface Props {
  selectedDocIds: Set<string>
  onDocSelect: (id: string, checked: boolean) => void
  onReportOpen: (id: string) => void
  onGenerateReport: () => void
  onUploadClick: () => void
  activeReportId?: string
}

export function HistorySidebar({
  selectedDocIds, onDocSelect, onReportOpen, onGenerateReport, onUploadClick, activeReportId
}: Props) {
  const { documents } = useDocuments()
  const { reports } = useReports()
  const [tab, setTab] = useState<'docs' | 'reports'>('docs')

  return (
    <aside className="w-52 flex-shrink-0 bg-[#0d1117] border-r border-[#21262d] flex flex-col h-full">
      <div className="p-3 border-b border-[#21262d]">
        <div className="text-[#e6edf3] font-bold text-sm mb-2">DocViz</div>
        <button
          onClick={onUploadClick}
          className="w-full bg-[#238636] hover:bg-[#2ea043] text-white text-xs rounded-md py-1.5 px-2 transition-colors"
        >
          + New Document
        </button>
        {selectedDocIds.size > 0 && (
          <button
            onClick={onGenerateReport}
            className="w-full mt-1 bg-[#388bfd] hover:bg-[#58a6ff] text-white text-xs rounded-md py-1.5 px-2 transition-colors"
          >
            Generate Report ({selectedDocIds.size})
          </button>
        )}
      </div>

      <div className="flex border-b border-[#21262d]">
        {(['docs', 'reports'] as const).map(t => (
          <button key={t} onClick={() => setTab(t)}
            className={`flex-1 py-1.5 text-xs capitalize transition-colors ${
              tab === t ? 'text-[#e6edf3] border-b-2 border-[#388bfd]' : 'text-[#8b949e] hover:text-[#e6edf3]'
            }`}>
            {t === 'docs' ? `Docs (${documents.length})` : `Reports (${reports.length})`}
          </button>
        ))}
      </div>

      <div className="flex-1 overflow-y-auto p-2 space-y-1">
        {tab === 'docs' && documents.map((doc: Document) => (
          <label key={doc.id}
            className={`flex items-start gap-2 rounded-md p-2 cursor-pointer border transition-colors ${
              selectedDocIds.has(doc.id)
                ? 'bg-[#161b22] border-[#388bfd]'
                : 'border-transparent hover:bg-[#161b22] hover:border-[#30363d]'
            }`}
          >
            <input type="checkbox" className="mt-0.5 accent-[#388bfd]"
              checked={selectedDocIds.has(doc.id)}
              onChange={e => onDocSelect(doc.id, e.target.checked)} />
            <div className="min-w-0">
              <div className="text-[10px] text-[#8b949e] truncate">
                {SOURCE_ICON[doc.source_type]} {doc.filename}
              </div>
              <div className="text-[9px] text-[#484f58]">
                {new Date(doc.created_at).toLocaleDateString()}
              </div>
            </div>
          </label>
        ))}

        {tab === 'reports' && reports.map((r: ReportMeta) => (
          <button key={r.id} onClick={() => onReportOpen(r.id)}
            className={`w-full text-left rounded-md p-2 border transition-colors ${
              activeReportId === r.id
                ? 'bg-[#161b22] border-[#388bfd]'
                : 'border-transparent hover:bg-[#161b22] hover:border-[#30363d]'
            }`}
          >
            <div className="flex items-center gap-1 mb-0.5">
              <div className="w-2 h-2 rounded-full flex-shrink-0"
                style={{ background: r.signature_color }} />
              <div className="text-[10px] text-[#e6edf3] truncate">{r.title}</div>
            </div>
            <div className="text-[9px] text-[#484f58]">
              {new Date(r.created_at).toLocaleDateString()} · {r.document_ids.length} doc{r.document_ids.length > 1 ? 's' : ''}
            </div>
          </button>
        ))}
      </div>
    </aside>
  )
}
