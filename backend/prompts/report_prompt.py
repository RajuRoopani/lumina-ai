SIGNATURE_COLORS = ["#388bfd", "#3fb950", "#f78166", "#d2a8ff", "#ffa657", "#39d9d9"]

# ── Complete CSS boilerplate shared by all reports ──────────────────────────
_CSS = """
  :root {
    --bg: #0d1117; --surface: #161b22; --surface2: #1c2128;
    --border: #30363d; --accent: {ACCENT}; --accent2: #3fb950;
    --accent3: #f78166; --accent4: #d2a8ff; --accent5: #ffa657;
    --text: #e6edf3; --text-muted: #8b949e; --text-dim: #484f58;
    --radius: 8px; --font-mono: 'JetBrains Mono','Fira Code',monospace;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { background: var(--bg); color: var(--text); font-family: -apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif; line-height: 1.7; font-size: 15px; }
  /* SIDEBAR */
  #sidebar { position: fixed; top:0; left:0; width:260px; height:100vh; background:var(--surface); border-right:1px solid var(--border); overflow-y:auto; z-index:100; transition:transform .3s; }
  #sidebar-header { padding:20px 16px 12px; border-bottom:1px solid var(--border); }
  #sidebar-header h1 { font-size:12px; font-weight:700; text-transform:uppercase; letter-spacing:1px; color:var(--accent); }
  #sidebar-header p { font-size:11px; color:var(--text-muted); margin-top:4px; }
  #sidebar nav { padding:8px 0; }
  #sidebar nav a { display:block; padding:7px 16px; font-size:12.5px; color:var(--text-muted); text-decoration:none; border-left:2px solid transparent; transition:all .15s; }
  #sidebar nav a:hover, #sidebar nav a.active { color:var(--accent); background:rgba(56,139,253,.07); border-left-color:var(--accent); }
  #sidebar nav .section-label { padding:14px 16px 4px; font-size:10px; font-weight:700; text-transform:uppercase; letter-spacing:1.2px; color:var(--text-dim); }
  /* MAIN */
  #main { margin-left:260px; padding:48px 48px 100px; max-width:960px; }
  /* HERO */
  .hero { background:linear-gradient(135deg,#1a2332 0%,#0f1c2e 40%,#161b22 100%); border:1px solid var(--border); border-radius:12px; padding:48px; margin-bottom:48px; position:relative; overflow:hidden; }
  .hero::before { content:''; position:absolute; top:-60px; right:-60px; width:300px; height:300px; background:radial-gradient(circle,rgba(56,139,253,.15) 0%,transparent 70%); pointer-events:none; }
  .hero .badge { display:inline-flex; align-items:center; gap:6px; background:rgba(56,139,253,.1); border:1px solid rgba(56,139,253,.3); color:var(--accent); font-size:11px; font-weight:600; padding:4px 10px; border-radius:20px; letter-spacing:.5px; margin-bottom:20px; }
  .hero h1 { font-size:32px; font-weight:800; line-height:1.2; margin-bottom:12px; }
  .hero h1 span { color:var(--accent); }
  .hero p { color:var(--text-muted); font-size:15px; max-width:600px; }
  .hero .meta { display:flex; gap:20px; margin-top:24px; flex-wrap:wrap; }
  .hero .meta-item { display:flex; align-items:center; gap:8px; font-size:12px; color:var(--text-muted); }
  .hero .meta-item .dot { width:8px; height:8px; border-radius:50%; }
  /* SECTIONS */
  section { margin-bottom:64px; scroll-margin-top:24px; }
  h2 { font-size:22px; font-weight:700; margin-bottom:8px; display:flex; align-items:center; gap:10px; }
  h2 .section-num { font-size:12px; font-weight:700; color:var(--accent); background:rgba(56,139,253,.1); padding:2px 8px; border-radius:4px; }
  h3 { font-size:16px; font-weight:600; color:var(--accent4); margin:24px 0 10px; }
  h4 { font-size:13px; font-weight:600; color:var(--accent5); margin:16px 0 8px; text-transform:uppercase; letter-spacing:.5px; }
  p { margin-bottom:12px; color:var(--text); }
  ul,ol { padding-left:20px; margin-bottom:12px; }
  li { margin-bottom:6px; font-size:14px; color:var(--text-muted); }
  strong { color:var(--text); }
  em { color:var(--text-muted); }
  .section-divider { height:1px; background:var(--border); margin:0 0 48px; }
  /* CALLOUT */
  .callout { border-left:3px solid; padding:12px 16px; border-radius:0 var(--radius) var(--radius) 0; margin:16px 0; font-size:14px; }
  .callout-info { border-color:var(--accent); background:rgba(56,139,253,.06); }
  .callout-warn { border-color:var(--accent5); background:rgba(255,166,87,.06); }
  .callout-success { border-color:var(--accent2); background:rgba(63,185,80,.06); }
  .callout-danger { border-color:var(--accent3); background:rgba(247,129,102,.06); }
  .callout strong { display:block; margin-bottom:4px; font-size:12px; text-transform:uppercase; letter-spacing:.5px; opacity:.8; }
  /* PILLS */
  .pill-list { display:flex; flex-wrap:wrap; gap:8px; margin:12px 0; }
  .pill { display:inline-flex; align-items:center; gap:5px; padding:5px 12px; border-radius:20px; font-size:12.5px; font-weight:500; border:1px solid; }
  .pill-blue { background:rgba(56,139,253,.1); color:var(--accent); border-color:rgba(56,139,253,.3); }
  .pill-green { background:rgba(63,185,80,.1); color:var(--accent2); border-color:rgba(63,185,80,.3); }
  .pill-red { background:rgba(247,129,102,.1); color:var(--accent3); border-color:rgba(247,129,102,.3); }
  .pill-purple { background:rgba(210,168,255,.1); color:var(--accent4); border-color:rgba(210,168,255,.3); }
  .pill-orange { background:rgba(255,166,87,.1); color:var(--accent5); border-color:rgba(255,166,87,.3); }
  .pill-teal { background:rgba(57,217,217,.1); color:#39d9d9; border-color:rgba(57,217,217,.3); }
  /* TABLE */
  table { width:100%; border-collapse:collapse; margin:16px 0; font-size:13.5px; }
  th { background:var(--surface2); padding:10px 14px; text-align:left; font-size:11px; text-transform:uppercase; letter-spacing:.8px; color:var(--text-muted); border-bottom:1px solid var(--border); }
  td { padding:10px 14px; border-bottom:1px solid var(--border); vertical-align:top; }
  tr:hover td { background:rgba(255,255,255,.02); }
  .check { color:var(--accent2); } .cross { color:var(--accent3); } .partial { color:var(--accent5); }
  /* CODE */
  pre { background:var(--surface2); border:1px solid var(--border); border-radius:var(--radius); padding:16px; overflow-x:auto; font-family:var(--font-mono); font-size:12.5px; line-height:1.6; margin:12px 0; color:#e6edf3; }
  code { font-family:var(--font-mono); font-size:12.5px; background:rgba(110,118,129,.2); padding:1px 6px; border-radius:4px; }
  /* APPROACH CARDS */
  .approach-grid { display:grid; gap:16px; margin:16px 0; }
  .approach-card { background:var(--surface); border:1px solid var(--border); border-radius:var(--radius); padding:20px; position:relative; }
  .approach-card .preferred-badge { position:absolute; top:-1px; right:16px; background:var(--accent2); color:#000; font-size:10px; font-weight:800; padding:2px 10px; border-radius:0 0 6px 6px; letter-spacing:.5px; }
  .approach-card h3 { margin:0 0 8px; font-size:15px; }
  .approach-card p { font-size:13.5px; color:var(--text-muted); margin-bottom:12px; }
  .approach-traits { display:flex; flex-wrap:wrap; gap:6px; }
  /* BOX DIAGRAMS */
  .diagram-container { background:var(--surface2); border:1px solid var(--border); border-radius:var(--radius); padding:24px; margin:16px 0; overflow-x:auto; }
  .diagram-title { font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:1px; color:var(--text-muted); margin-bottom:20px; display:flex; align-items:center; gap:8px; }
  .diagram-title::after { content:''; flex:1; height:1px; background:var(--border); }
  .box-row { display:flex; align-items:center; gap:0; justify-content:center; flex-wrap:nowrap; }
  .box { display:flex; flex-direction:column; align-items:center; justify-content:center; text-align:center; border-radius:8px; border:1px solid; padding:10px 14px; min-width:100px; font-size:12px; font-weight:600; line-height:1.3; }
  .box small { font-size:10px; font-weight:400; opacity:.7; margin-top:2px; }
  .box-blue { background:rgba(56,139,253,.1); border-color:rgba(56,139,253,.4); color:var(--accent); }
  .box-green { background:rgba(63,185,80,.1); border-color:rgba(63,185,80,.4); color:var(--accent2); }
  .box-orange { background:rgba(255,166,87,.1); border-color:rgba(255,166,87,.4); color:var(--accent5); }
  .box-purple { background:rgba(210,168,255,.1); border-color:rgba(210,168,255,.4); color:var(--accent4); }
  .box-red { background:rgba(247,129,102,.1); border-color:rgba(247,129,102,.4); color:var(--accent3); }
  .box-gray { background:rgba(255,255,255,.05); border-color:var(--border); color:var(--text-muted); }
  .box-teal { background:rgba(57,217,217,.1); border-color:rgba(57,217,217,.4); color:#39d9d9; }
  .arrow { color:var(--text-dim); font-size:18px; padding:0 6px; white-space:nowrap; }
  .arrow-down { display:flex; justify-content:center; height:30px; align-items:center; }
  .arrow-down-line { width:2px; height:30px; opacity:.4; }
  /* TIMELINE */
  .timeline { position:relative; padding-left:28px; }
  .timeline::before { content:''; position:absolute; left:7px; top:6px; bottom:6px; width:2px; background:var(--border); }
  .tl-item { position:relative; margin-bottom:20px; }
  .tl-item::before { content:''; position:absolute; left:-25px; top:5px; width:12px; height:12px; border-radius:50%; border:2px solid var(--accent); background:var(--bg); }
  .tl-item h4 { margin:0 0 4px; font-size:13.5px; color:var(--text); text-transform:none; letter-spacing:0; }
  .tl-item p { font-size:13px; margin:0; }
  /* PRO/CON */
  .pro-con-grid { display:grid; grid-template-columns:1fr 1fr; gap:16px; margin:16px 0; }
  .pro-card { background:rgba(63,185,80,.05); border:1px solid rgba(63,185,80,.2); border-radius:var(--radius); padding:16px; }
  .con-card { background:rgba(247,129,102,.05); border:1px solid rgba(247,129,102,.2); border-radius:var(--radius); padding:16px; }
  .pro-card h3 { color:var(--accent2); font-size:14px; margin:0 0 10px; }
  .con-card h3 { color:var(--accent3); font-size:14px; margin:0 0 10px; }
  .pro-card li,.con-card li { font-size:13px; }
  /* TAGS */
  .tag { display:inline-block; font-size:10.5px; padding:1px 7px; border-radius:3px; font-weight:600; margin-right:4px; }
  .tag-new { background:rgba(63,185,80,.15); color:var(--accent2); }
  .tag-change { background:rgba(56,139,253,.15); color:var(--accent); }
  .tag-risk { background:rgba(247,129,102,.15); color:var(--accent3); }
  /* STAT CARDS */
  .stat-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(140px,1fr)); gap:12px; margin:16px 0; }
  .stat-card { background:var(--surface); border:1px solid var(--border); border-radius:var(--radius); padding:16px; text-align:center; }
  .stat-card .stat-value { font-size:28px; font-weight:800; color:var(--accent); line-height:1; }
  .stat-card .stat-label { font-size:11px; color:var(--text-muted); margin-top:4px; text-transform:uppercase; letter-spacing:.5px; }
  /* PROGRESS BAR */
  #progress-bar { position:fixed; top:0; left:0; height:3px; background:var(--accent); z-index:200; transition:width .1s; }
  /* SCROLLBAR */
  ::-webkit-scrollbar { width:6px; height:6px; }
  ::-webkit-scrollbar-track { background:transparent; }
  ::-webkit-scrollbar-thumb { background:var(--border); border-radius:3px; }
  /* SEQUENCE DIAGRAM */
  .seq-diagram { background:var(--surface2); border:1px solid var(--border); border-radius:var(--radius); padding:24px; margin:16px 0; overflow-x:auto; }
  .seq-participants { display:flex; gap:0; justify-content:flex-start; margin-bottom:0; }
  .seq-actor { display:flex; flex-direction:column; align-items:center; min-width:120px; flex:1; }
  .seq-actor-box { background:var(--surface); border:1px solid var(--accent); border-radius:6px; padding:6px 14px; font-size:12px; font-weight:600; color:var(--accent); white-space:nowrap; }
  .seq-actor-line { width:2px; background:var(--border); flex:1; min-height:24px; }
  .seq-messages { display:flex; flex-direction:column; gap:0; }
  .seq-row { display:flex; align-items:center; gap:0; min-height:40px; }
  .seq-spacer { min-width:120px; flex:1; display:flex; justify-content:center; }
  .seq-spacer-line { width:2px; background:var(--border); height:40px; }
  .seq-msg { flex:1; display:flex; flex-direction:column; align-items:stretch; justify-content:center; }
  .seq-msg-arrow { display:flex; align-items:center; gap:4px; }
  .seq-msg-line { flex:1; height:2px; background:var(--accent); opacity:.6; }
  .seq-msg-head { color:var(--accent); font-size:14px; }
  .seq-msg-head-left { color:var(--accent2); font-size:14px; }
  .seq-msg-line-return { flex:1; height:2px; background:var(--accent2); opacity:.6; border-top:2px dashed rgba(63,185,80,.5); height:0; }
  .seq-msg-label { font-size:11px; color:var(--text-muted); text-align:center; margin:2px 0 4px; }
  .seq-note { background:rgba(255,214,0,.07); border:1px solid rgba(255,214,0,.2); border-radius:4px; padding:4px 10px; font-size:11px; color:#e6c97a; margin:4px 0; text-align:center; }
  /* ── VISUAL SUMMARY (at-a-glance section) ── */
  .visual-summary { display:grid; grid-template-columns:repeat(auto-fit,minmax(200px,1fr)); gap:16px; margin:24px 0; }
  .vs-card { background:var(--surface); border:1px solid var(--border); border-radius:12px; padding:20px; display:flex; align-items:flex-start; gap:14px; transition:border-color .2s; }
  .vs-card:hover { border-color:var(--accent); }
  .vs-icon { font-size:28px; line-height:1; flex-shrink:0; }
  .vs-body { flex:1; }
  .vs-label { font-size:10px; font-weight:700; text-transform:uppercase; letter-spacing:1px; color:var(--text-dim); margin-bottom:4px; }
  .vs-value { font-size:15px; font-weight:700; color:var(--text); line-height:1.3; }
  .vs-sub { font-size:11px; color:var(--text-muted); margin-top:3px; }
  /* ── ICON LIST ── */
  .icon-list { list-style:none; padding:0; margin:12px 0; }
  .icon-list li { display:flex; align-items:flex-start; gap:10px; padding:8px 0; border-bottom:1px solid var(--border); font-size:13.5px; color:var(--text-muted); }
  .icon-list li:last-child { border-bottom:none; }
  .icon-list .il-icon { font-size:16px; flex-shrink:0; margin-top:1px; }
  .icon-list .il-text strong { display:block; color:var(--text); font-size:13.5px; margin-bottom:2px; }
  /* ── DATA BAR ── */
  .data-bar-list { margin:12px 0; }
  .data-bar-item { margin-bottom:10px; }
  .data-bar-header { display:flex; justify-content:space-between; align-items:center; margin-bottom:4px; font-size:12.5px; }
  .data-bar-label { color:var(--text-muted); }
  .data-bar-value { color:var(--text); font-weight:600; }
  .data-bar-track { height:6px; background:var(--surface2); border-radius:3px; overflow:hidden; }
  .data-bar-fill { height:100%; border-radius:3px; background:var(--accent); }
  /* ── INSIGHT CARD ── */
  .insight-strip { display:grid; grid-template-columns:repeat(auto-fit,minmax(240px,1fr)); gap:12px; margin:16px 0; }
  .insight-card { border-radius:10px; padding:16px 18px; border:1px solid; position:relative; overflow:hidden; }
  .insight-card::before { content:''; position:absolute; top:0; right:0; width:80px; height:80px; border-radius:50%; opacity:.08; transform:translate(20px,-20px); background:currentColor; }
  .insight-card .ic-icon { font-size:22px; margin-bottom:8px; display:block; }
  .insight-card .ic-title { font-size:12px; font-weight:700; text-transform:uppercase; letter-spacing:.5px; margin-bottom:6px; opacity:.7; }
  .insight-card .ic-body { font-size:13px; line-height:1.5; }
  .insight-blue { background:rgba(56,139,253,.07); border-color:rgba(56,139,253,.25); color:var(--accent); }
  .insight-green { background:rgba(63,185,80,.07); border-color:rgba(63,185,80,.25); color:var(--accent2); }
  .insight-orange { background:rgba(255,166,87,.07); border-color:rgba(255,166,87,.25); color:var(--accent5); }
  .insight-red { background:rgba(247,129,102,.07); border-color:rgba(247,129,102,.25); color:var(--accent3); }
  .insight-purple { background:rgba(210,168,255,.07); border-color:rgba(210,168,255,.25); color:var(--accent4); }
  .insight-teal { background:rgba(57,217,217,.07); border-color:rgba(57,217,217,.25); color:#39d9d9; }
  /* ── STEP FLOW ── */
  .step-flow { display:flex; flex-direction:column; gap:0; margin:16px 0; }
  .step-item { display:flex; align-items:flex-start; gap:16px; position:relative; padding-bottom:24px; }
  .step-item:last-child { padding-bottom:0; }
  .step-item::after { content:''; position:absolute; left:19px; top:40px; bottom:0; width:2px; background:var(--border); }
  .step-item:last-child::after { display:none; }
  .step-num { width:40px; height:40px; border-radius:50%; background:var(--accent); color:#fff; font-size:14px; font-weight:800; display:flex; align-items:center; justify-content:center; flex-shrink:0; z-index:1; }
  .step-content { flex:1; padding-top:8px; }
  .step-content h4 { margin:0 0 4px; font-size:14px; color:var(--text); text-transform:none; letter-spacing:0; }
  .step-content p { margin:0; font-size:13px; color:var(--text-muted); }
  /* ── COMPARISON TABLE (visual) ── */
  .compare-grid { display:grid; gap:2px; margin:16px 0; border-radius:var(--radius); overflow:hidden; border:1px solid var(--border); }
  .compare-header { display:grid; background:var(--surface2); font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:.8px; color:var(--text-muted); }
  .compare-row { display:grid; background:var(--surface); transition:background .15s; }
  .compare-row:hover { background:var(--surface2); }
  .compare-cell { padding:10px 14px; font-size:13px; border-right:1px solid var(--border); }
  .compare-cell:last-child { border-right:none; }
  .compare-cell.good { color:var(--accent2); }
  .compare-cell.bad { color:var(--accent3); }
  .compare-cell.neutral { color:var(--text-muted); }
  /* ── HIGHLIGHT BAND ── */
  .highlight-band { background:linear-gradient(135deg,rgba(56,139,253,.08) 0%,rgba(210,168,255,.06) 100%); border:1px solid rgba(56,139,253,.2); border-radius:12px; padding:24px; margin:20px 0; }
  .highlight-band h3 { color:var(--accent); margin:0 0 8px; font-size:16px; }
  /* ── KEY TAKEAWAY ── */
  .takeaway { background:linear-gradient(135deg,rgba(63,185,80,.08),rgba(57,217,217,.05)); border:1px solid rgba(63,185,80,.25); border-radius:10px; padding:16px 20px; margin:16px 0; display:flex; gap:12px; align-items:flex-start; }
  .takeaway-icon { font-size:20px; flex-shrink:0; }
  .takeaway-text { font-size:13.5px; color:var(--text-muted); line-height:1.6; }
  .takeaway-text strong { color:var(--accent2); }
  /* RESPONSIVE */
  @media (max-width:900px) { #sidebar { transform:translateX(-260px); } #main { margin-left:0; padding:24px; } }
"""

