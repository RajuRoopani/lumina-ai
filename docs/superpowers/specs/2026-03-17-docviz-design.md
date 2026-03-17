# DocViz — Document to Rich Visual Report Converter
**Date:** 2026-03-17
**Status:** Approved
**Folder:** `/Users/rajuroopani/Work6/experiments/design-and-explore/`

---

## 1. Problem Statement

Engineers and knowledge workers receive documents in many formats (PDF, DOCX, URL, Markdown, images, raw text). Consuming and comparing them is slow and cognitively expensive. DocViz converts one or more documents into a beautiful, navigable rich-HTML report, maintains history of all uploads and generated reports, and provides an AI chat panel that can answer questions, compare documents, generate proposals, and inject new content (e.g. sequence diagrams) directly into the live report.

---

## 2. Core Features

| Feature | Description |
|---|---|
| Multi-format ingestion | PDF, DOCX, URL, Markdown, raw text paste, images (vision OCR) |
| Multi-doc selection | Select 1–N docs to generate a single combined report |
| Rich HTML report generation | Claude generates dark-themed, sidebar-navigated HTML using the rich-html-reports design system |
| Document & report history | All uploads and generated reports persisted, browsable in sidebar |
| AI chat — Q&A | Ask questions about document content; streamed answers |
| AI chat — editing | "Add a sequence diagram for the login flow" → Claude injects HTML into the report live |
| AI chat — comparison | "Compare these two docs and draft a new proposal" → new report section or standalone report |
| Annotations tab | Simple inline comments — click a section heading to add a note (stored in ChatMessage with role="annotation") |
| Export | Download the generated HTML as a self-contained file |

---

## 3. Architecture

```
┌─────────────────────────────────────────────────────┐
│                    Frontend (React)                  │
│  ┌──────────┐  ┌──────────────────┐  ┌───────────┐  │
│  │ History  │  │  Report Viewer   │  │ Chat      │  │
│  │ Sidebar  │  │ (iframe/srcdoc)  │  │ Panel     │  │
│  │          │  │ + Report Nav     │  │ SSE stream│  │
│  └──────────┘  └──────────────────┘  └───────────┘  │
└─────────────────────────┬───────────────────────────┘
                          │ REST + SSE
┌─────────────────────────┴───────────────────────────┐
│                 Backend (FastAPI)                    │
│  ┌──────────┐  ┌──────────┐  ┌────────────────────┐ │
│  │ Parsers  │  │ Report   │  │  Chat Service      │ │
│  │ PDF/DOCX │  │ Service  │  │  (Claude API SSE)  │ │
│  │ URL/Img  │  │ (Claude) │  │                    │ │
│  └──────────┘  └──────────┘  └────────────────────┘ │
│  ┌──────────────────────────────────────────────┐    │
│  │          SQLite + Local Filesystem           │    │
│  │  documents table · reports table · messages  │    │
│  └──────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────┘
```

---

## 4. Tech Stack

| Layer | Technology | Rationale |
|---|---|---|
| Backend | Python 3.12, FastAPI | Async, fast, best doc-parsing ecosystem |
| AI | Anthropic SDK (`claude-sonnet-4-6`) | Best at structured HTML generation |
| PDF parsing | PyMuPDF (`fitz`) | Structure-aware: headers, tables, lists |
| DOCX parsing | `python-docx` | Native DOCX object model |
| URL parsing | `httpx` + `BeautifulSoup4` | Async fetching + HTML extraction |
| Image OCR | Claude vision API | No extra library needed |
| Database | SQLite + SQLAlchemy | Zero-config persistence |
| Frontend | React 18 + TypeScript + Vite | Fast DX, type-safe |
| Styling (app chrome) | Tailwind CSS | Utility-first, fast to write |
| Report rendering | `<iframe srcdoc>` | Isolated CSS — report styles don't bleed into app |
| Diagrams | Mermaid.js (in report) | Claude generates `mermaid` code blocks; rendered client-side |
| Streaming | SSE (Server-Sent Events) | Simple, browser-native, no WebSocket overhead |

