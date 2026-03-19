import re
import anthropic
from models import DocumentORM
from prompts.report_prompt import get_report_prompt, SIGNATURE_COLORS
from config import ANTHROPIC_API_KEY
from services.learnings_service import get_prompt_hints, record_report_generation

# Docs under this threshold are sent directly; larger docs are chunked + summarized
LARGE_DOC_THRESHOLD = 12_000   # chars
SUMMARY_CHUNK_SIZE  = 80_000   # chars per chunk (~20k tokens)


def pick_signature_color(report_index: int) -> str:
    return SIGNATURE_COLORS[report_index % len(SIGNATURE_COLORS)]


def make_client() -> anthropic.Anthropic:
    if not ANTHROPIC_API_KEY:
        raise ValueError("ANTHROPIC_API_KEY is not configured")
    return anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


def split_into_chunks(text: str, chunk_size: int = SUMMARY_CHUNK_SIZE) -> list:
    """Split text into chunks, preferring paragraph boundaries."""
    chunks: list = []
    while len(text) > chunk_size:
        # Prefer splitting at double newline (paragraph boundary)
        split_at = text.rfind('\n\n', 0, chunk_size + 3000)
        if split_at < chunk_size // 2:
            split_at = text.rfind('\n', 0, chunk_size + 500)
        if split_at < chunk_size // 2:
            split_at = chunk_size
        chunks.append(text[:split_at].strip())
        text = text[split_at:].strip()
    if text:
        chunks.append(text)
    return chunks


def summarize_chunk(client: anthropic.Anthropic, chunk: str, idx: int, total: int, doc_name: str) -> str:
    """Extract dense technical key points from one chunk of a large document."""
    resp = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=1200,
        messages=[{"role": "user", "content": (
            f"Extract ALL key technical concepts, architectural patterns, data structures, algorithms, "
            f"trade-offs, numbers/stats, and important insights from this section of '{doc_name}' "
            f"(section {idx} of {total}).\n\n"
            f"Be thorough and specific — include exact terminology, formulas, and real examples. "
            f"Organize by topic. Be dense, not verbose.\n\n"
            f"---\n{chunk}"
        )}]
    )
    return f"[Section {idx}/{total}]\n{resp.content[0].text}"


# Injected into every report before </body>
_NAV_FIX_JS = """<script>
(function() {
  // Smooth scroll — works inside sandboxed srcdoc iframes where href="#id" breaks
  document.querySelectorAll('#sidebar nav a').forEach(function(link) {
    link.addEventListener('click', function(e) {
      e.preventDefault();
      e.stopPropagation();
      var id = this.getAttribute('href').replace(/^#/, '');
      var target = document.getElementById(id);
      if (target) target.scrollIntoView({ behavior: 'smooth', block: 'start' });
    });
  });
  // Progress bar
  var bar = document.getElementById('progress-bar');
  if (bar) {
    window.addEventListener('scroll', function() {
      var h = document.documentElement;
      var pct = (h.scrollTop / (h.scrollHeight - h.clientHeight)) * 100;
      bar.style.width = pct + '%';
    });
  }
  // Active sidebar highlight
  var sections = document.querySelectorAll('section[id]');
  var links = document.querySelectorAll('#sidebar nav a');
  if (sections.length && links.length && window.IntersectionObserver) {
    var obs = new IntersectionObserver(function(entries) {
      entries.forEach(function(e) {
        if (e.isIntersecting) {
          links.forEach(function(l) {
            l.classList.toggle('active', l.getAttribute('href') === '#' + e.target.id);
          });
        }
      });
    }, { rootMargin: '-20% 0px -70% 0px' });
    sections.forEach(function(s) { obs.observe(s); });
  }
})();
</script>"""