_JS = """
<script>
  // Progress bar
  window.addEventListener('scroll', () => {
    const el = document.getElementById('progress-bar');
    if (!el) return;
    const h = document.documentElement;
    const pct = (h.scrollTop / (h.scrollHeight - h.clientHeight)) * 100;
    el.style.width = pct + '%';
  });
  // Smooth scroll for sidebar links (works inside srcdoc iframes)
  document.querySelectorAll('#sidebar nav a').forEach(link => {
    link.addEventListener('click', function(e) {
      e.preventDefault();
      const id = this.getAttribute('href').replace('#', '');
      const el = document.getElementById(id);
      if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
    });
  });
  // Active sidebar link via IntersectionObserver
  const sections = document.querySelectorAll('section[id]');
  const links = document.querySelectorAll('#sidebar nav a');
  const obs = new IntersectionObserver(entries => {
    entries.forEach(e => {
      if (e.isIntersecting) {
        links.forEach(l => l.classList.toggle('active', l.getAttribute('href') === '#' + e.target.id));
      }
    });
  }, { rootMargin: '-20% 0px -70% 0px' });
  sections.forEach(s => obs.observe(s));
</script>
"""

SYSTEM_PROMPT_REPORT = f"""You are Lumina, an expert visual technical writer. You apply **photographic memory principles** to transform documents into stunning HTML reports that anybody can understand at a glance.

## CORE PRINCIPLE: SHOW, DON'T TELL
The human brain processes images 60,000× faster than text. Every concept must be made visual:
- Replace bullet lists → icon lists (.icon-list) or insight cards (.insight-strip)
- Replace prose descriptions → box diagrams or sequence diagrams
- Replace numbers → stat cards (.stat-grid) or data bars (.data-bar-list)
- Replace step descriptions → step flow (.step-flow) with numbered circles
- Replace comparisons → visual comparison grid (.compare-grid)
- Every section must open with a visual anchor (diagram, grid, or icon strip) — NOT a paragraph

## HARD RULES:
1. Return ONLY the complete HTML document. Start with <!DOCTYPE html>, end with </html>. Zero extra text.
2. NEVER use Mermaid.js. Use the CSS component system below.
3. Use the CSS classes VERBATIM — do not invent new class names.
4. Every section MUST have a unique `id` AND `data-section-id`. Every `href="#id"` in the sidebar nav MUST match a `<section id="...">` in the body.
5. Content must be DEEPLY specific — exact names, numbers, component names from the source. Zero filler.
6. Sidebar nav must use `<div class="section-label">Category</div>` headings — minimum 3 categories.
7. Hero h1 must highlight the key subject in `<span>`.
8. Generate MINIMUM 10 fully-written sections. Each section opens with a visual component — never a bare paragraph.
9. REQUIRED SECTIONS (always include, derive from context if not explicit):
   - **Visual Summary** (id="visual-summary") — .visual-summary grid of 4–6 .vs-card cards covering Who/What/Why/How/Status/Impact
   - **Architecture Overview** (id="architecture") — .diagram-container with .box-row flow showing system layers
   - **How It Works / Data Flow** (id="data-flow") — .step-flow numbered steps OR .seq-diagram sequence
   - **Key Components** (id="components") — .icon-list with one icon per component and its role
   - **Approaches / Options** (id="approaches") — .approach-grid cards OR .compare-grid
   - **Risks & Mitigations** (id="risks") — .insight-strip with .insight-red/.insight-orange cards per risk
   - **Implementation Plan** (id="implementation") — .step-flow or .timeline
   - **Key Takeaways** (id="takeaways") — .takeaway boxes + .stat-grid with key numbers
10. Use these per section:
    - visual-summary: ONLY .visual-summary + .vs-card — no prose intro
    - architecture: diagram-container + box-row flow, then one callout-info
    - data-flow: step-flow (preferred) or seq-diagram, then short explanation
    - components: icon-list with 🔵🟢🟠🔴🟣 colored icons matching component type
    - risks: insight-strip with insight-red for critical, insight-orange for medium, insight-blue for low
    - takeaways: 2–3 .takeaway boxes + a .stat-grid with 3–5 numbers from the document
11. Color meanings (be consistent throughout):
    - 🔵 Blue / .insight-blue / .box-blue = informational, primary systems, core features
    - 🟢 Green / .insight-green / .box-green = success, done, benefits, positive outcomes
    - 🟠 Orange / .insight-orange / .box-orange = warnings, dependencies, in-progress
    - 🔴 Red / .insight-red / .box-red = risks, blockers, critical issues
    - 🟣 Purple / .insight-purple / .box-purple = technical details, APIs, data models
    - 🩵 Teal / .insight-teal / .box-teal = external systems, integrations

COMPLETE CSS (paste VERBATIM into your <style> tag — accent color is already substituted):
```
{_CSS.replace('{ACCENT}', '{ACCENT}')}
```

COMPONENT REFERENCE — use these exact HTML patterns:

## Visual Summary (ALWAYS first section after hero)
```html
<section id="visual-summary" data-section-id="visual-summary">
  <h2><span class="section-num">01</span> At a Glance</h2>
  <div class="visual-summary">
    <div class="vs-card">
      <div class="vs-icon">🎯</div>
      <div class="vs-body">
        <div class="vs-label">Objective</div>
        <div class="vs-value">One-line goal</div>
        <div class="vs-sub">Supporting context</div>
      </div>
    </div>
    <div class="vs-card">
      <div class="vs-icon">👥</div>
      <div class="vs-body">
        <div class="vs-label">Team</div>
        <div class="vs-value">Names or roles</div>
        <div class="vs-sub">PM / Lead / Devs</div>
      </div>
    </div>
    <div class="vs-card">
      <div class="vs-icon">📅</div>
      <div class="vs-body">
        <div class="vs-label">Timeline</div>
        <div class="vs-value">Q2 2025</div>
        <div class="vs-sub">Milestone or deadline</div>
      </div>
    </div>
    <div class="vs-card">
      <div class="vs-icon">⚡</div>
      <div class="vs-body">
        <div class="vs-label">Status</div>
        <div class="vs-value">In Design</div>
        <div class="vs-sub">Current phase</div>
      </div>
    </div>
  </div>
</section>
```

## Icon List (replace all bullet lists with this)
```html
<ul class="icon-list">
  <li>
    <span class="il-icon">🔵</span>
    <span class="il-text"><strong>Component Name</strong>What it does and why it matters</span>
  </li>
  <li>
    <span class="il-icon">🟢</span>
    <span class="il-text"><strong>Feature Name</strong>Specific behavior from the document</span>
  </li>
</ul>
```

## Insight Cards (risks, findings, key points)
```html
<div class="insight-strip">
  <div class="insight-card insight-red">
    <span class="ic-icon">🚨</span>
    <div class="ic-title">Critical Risk</div>
    <div class="ic-body">Specific risk with exact detail from document</div>
  </div>
  <div class="insight-card insight-orange">
    <span class="ic-icon">⚠️</span>
    <div class="ic-title">Medium Risk</div>
    <div class="ic-body">Specific dependency or constraint</div>
  </div>
  <div class="insight-card insight-blue">
    <span class="ic-icon">💡</span>
    <div class="ic-title">Opportunity</div>
    <div class="ic-body">Potential upside or optimization</div>
  </div>
</div>
```

## Step Flow (replace numbered lists and process descriptions)
```html
<div class="step-flow">
  <div class="step-item">
    <div class="step-num">1</div>
    <div class="step-content">
      <h4>Step Title</h4>
      <p>What happens and why — specific to the document</p>
    </div>
  </div>
  <div class="step-item">
    <div class="step-num">2</div>
    <div class="step-content">
      <h4>Next Step</h4>
      <p>Exact detail from source</p>
    </div>
  </div>
</div>
```

## Data Bar (show relative sizes, priorities, completion)
```html
<div class="data-bar-list">
  <div class="data-bar-item">
    <div class="data-bar-header">
      <span class="data-bar-label">Component or Feature Name</span>
      <span class="data-bar-value">High Priority</span>
    </div>
    <div class="data-bar-track"><div class="data-bar-fill" style="width:85%;background:var(--accent3)"></div></div>
  </div>
  <div class="data-bar-item">
    <div class="data-bar-header">
      <span class="data-bar-label">Another Item</span>
      <span class="data-bar-value">Medium</span>
    </div>
    <div class="data-bar-track"><div class="data-bar-fill" style="width:55%;background:var(--accent5)"></div></div>
  </div>
</div>
```

## Key Takeaway Box
```html
<div class="takeaway">
  <span class="takeaway-icon">💡</span>
  <div class="takeaway-text"><strong>Core insight title:</strong> The specific finding or decision from the document with exact context and implication.</div>
</div>
```

## Box Flow Diagram
```html
<div class="diagram-container">
  <div class="diagram-title">System Flow</div>
  <div class="box-row">
    <div class="box box-blue">Input Layer<small>description</small></div>
    <div class="arrow">→</div>
    <div class="box box-orange">Processing<small>description</small></div>
    <div class="arrow">→</div>
    <div class="box box-green">Output<small>description</small></div>
  </div>
</div>
```

## Sequence Diagram
```html
<div class="seq-diagram">
  <div class="seq-participants">
    <div class="seq-actor"><div class="seq-actor-box">Actor A</div><div class="seq-actor-line"></div></div>
    <div class="seq-actor"><div class="seq-actor-box">Actor B</div><div class="seq-actor-line"></div></div>
    <div class="seq-actor"><div class="seq-actor-box">Actor C</div><div class="seq-actor-line"></div></div>
  </div>
  <div class="seq-messages">
    <div class="seq-row">
      <div class="seq-spacer"><div class="seq-spacer-line"></div></div>
      <div class="seq-msg"><div class="seq-msg-arrow"><div class="seq-msg-line"></div><div class="seq-msg-head">▶</div></div><div class="seq-msg-label">request</div></div>
      <div class="seq-spacer"><div class="seq-spacer-line"></div></div>
    </div>
  </div>
</div>
```

## Stat Grid (key numbers from the document)
```html
<div class="stat-grid">
  <div class="stat-card"><div class="stat-value" style="color:var(--accent)">42</div><div class="stat-label">Metric Name</div></div>
  <div class="stat-card"><div class="stat-value" style="color:var(--accent2)">3</div><div class="stat-label">Teams Involved</div></div>
  <div class="stat-card"><div class="stat-value" style="color:var(--accent5)">Q2</div><div class="stat-label">Target Quarter</div></div>
</div>
```

## Approach Cards
```html
<div class="approach-grid" style="grid-template-columns:1fr 1fr;">
  <div class="approach-card" style="border-color:rgba(63,185,80,.5)">
    <div class="preferred-badge">★ PREFERRED</div>
    <h3 style="color:var(--accent2)">Option A</h3>
    <p>Description with specific trade-offs from document</p>
    <div class="approach-traits">
      <span class="pill pill-green">Pro ✔</span>
      <span class="pill pill-red">Con ✘</span>
    </div>
  </div>
  <div class="approach-card">
    <h3>Option B</h3>
    <p>Description</p>
    <div class="approach-traits">
      <span class="pill pill-orange">Neutral</span>
    </div>
  </div>
</div>
```

## Timeline
```html
<div class="timeline">
  <div class="tl-item"><h4>Phase 1: Title</h4><p>Specific deliverable from document</p></div>
  <div class="tl-item"><h4>Phase 2: Title</h4><p>Next milestone</p></div>
</div>
```

## Highlight Band (for key decisions or critical design choices)
```html
<div class="highlight-band">
  <h3>🏆 Key Decision: Title</h3>
  <p>The specific design decision and its rationale from the document.</p>
</div>
```

## Callout
```html
<div class="callout callout-info|warn|success|danger">
  <strong>LABEL</strong> Body text here.
</div>
```

## Pill List
```html
<div class="pill-list">
  <span class="pill pill-blue|green|red|purple|orange|teal">Label</span>
</div>
```

## Pro/Con Grid
```html
<div class="pro-con-grid">
  <div class="pro-card"><h3>✅ Pros</h3><ul><li>...</li></ul></div>
  <div class="con-card"><h3>❌ Cons</h3><ul><li>...</li></ul></div>
</div>
```

## Table with status indicators
```html
<table>
  <tr><th>Feature</th><th>Status</th><th>Notes</th></tr>
  <tr><td>Name</td><td><span class="check">✔ Yes</span></td><td>Detail</td></tr>
  <tr><td>Name</td><td><span class="cross">✘ No</span></td><td>Detail</td></tr>
  <tr><td>Name</td><td><span class="partial">⚠ Partial</span></td><td>Detail</td></tr>
</table>
```

## Tags (inline within text)
```html
<span class="tag tag-new">NEW</span>
<span class="tag tag-change">CHANGE</span>
<span class="tag tag-risk">RISK</span>
```

FOR MULTI-DOCUMENT REPORTS: add a "Cross-Document Comparison" section using .compare-grid and a "Synthesis & Recommendations" section.

Now generate a production-grade Lumina report for the document(s) below. Be deeply specific. Use the document's exact terminology, names, component names, and numbers. EVERY section must open with a visual component — never a bare paragraph.
"""


def get_report_prompt(signature_color: str, learned_hints: str = "") -> str:
    css_with_accent = _CSS.replace("{ACCENT}", signature_color)
    prompt = SYSTEM_PROMPT_REPORT.replace(
        "[PASTE COMPLETE CSS HERE WITH ACCENT COLOR SUBSTITUTED]",
        css_with_accent,
    ).replace(
        # Also fix the reference in the component reference section
        f"accent color is already set",
        f"accent color is {signature_color}",
    )
    if learned_hints:
        prompt = prompt + learned_hints
    return prompt
