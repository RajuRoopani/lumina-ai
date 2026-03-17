# ✦ Lumina — AI Document Intelligence

> Transform any document into a rich, interactive visual report. Chat with your documents. Expand sections with AI. Get smarter with every report.

![Lumina](https://img.shields.io/badge/AI-Powered-388bfd?style=flat-square) ![FastAPI](https://img.shields.io/badge/FastAPI-Backend-3fb950?style=flat-square) ![React](https://img.shields.io/badge/React-Frontend-61dafb?style=flat-square) ![Claude](https://img.shields.io/badge/Claude-Haiku-d2a8ff?style=flat-square)

---

## What is Lumina?

Lumina takes raw documents (PDFs, DOCX, URLs, text) and uses Claude AI to generate stunning, structured HTML reports — complete with architecture diagrams, sequence diagrams, timeline flows, comparison tables, stat grids, and more. A built-in AI chat panel lets you ask questions or request changes to any section in real time.

**Key features:**
- **Rich visual reports** — auto-generated with sidebars, progress bars, CSS diagrams, and structured sections
- **AI Chat** — ask questions or say "expand the architecture section" and watch it update live
- **Section editing** — Claude calls a native tool to rewrite any section with your requested changes
- **Retro loop** — system learns from every report and chat to progressively improve quality
- **Multi-document** — select multiple docs to generate comparison and synthesis reports

---

## Tech Stack

| Layer | Tech |
|-------|------|
| Backend | FastAPI, SQLAlchemy, SQLite |
| AI | Anthropic Claude (`claude-haiku-4-5`), native tool use |
| Frontend | React 19, Vite, TailwindCSS, @tanstack/react-query |
| Parsing | PyMuPDF, python-docx, BeautifulSoup4 |

---

## Getting Started

### Prerequisites
- Python 3.9+
- Node.js 18+
- Anthropic API key

### Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Set your API key
echo "ANTHROPIC_API_KEY=sk-ant-..." > .env

# Start server
python3 -m uvicorn main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:5173](http://localhost:5173)

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    React Frontend                        │
│  HistorySidebar │ ReportViewer (iframe) │ ChatPanel      │
└─────────────────┬───────────────────────┬───────────────┘
                  │ REST + SSE            │ SSE stream
┌─────────────────▼───────────────────────▼───────────────┐
│                  FastAPI Backend                         │
│  /api/documents │ /api/reports │ /api/chat               │
└─────────────────┬───────────────────────────────────────┘
                  │
┌─────────────────▼───────────────┐  ┌─────────────────────┐
│    Anthropic Claude API          │  │  SQLite + learnings  │
│    (report gen + chat tool use)  │  │  (retro loop data)   │
└──────────────────────────────────┘  └─────────────────────┘
```

### How Report Generation Works

1. Upload documents → text extracted (PDF/DOCX/URL)
2. Click **Generate Report** → SSE stream starts
3. Backend calls Claude with full CSS template + retro-loop hints
4. Claude writes a complete HTML page (sidebar, sections, diagrams)
5. Backend post-processes: strips orphan nav links, injects smooth-scroll JS
6. Report renders in sandboxed `<iframe srcDoc>`, sidebar navigation works via `scrollIntoView`

### How AI Chat Works

1. User types a message → backend calls Claude with report context + section IDs
2. If edit request → Claude calls native `update_section` tool (section_id + full HTML)
3. Backend saves updated HTML to DB → frontend invalidates React Query cache → iframe re-renders
4. Retro loop records which sections get updated most → future reports make those sections richer

---

## Visual Components

Reports use pure CSS components (no Mermaid, no external libraries):

- **Box diagrams** — horizontal/vertical flow with colored boxes and arrows
- **Sequence diagrams** — multi-actor message flows for API/system interactions
- **Timeline** — vertical step-by-step flows
- **Approach cards** — side-by-side option comparison with preferred badge
- **Stat grid** — KPI cards with large numbers
- **Pro/Con grid** — two-column pros and cons
- **Callouts** — info/warn/success/danger highlighted notes
- **Pills** — colored tag labels
- **Tables** — with ✔/✘/⚠ status indicators

---

## Retro Loop

Lumina gets smarter with each report:

```
Generate report → record section count + CSS class usage
Chat interaction → record which sections users edit
        ↓
_refresh_hints() derives actionable prompts:
  • "Use seq-diagram — it has never appeared"
  • "Make architecture section richer — users edit it most"
        ↓
get_prompt_hints() injects hints into next generation
```

Stats persist in `backend/learnings.json`.

---

## License

MIT
