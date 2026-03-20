import React, { useEffect, useRef, useState, useCallback } from 'react'
import { useQuery } from '@tanstack/react-query'
import { api } from '../../api/client'
import type { Report } from '../../types'

interface Props {
  reportId: string
  onReportLoaded?: (report: Report) => void
  iframeRef?: React.RefObject<HTMLIFrameElement | null>
}

export function ReportViewer({ reportId, onReportLoaded, iframeRef: externalRef }: Props) {
  const internalRef = useRef<HTMLIFrameElement>(null)
  const iframeRef = externalRef ?? internalRef
  const [copied, setCopied] = useState(false)

  const { data: report, isLoading } = useQuery({
    queryKey: ['report', reportId],
    queryFn: () => api.reports.get(reportId),
    enabled: !!reportId,
  })

  useEffect(() => {
    if (report) onReportLoaded?.(report)
  }, [report, onReportLoaded])

  const printToPdf = useCallback(() => {
    const win = iframeRef.current?.contentWindow
    if (!win) return
    const doc = win.document
    const style = doc.createElement('style')
    style.id = '__lumina-print-css__'
    style.textContent = `
      @media print {
        nav, aside, [class*="sidebar"], [class*="nav"], [class*="toc"],
        .progress-bar, #progress-bar, [id*="progress"] { display: none !important; }
        body { margin: 0 !important; padding: 1cm !important; background: #fff !important; color: #111 !important; font-size: 11pt !important; }
        a { color: inherit !important; text-decoration: none !important; }
        @page { margin: 1.5cm; size: A4; }
        * { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
      }
    `
    doc.head.appendChild(style)
    win.print()
    setTimeout(() => style.remove(), 1000)
  }, [iframeRef])

  const copyShareLink = () => {
    navigator.clipboard.writeText(window.location.origin + api.reports.shareUrl(reportId))
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  if (isLoading) return (
    <div className="flex-1 flex items-center justify-center text-[#8b949e]">
      Generating report...
    </div>
  )
  if (!report) return null

  return (
    <div className="flex-1 flex flex-col overflow-hidden">
      <div className="flex items-center gap-2 px-4 py-2 bg-[#161b22] border-b border-[#21262d] flex-shrink-0">
        <div className="flex-1 text-xs text-[#8b949e] truncate">
          <span style={{ color: report.signature_color }}>●</span> {report.title}
        </div>
        <button onClick={copyShareLink}
          className="text-xs bg-[#1c2128] hover:bg-[#2d333b] border border-[#30363d] rounded px-2 py-1 text-[#8b949e] transition-colors">
          {copied ? '✓ Copied!' : '🔗 Share'}
        </button>
        <a href={api.reports.exportUrl(reportId)} download
          className="text-xs bg-[#1c2128] hover:bg-[#2d333b] border border-[#30363d] rounded px-2 py-1 text-[#8b949e] transition-colors">
          ⬇ HTML
        </a>
        <button
          onClick={printToPdf}
          className="text-xs bg-[#1c2128] hover:bg-[#2d333b] border border-[#30363d] rounded px-2 py-1 text-[#8b949e] transition-colors"
        >
          🖨 PDF
        </button>
      </div>
      <iframe
        ref={iframeRef}
        srcDoc={report.html_content}
        className="flex-1 w-full border-none"
        title="Report"
        sandbox="allow-scripts allow-same-origin"
      />
    </div>
  )
}