---

## 5. Folder Structure

```
design-and-explore/
├── backend/
│   ├── main.py                    # FastAPI app, CORS, startup
│   ├── database.py                # SQLAlchemy engine + session
│   ├── models.py                  # Document, Report, ChatMessage ORM models
│   ├── config.py                  # Settings (ANTHROPIC_API_KEY, paths)
│   ├── parsers/
│   │   ├── __init__.py
│   │   ├── pdf_parser.py          # PyMuPDF → structured text
│   │   ├── docx_parser.py         # python-docx → structured text
│   │   ├── url_parser.py          # httpx + BeautifulSoup → text
│   │   ├── image_parser.py        # Claude vision → text
│   │   └── text_parser.py         # Raw text / markdown passthrough
│   ├── services/
│   │   ├── __init__.py
│   │   ├── report_service.py      # Claude call → rich HTML report
│   │   └── chat_service.py        # Claude chat + SSE streaming
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── documents.py           # POST /documents, GET /documents
│   │   ├── reports.py             # POST /reports/generate, GET /reports, PATCH /reports/{id}/section
│   │   └── chat.py                # POST /chat/{report_id}/message (SSE), POST /chat/compare
│   ├── prompts/
│   │   ├── report_prompt.py       # System prompt for report generation
│   │   └── chat_prompt.py         # System prompt for chat + editing
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.tsx                # Root layout: 4-zone grid
│   │   ├── main.tsx
│   │   ├── components/
│   │   │   ├── HistorySidebar/    # Doc + report history list
│   │   │   ├── UploadModal/       # Drag-drop, URL input, paste, multi-select
│   │   │   ├── ReportViewer/      # iframe srcdoc, export button
│   │   │   ├── ChatPanel/         # SSE chat, annotations tab, quick actions
│   │   │   └── MultiDocSelector/  # Checkbox list to pick docs for report gen
│   │   ├── hooks/
│   │   │   ├── useDocuments.ts    # CRUD + upload
│   │   │   ├── useReports.ts      # generate, fetch, patch section
│   │   │   └── useChat.ts         # SSE streaming chat
│   │   ├── types/
│   │   │   └── index.ts           # Document, Report, ChatMessage types
│   │   └── api/
│   │       └── client.ts          # Typed fetch wrappers
│   ├── package.json
│   ├── vite.config.ts
│   ├── tsconfig.json
│   └── tailwind.config.js
├── .env.example
└── docs/superpowers/specs/2026-03-17-docviz-design.md
```

---

## 6. Data Models

### Document
```sql
id            TEXT PRIMARY KEY   -- UUID
filename      TEXT               -- original filename or URL
source_type   TEXT               -- pdf | docx | url | markdown | text | image
source_url    TEXT               -- if URL type
file_path     TEXT               -- local storage path
extracted_text TEXT              -- parsed plain text
metadata      TEXT               -- JSON: page count, word count, etc.
created_at    DATETIME
```

### Report
```sql
id            TEXT PRIMARY KEY   -- UUID
title         TEXT               -- AI-generated title
document_ids  TEXT               -- JSON array of document UUIDs
html_content  TEXT               -- full generated HTML
signature_color TEXT             -- hex, for the report's accent
created_at    DATETIME
```

### ChatMessage
```sql
id            TEXT PRIMARY KEY
report_id     TEXT               -- FK → Report
role          TEXT               -- user | assistant
content       TEXT
action        TEXT               -- null | section_update | new_report
action_data   TEXT               -- JSON: {section_id, html} or {report_html}
created_at    DATETIME
```

---

## 7. API Endpoints

All endpoints return `application/json` unless noted. Errors return `{"detail": "..."}` with appropriate HTTP status codes (400 bad request, 404 not found, 422 validation, 500 server error, 503 Claude unavailable).