def _fix_sections_outside_main(html: str) -> str:
    """Ensure all <section> elements are inside <div id="main">.

    Claude sometimes emits a premature </div> that closes #main, leaving the
    last N sections outside it (no margin-left → content renders behind sidebar).
    Strategy: collect every <section>...</section> block, remove them from their
    current positions, and re-inject them all inside #main before it closes.
    """
    main_open_tag = '<div id="main">'
    main_pos = html.find(main_open_tag)
    if main_pos == -1:
        return html

    # Find all complete section blocks
    section_pattern = re.compile(
        r'<section[^>]*data-section-id="[^"]*".*?</section>', re.DOTALL
    )
    sections = section_pattern.findall(html)
    if not sections:
        return html

    # Find position of last section end in the raw HTML
    last_section_end = 0
    for m in section_pattern.finditer(html):
        last_section_end = m.end()

    # Find the first </div> that appears AFTER #main opens but BEFORE the last section ends
    # — this is the premature closing div
    between = html[main_pos + len(main_open_tag): last_section_end]
    # Count opening vs closing divs to find where #main actually gets closed early
    depth = 0
    premature_close = -1
    i = 0
    while i < len(between):
        open_m = re.search(r'<div[^>]*>', between[i:])
        close_m = re.search(r'</div>', between[i:])
        if not close_m:
            break
        if open_m and open_m.start() < close_m.start():
            depth += 1
            i += open_m.start() + len(open_m.group(0))
        else:
            if depth == 0:
                # This </div> closes #main — it's premature if sections follow it
                abs_pos = main_pos + len(main_open_tag) + i + close_m.start()
                if abs_pos < last_section_end:
                    premature_close = abs_pos
                    # Remove this premature close and re-add it after the last section
                    html = html[:abs_pos] + html[abs_pos + 6:]  # remove </div>
                    # Now find updated last section end (indices shifted by 6)
                    updated_last = 0
                    for m in section_pattern.finditer(html):
                        updated_last = m.end()
                    html = html[:updated_last] + '\n</div>' + html[updated_last:]
                break
            depth -= 1
            i += close_m.start() + len(close_m.group(0))

    return html


def _strip_orphan_nav_links(html: str) -> str:
    """Remove sidebar <a href="#id"> links that have no matching <section id="id"> in the body."""
    section_ids = set(re.findall(r'<section[^>]+id="([^"]+)"', html))
    def replace_link(m: re.Match) -> str:
        href_id = m.group(1)
        return "" if href_id not in section_ids else m.group(0)
    return re.sub(r'<a href="#([^"]+)"[^>]*>.*?</a>', replace_link, html, flags=re.DOTALL)


def _fix_close_tags(html: str) -> str:
    """Fix structural close-tag issues that Claude frequently produces:
    1. </main> with no matching <main> opener → replace with </section></div>
    2. Unclosed last <section> → insert </section> before </div> closing #main
    3. Truncated HTML (no </html>) → append closing tags
    """
    # Fix spurious </main>: Claude uses <div id="main"> but sometimes closes with </main>
    has_main_open = bool(re.search(r'<main[\s>]', html))
    if not has_main_open and '</main>' in html:
        # Count unclosed sections at the point of </main>
        before_main_close = html[:html.index('</main>')]
        n_open = len(re.findall(r'<section[^>]*>', before_main_close))
        n_close = len(re.findall(r'</section>', before_main_close))
        missing_closes = '\n</section>' * (n_open - n_close)
        html = html.replace('</main>', missing_closes + '\n</div>', 1)

    # If still truncated (no </html>), append closing tags
    if '</html>' not in html:
        closing = ''
        n_open = len(re.findall(r'<section[^>]*>', html))
        n_close = len(re.findall(r'</section>', html))
        closing += '\n</section>' * (n_open - n_close)
        if '</body>' not in html:
            closing += '\n</body>'
        closing += '\n</html>'
        html = html + closing

    return html


