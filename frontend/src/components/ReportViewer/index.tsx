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
  const [exportingPdf, setExportingPdf] = useState(false)

  const { data: report, isLoading } = useQuery({
    queryKey: ['report', reportId],
    queryFn: () => api.reports.get(reportId),
    enabled: !!reportId,
  })

  useEffect(() => {
    if (report) onReportLoaded?.(report)
  }, [report, onReportLoaded])

  const exportPdf = useCallback(async () => {
    const iframe = iframeRef.current
    if (!iframe?.contentDocument?.body) return
    setExportingPdf(true)
    try {
      const [{ default: html2canvas }, { default: jsPDF }] = await Promise.all([
        import('html2canvas'),
        import('jspdf'),
      ])
      const body = iframe.contentDocument.body
      const canvas = await html2canvas(body, {
        scale: 2,
        useCORS: true,
        allowTaint: true,
        backgroundColor: '#0d1117',
        width: body.scrollWidth,
        height: body.scrollHeight,
        windowWidth: body.scrollWidth,
        windowHeight: body.scrollHeight,
      })
      const imgData = canvas.toDataURL('image/jpeg', 0.92)
      const pdf = new jsPDF({ orientation: 'portrait', unit: 'mm', format: 'a4' })
      const pageW = pdf.internal.pageSize.getWidth()
      const pageH = pdf.internal.pageSize.getHeight()
      const imgH = (canvas.height * pageW) / canvas.width
      let remaining = imgH
      let offset = 0
      pdf.addImage(imgData, 'JPEG', 0, offset, pageW, imgH)
      remaining -= pageH
      while (remaining > 0) {
        offset -= pageH
        pdf.addPage()
        pdf.addImage(imgData, 'JPEG', 0, offset, pageW, imgH)
        remaining -= pageH
      }
      const filename = report?.title
        ? report.title.replace(/[^a-z0-9\s_-]/gi, '').trim().replace(/\s+/g, '-').toLowerCase().slice(0, 50) + '.pdf'
        : 'report.pdf'
      pdf.save(filename)
    } finally {
      setExportingPdf(false)
    }
  }, [iframeRef, report?.title])

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
          onClick={exportPdf}
          disabled={exportingPdf}
          className="text-xs bg-[#1c2128] hover:bg-[#2d333b] border border-[#30363d] rounded px-2 py-1 text-[#8b949e] transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {exportingPdf ? '⏳ Generating…' : '⬇ PDF'}
        </button>
      </div>
      <iframe
        ref={iframeRef}
        srcDoc={report.html_content}
        className="flex-1 w-full border-none"
        title="Report"
        sandbox="allow-scripts allow-same-origin allow-modals"
      />
    </div>
  )
}