**Documents**
| Method | Path | Response | Description |
|---|---|---|---|
| POST | `/api/documents/upload` | `Document[]` | Multipart upload; max 50MB per file; allowed: pdf, docx, md, txt, png, jpg, jpeg, gif, webp |
| POST | `/api/documents/fetch-url` | `Document` | Fetch + parse URL |
| POST | `/api/documents/paste` | `Document` | Save raw text or markdown |
| GET  | `/api/documents` | `Document[]` | List all, ordered by created_at desc |
| GET  | `/api/documents/{id}` | `Document` | Single document metadata + extracted text |
| DELETE | `/api/documents/{id}` | `204` | Remove doc + file from disk |

**Reports**
| Method | Path | Response | Description |
|---|---|---|---|
| POST | `/api/reports/generate` | SSE stream | Body: `{document_ids: string[]}`. Streams `{"event":"progress","data":"Parsing docs..."}` events, ends with `{"event":"done","data":{"id":"...","title":"..."}}` |
| GET  | `/api/reports` | `Report[]` | List all with metadata (no html_content) |
| GET  | `/api/reports/{id}` | `Report` | Full report including html_content |
| DELETE | `/api/reports/{id}` | `204` | Remove report |
| GET  | `/api/reports/{id}/export` | `text/html` file download | Self-contained HTML file |
| PATCH | `/api/reports/{id}/section` | `Report` | `{section_id: string, html: string}` → replace section HTML in-place |

**Chat**
| Method | Path | Response | Description |
|---|---|---|---|
| POST | `/api/chat/{report_id}/stream` | SSE stream | Body: `{message: string}`. Streams text chunks; ends with optional `{"event":"action","data":{...}}` |
| GET  | `/api/chat/{report_id}/messages` | `ChatMessage[]` | Full chat history for a report |
| POST | `/api/chat/compare` | SSE stream | Body: `{document_ids: string[], prompt: string}` → comparison report SSE |

**Share** (served by FastAPI, not the React SPA)
| Method | Path | Response | Description |
|---|---|---|---|
| GET | `/share/{id}` | `text/html` | Raw report HTML — self-contained, shareable link, no auth required |

---

## 8. Report Generation Prompt Strategy

Claude receives:
1. **System prompt** — instructs it to output a complete self-contained HTML file using the exact rich-html-reports CSS design system (CSS variables, component library, sidebar, hero, section numbers, Mermaid blocks)
2. **User message** — the extracted text of all selected documents, structured as `[DOC 1: filename]\n{text}\n[DOC 2: filename]\n{text}...`
3. **Instructions** — generate: hero block, sidebar nav, sections (overview, architecture/structure, key concepts, risks/issues, summary), use callouts, diagrams (Mermaid), pro/con grids, timelines where appropriate. Each diagram uses a `<div class="mermaid">` block.

The report HTML includes Mermaid.js from CDN, so diagrams render client-side inside the iframe.

---

## 8b. Section ID Scheme

All `<section>` elements in the generated HTML carry a `data-section-id` attribute matching the sidebar anchor:

```html
<section id="overview" data-section-id="overview">
  <h2><span class="section-num">01</span> Overview</h2>
  ...
</section>
```

`PATCH /api/reports/{id}/section` receives `{section_id: "overview", html: "<section id=\"overview\" ...>...</section>"}`. The backend does a targeted string replace using a regex anchored to `data-section-id="{section_id}"` — replacing from the opening `<section` tag to the matching `</section>` close. The result is stored back to `html_content`.

The frontend reads the `section_id` from the SSE action payload and uses `postMessage` to the iframe to swap the section:
```js
iframe.contentWindow.postMessage({type: 'UPDATE_SECTION', sectionId, html}, '*')
```
The iframe listens and replaces the section element in-place without a full reload.

---

## 8c. Routing Strategy

- **FastAPI** owns `/api/*`, `/share/*` — mounted first.
- **React SPA** is served by FastAPI as a static mount at `/`. All unmatched routes return `index.html` (SPA catch-all).
- In development, Vite dev server proxies `/api/*` and `/share/*` to `localhost:8000`.
- Frontend React Router routes: `/` (home/upload), `/reports/{id}` (full app, report loaded), `/share/{id}` is **not** a React route — FastAPI serves it directly as raw HTML.