def _inject_nav_js(html: str) -> str:
    """Inject reliable nav JS before </body>, replacing any existing progress/observer scripts."""
    html = re.sub(
        r'<script>\s*(?:(?:window\.addEventListener|document\.querySelectorAll|const obs|var obs)[^<]*)+</script>',
        '',
        html,
        flags=re.DOTALL,
    )
    html = _fix_close_tags(html)
    html = _fix_sections_outside_main(html)
    return html.replace('</body>', _NAV_FIX_JS + '\n</body>', 1)


def _continue_html(client: anthropic.Anthropic, system_prompt: str,
                   user_prompt: str, partial_html: str) -> str:
    """If Claude was cut off (max_tokens), continue from the partial output."""
    try:
        cont = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=8000,
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_prompt},
                {"role": "assistant", "content": partial_html},
                {"role": "user", "content": (
                    "Continue the HTML report exactly where you left off. "
                    "Do NOT repeat anything already written. "
                    "Pick up mid-sentence or mid-tag if needed and finish all open sections. "
                    "End with </body></html>."
                )},
            ]
        )
        if cont.content and hasattr(cont.content[0], "text"):
            return partial_html + cont.content[0].text
    except Exception:
        pass
    return partial_html


def generate_report_html(docs: list, signature_color: str, doc_context: str = None) -> str:
    """Generate a rich HTML report. If doc_context is provided (pre-built from chunks),
    use it directly instead of building from docs."""
    if not docs:
        raise ValueError("Need at least one document to generate a report")

    client = make_client()
    is_multi = len(docs) > 1

    if doc_context is None:
        # Small doc — build context directly
        parts: list = []
        for i, doc in enumerate(docs, start=1):
            text = doc.extracted_text[:LARGE_DOC_THRESHOLD]
            parts.append(f"[DOCUMENT {i}: {doc.filename}]\n{text}")
        doc_context = "\n\n---\n\n".join(parts)

    multi_instruction = (
        "\n\nThis is a MULTI-DOCUMENT report. Include per-doc-analysis, "
        "comparison, and synthesis sections in addition to the standard sections."
    ) if is_multi else ""

    learned_hints = get_prompt_hints()
    system_prompt = get_report_prompt(signature_color, learned_hints=learned_hints)
    user_prompt = (
        f"Generate a rich HTML report for the following document(s):"
        f"{multi_instruction}\n\n{doc_context}"
    )

    try:
        message = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=16000,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}]
        )
    except anthropic.APIError as exc:
        raise ValueError(f"Claude API error during report generation: {exc}") from exc

    if not message.content:
        raise ValueError("Claude returned an empty response for report generation")

    first_block = message.content[0]
    if not hasattr(first_block, "text") or not first_block.text:
        raise ValueError(
            f"Claude returned unexpected content type '{type(first_block).__name__}' "
            "or empty text"
        )

    raw_html = first_block.text

    # If Claude hit the token limit, do a continuation pass to complete the report
    if message.stop_reason == "max_tokens":
        raw_html = _continue_html(client, system_prompt, user_prompt, raw_html)

    # Strip markdown code fences Claude sometimes wraps around the HTML
    raw_html = re.sub(r'^```[a-zA-Z]*\n?', '', raw_html.strip())
    raw_html = re.sub(r'\n?```\s*$', '', raw_html.strip())

    html = _strip_orphan_nav_links(raw_html)
    html = _inject_nav_js(html)

    try:
        record_report_generation(html)
    except Exception:
        pass

    return html


def complete_truncated_report(partial_html: str, signature_color: str) -> str:
    """Continuation pass for an already-saved report that was cut off at max_tokens.
    Returns the completed HTML (post-processed and ready to save)."""
    client = make_client()
    learned_hints = get_prompt_hints()
    system_prompt = get_report_prompt(signature_color, learned_hints=learned_hints)
    # We don't have the original user prompt, so reconstruct a minimal one
    user_prompt = "Generate a rich HTML report for the following document(s):\n\n[context provided above]"

    raw_html = _continue_html(client, system_prompt, user_prompt, partial_html)
    html = _strip_orphan_nav_links(raw_html)
    html = _inject_nav_js(html)
    return html
