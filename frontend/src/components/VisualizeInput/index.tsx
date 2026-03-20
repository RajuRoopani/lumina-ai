import { useState, useRef, useCallback, KeyboardEvent } from 'react'

const SUGGESTIONS = [
  'merge sort with step-by-step example',
  'how TCP three-way handshake works',
  'binary search tree insertion',
  'consistent hashing in distributed systems',
  'React reconciliation and the virtual DOM',
  'how HTTPS and TLS work',
  'CAP theorem with examples',
  'dynamic programming — coin change problem',
  'Bloom filters explained visually',
  'database indexing with B-trees',
]

interface Props {
  onStart: (query: string) => void
  disabled?: boolean
}

export function VisualizeInput({ onStart, disabled }: Props) {
  const [query, setQuery] = useState('')
  const inputRef = useRef<HTMLInputElement>(null)

  const submit = useCallback(() => {
    const q = query.trim()
    if (!q || disabled) return
    onStart(q)
  }, [query, disabled, onStart])

  const onKey = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') submit()
  }

  return (
    <div className="flex-1 flex flex-col items-center justify-center gap-8 px-8 py-12 text-center">
      {/* Header */}
      <div className="flex flex-col items-center gap-3">
        <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-[#1a2d4e] to-[#161b22] border border-[#388bfd]/30 flex items-center justify-center text-3xl shadow-lg shadow-[#388bfd]/10">
          ✦
        </div>
        <h2 className="text-2xl font-bold text-[#e6edf3] tracking-tight">
          Visualize Any Concept
        </h2>
        <p className="text-[#8b949e] text-sm max-w-sm leading-relaxed">
          Type any algorithm, system, or concept. Get a beautiful interactive diagram
          you'll remember forever.
        </p>
      </div>

      {/* Input */}
      <div className="w-full max-w-xl flex flex-col gap-3">
        <div className="relative">
          <div className="absolute left-4 top-1/2 -translate-y-1/2 text-[#388bfd] text-lg pointer-events-none">
            ✦
          </div>
          <input
            ref={inputRef}
            value={query}
            onChange={e => setQuery(e.target.value)}
            onKeyDown={onKey}
            disabled={disabled}
            placeholder="e.g. merge sort, TCP handshake, B-trees, consistent hashing…"
            className="w-full bg-[#161b22] border border-[#30363d] focus:border-[#388bfd]/70 focus:ring-1 focus:ring-[#388bfd]/30 rounded-xl px-4 py-3.5 pl-10 text-[#e6edf3] placeholder-[#484f58] text-sm outline-none transition-all disabled:opacity-50"
          />
        </div>
        <button
          onClick={submit}
          disabled={!query.trim() || disabled}
          className="w-full bg-[#1a3a5c] hover:bg-[#1d4a75] border border-[#388bfd]/40 hover:border-[#388bfd]/70 text-[#388bfd] font-semibold text-sm rounded-xl px-6 py-3 transition-all disabled:opacity-40 disabled:cursor-not-allowed flex items-center justify-center gap-2"
        >
          <span className="text-base">✦</span>
          Generate Visual Explanation
        </button>
      </div>

      {/* Suggestions */}
      <div className="w-full max-w-xl">
        <p className="text-[#484f58] text-xs uppercase tracking-widest font-semibold mb-3">
          Try these
        </p>
        <div className="flex flex-wrap gap-2 justify-center">
          {SUGGESTIONS.map(s => (
            <button
              key={s}
              disabled={disabled}
              onClick={() => { setQuery(s); inputRef.current?.focus() }}
              className="text-xs text-[#8b949e] hover:text-[#388bfd] bg-[#161b22] hover:bg-[#1a2332] border border-[#30363d] hover:border-[#388bfd]/40 rounded-full px-3 py-1.5 transition-all disabled:opacity-40"
            >
              {s}
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}