---

## 8d. Upload Security

- Max file size: 50MB (enforced in FastAPI dependency).
- Allowed MIME types allowlist: `application/pdf`, `application/vnd.openxmlformats-officedocument.wordprocessingml.document`, `text/markdown`, `text/plain`, `image/png`, `image/jpeg`, `image/gif`, `image/webp`.
- Filenames are sanitized with `werkzeug.utils.secure_filename` before writing to disk. Files stored as `uploads/{uuid}.{ext}` — original filename only in the DB, never used as a path.
- `ANTHROPIC_API_KEY` is server-only, never sent to the browser. Frontend config is limited to `VITE_API_BASE_URL`.

---

## 9. Chat + Editing Protocol

Chat messages carry intent detection:

| Intent | Trigger phrases | Action |
|---|---|---|
| Q&A | "what", "how", "why", "explain" | Text answer only |
| Section edit | "add", "insert", "update section", "change" | Returns `{action: "section_update", section_id, html}` |
| New report | "compare", "draft a proposal", "generate new" | Returns `{action: "new_report", html}` |
| Summarize | "summarize", "tldr", "key points" | Text answer only |

The frontend reads the `action` field in the SSE `data:` payload and either: injects the new section HTML into the iframe, or creates a new report entry.

---

## 10. Multi-Doc Comparison Flow

1. User selects 2+ docs in the History Sidebar via checkboxes
2. Clicks "Generate Combined Report" or types in chat: "Compare these docs and propose a new architecture"
3. Backend sends all doc texts to Claude with comparison instructions
4. Claude generates a report with sections: Per-Document Analysis, Side-by-Side Comparison, Synthesis / New Proposal, Recommendations
5. Stored as a new Report linked to all selected document IDs

---

## 11. Design System Compliance

The generated HTML reports use the **exact** rich-html-reports design system:
- CSS variables: `--bg: #0d1117`, `--surface: #161b22`, `--border: #30363d`, etc.
- Per-report signature color (Claude picks from: `#388bfd`, `#3fb950`, `#f78166`, `#d2a8ff`, `#ffa657`, `#39d9d9`)
- Fixed 260px sidebar + `margin-left: 260px` main, `max-width: 960px`
- Progress bar fixed at top (3px)
- Components: callouts, diagram-container, timeline, pro-con-grid, cost-summary-bar, pills
- Intersection Observer for active sidebar link
- Mermaid.js CDN script tag in `<head>` for diagram rendering
- `<script type="module">` Mermaid init block

---

## 12. Shareable Report URLs

Every generated report has a UUID (e.g. `a3f2b1c4-...`). Two URL modes:

| URL | Experience |
|---|---|
| `/reports/{id}` | Full app with history sidebar + chat panel, report pre-loaded |
| `/share/{id}` | **Standalone view** — just the rich HTML report, no app chrome. Safe to share with anyone, no login required. |

The `/share/{id}` route is served directly by FastAPI as the raw HTML content (the report's `html_content` field), so the recipient sees the exact same beautiful dark-themed report with full sidebar navigation and Mermaid diagrams — no app needed.

The Chat Panel in the full app shows a **"Copy share link"** button that copies `http://localhost:5173/share/{id}` (configurable via `PUBLIC_BASE_URL` env var for production deployments).

---

## 13. Success Criteria

- [ ] Upload a PDF → rich HTML report generated within 30s
- [ ] Paste a URL → report generated from fetched content
- [ ] Upload 2 PDFs → combined comparison report with synthesis section
- [ ] Chat: "What are the key risks?" → streamed AI answer in < 3s
- [ ] Chat: "Add a sequence diagram for user registration" → diagram injected into report live
- [ ] Chat: "Compare these two docs and propose a new design" → new report section created
- [ ] All docs and reports visible in history sidebar, clickable to reload
- [ ] Generated HTML is exportable as a standalone self-contained file
- [ ] App works end-to-end with `python -m uvicorn main:app` + `npm run dev`
