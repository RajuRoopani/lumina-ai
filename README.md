<div align="center">

# ✦ Lumina

### AI Document Intelligence

**Transform any document into a rich, interactive engineering report — in seconds.**
Ask questions. Edit sections. Watch your report evolve in real time.

<br/>

[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React_19-20232A?style=for-the-badge&logo=react&logoColor=61DAFB)](https://react.dev)
[![Claude](https://img.shields.io/badge/Claude_AI-D97706?style=for-the-badge&logo=anthropic&logoColor=white)](https://anthropic.com)
[![TypeScript](https://img.shields.io/badge/TypeScript-3178C6?style=for-the-badge&logo=typescript&logoColor=white)](https://typescriptlang.org)

<br/>

![Lumina Demo](https://raw.githubusercontent.com/RajuRoopani/lumina-ai/main/docs/demo-placeholder.png)

</div>

---

## What is Lumina?

Most document tools let you read. **Lumina lets you understand.**

Drop in a PDF, DOCX, URL, or raw text. Lumina's AI engine (powered by Claude) instantly generates a **production-grade visual engineering report** — with a sidebar navigator, architecture diagrams, sequence flows, comparison tables, stat cards, timelines, and more. No templates. No manual formatting. Just intelligence.

Then **chat with your document**. Ask "what are the main risks?" and get a precise answer. Say "expand the architecture section and add a sequence diagram" and watch the report update live — right in front of you.

---

## ✦ Key Features

| Feature | Description |
|---------|-------------|
| **Instant Visual Reports** | Claude generates a complete, styled HTML report with sidebar, diagrams, and sections |
| **Live AI Chat** | Ask questions or request edits — responses stream in real time |
| **Section Editing** | Say "add a comparison table to the architecture section" — it just works |
| **Sequence Diagrams** | CSS-native API/system flow diagrams (no Mermaid, no external deps) |
| **Multi-Document Analysis** | Select multiple docs for comparison, synthesis, and cross-document insights |
| **Retro Loop** | System learns from every interaction and makes each report better than the last |
| **Smooth UX** | Optimistic chat rendering, drag-to-resize panel, progress bar, smooth scroll nav |

---

## Demo

```
Upload a 50-page system design doc
        ↓  3 seconds
Rich report with 10 sections:
  • Executive Summary with stat grid
  • Architecture diagram with box flows
  • Sequence diagram for API calls
  • Risk matrix with callout cards
  • Timeline of implementation phases
  • Comparison table of approaches
        ↓  ask AI
"Expand the architecture section and make it more visual"
        ↓  2 seconds
Section updated in place — iframe re-renders instantly
```

---

## Architecture

```
┌───────────────────────────────────────────────────────────────────┐
│                        React Frontend                              │
│                                                                    │
│  ┌─────────────────┐  ┌────────────────────┐  ┌───────────────┐  │
│  │  HistorySidebar  │  │   ReportViewer      │  │  ✦ Lumina AI  │  │
│  │  (docs/reports)  │  │   (srcdoc iframe)   │  │  (chat panel) │  │
│  └────────┬─────────┘  └────────┬───────────┘  └──────┬────────┘  │
└───────────┼─────────────────────┼────────────────────┼────────────┘
            │   REST              │  React Query        │  SSE stream
┌───────────▼─────────────────────▼────────────────────▼────────────┐
│                        FastAPI Backend                              │
│                                                                    │
│   /api/documents    /api/reports    /api/chat                      │
│   (upload/parse)    (gen/edit)      (stream/tool-use)              │
└───────────────────────────┬────────────────────────────────────────┘
                            │
              ┌─────────────┴───────────────┐
              │                             │
    ┌─────────▼──────────┐     ┌────────────▼──────────┐
    │  Claude claude-    │     │  SQLite + learnings.   │
    │  haiku-4-5         │     │  json (retro loop)     │
    │  (reports + chat)  │     │                        │
    └────────────────────┘     └───────────────────────┘
```

### Report Generation Pipeline

```
Document upload
    → text extraction (PyMuPDF / python-docx / BeautifulSoup)
    → Claude Haiku (16k tokens, full CSS template + retro hints injected)
    → post-process: strip orphan nav links, inject smooth-scroll JS
    → store in SQLite
    → render in sandboxed srcdoc iframe with IntersectionObserver nav
```

### AI Chat Pipeline

```
User message
    → optimistic render (shown instantly, no waiting)
    → Claude Haiku with report context + section IDs + tool definition
    → if edit request → update_section tool call (section_id + full HTML)
    → PATCH /api/reports/:id/section → DB updated
    → React Query invalidates → iframe re-renders
    → retro loop records: which sections users edit most
```

---

## Visual Component Library

Lumina reports use a **pure CSS component system** — no Mermaid, no external chart libs, no CDN dependencies. Everything works offline and in sandboxed iframes.

<table>
<tr>
<th>Component</th>
<th>CSS Class</th>
<th>Use When</th>
</tr>
<tr><td>Box Flow Diagram</td><td><code>.box-row .box .arrow</code></td><td>Service architecture, data flows</td></tr>
<tr><td>Sequence Diagram</td><td><code>.seq-diagram .seq-actor .seq-msg</code></td><td>API call chains, request/response flows</td></tr>
<tr><td>Timeline</td><td><code>.timeline .tl-item</code></td><td>Implementation phases, history</td></tr>
<tr><td>Approach Cards</td><td><code>.approach-card .preferred-badge</code></td><td>Comparing options with trade-offs</td></tr>
<tr><td>Stat Grid</td><td><code>.stat-grid .stat-card</code></td><td>KPIs, metrics, numbers that matter</td></tr>
<tr><td>Pro/Con Grid</td><td><code>.pro-con-grid .pro-card .con-card</code></td><td>Decision analysis</td></tr>
<tr><td>Callouts</td><td><code>.callout-info|warn|danger|success</code></td><td>Highlighted notes, warnings, tips</td></tr>
<tr><td>Pills</td><td><code>.pill .pill-blue|green|red|purple</code></td><td>Status tags, labels, categories</td></tr>
</table>

---

## Retro Loop

Lumina gets smarter with every report you generate.

```
After each report:
  → count sections, detect which CSS components were used

After each AI chat edit:
  → record which section was updated

Every few interactions, _refresh_hints() derives rules like:
  • "Average section count is 6 — target 9-12 for depth"
  • ".seq-diagram has never appeared — use it"
  • "Users edit 'architecture' most — make it rich upfront"

These hints are injected into the next report's system prompt.
Quality compounds over time.
```

Stats persist in `backend/learnings.json`.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **AI** | Anthropic Claude `claude-haiku-4-5`, native tool use |
| **Backend** | Python 3.9+, FastAPI, SQLAlchemy, SQLite |
| **Document Parsing** | PyMuPDF, python-docx, BeautifulSoup4, httpx |
| **Frontend** | React 19, TypeScript, Vite, TailwindCSS |
| **State / Fetching** | @tanstack/react-query, SSE streaming |

---

## Getting Started

### Prerequisites

- Python 3.9+
- Node.js 18+
- An [Anthropic API key](https://console.anthropic.com)

### 1. Backend

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Create .env
echo "ANTHROPIC_API_KEY=sk-ant-..." > .env

# Start
python3 -m uvicorn main:app --reload --port 8000
```

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173** ✦

---

## Project Structure

```
lumina-ai/
├── backend/
│   ├── main.py                   # FastAPI app
│   ├── models.py                 # SQLAlchemy ORM + Pydantic schemas
│   ├── database.py               # SQLite setup
│   ├── config.py                 # Environment config
│   ├── routers/
│   │   ├── documents.py          # Upload, list, delete docs
│   │   ├── reports.py            # Generate, view, update, delete reports
│   │   └── chat.py               # SSE chat stream + compare endpoint
│   ├── services/
│   │   ├── report_service.py     # Claude report generation + post-processing
│   │   ├── chat_service.py       # Claude chat with native tool use
│   │   └── learnings_service.py  # Retro loop — tracks stats, derives hints
│   ├── prompts/
│   │   ├── report_prompt.py      # Full CSS template + component reference
│   │   └── chat_prompt.py        # Chat system prompt with component guide
│   └── parsers/                  # PDF, DOCX, URL, text extractors
└── frontend/
    ├── src/
    │   ├── App.tsx               # Root layout + report generation flow
    │   ├── components/
    │   │   ├── HistorySidebar/   # Docs + reports list with delete
    │   │   ├── ReportViewer/     # Sandboxed iframe renderer
    │   │   └── ChatPanel/        # AI chat with resize + markdown rendering
    │   ├── hooks/
    │   │   └── useChat.ts        # Local message state + SSE streaming
    │   └── api/
    │       └── client.ts         # Typed API client
    └── index.html
```

---

## License

MIT — use it, fork it, build on it.

---

<div align="center">

**Built with [Claude](https://anthropic.com) · Powered by curiosity**

*✦ Lumina — because documents deserve better than ctrl+F*

</div>
