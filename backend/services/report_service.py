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


def _strip_orphan_nav_links(html: str) -> str:
    """Remove sidebar <a href="#id"> links that have no matching <section id="id"> in the body."""
    section_ids = set(re.findall(r'<section[^>]+id="([^"]+)"', html))
    def replace_link(m: re.Match) -> str:
        href_id = m.group(1)
        return "" if href_id not in section_ids else m.group(0)
    return re.sub(r'<a href="#([^"]+)"[^>]*>.*?</a>', replace_link, html, flags=re.DOTALL)


def _close_truncated_html(html: str) -> str:
    """If Claude was cut off before closing tags, append them so the browser renders cleanly."""
    if '</html>' in html:
        return html
    # Close any unclosed structural tags in reverse order
    closing = ''
    if '</main>' not in html:
        closing += '\n</main>'
    if '</div>' not in html.split('</main>')[-1]:
        closing += '\n</div>'
    if '</body>' not in html:
        closing += '\n</body>'
    closing += '\n</html>'
    return html + closing


def _inject_nav_js(html: str) -> str:
    """Inject reliable nav JS before </body>, replacing any existing progress/observer scripts."""
    html = re.sub(
        r'<script>\s*(?:(?:window\.addEventListener|document\.querySelectorAll|const obs|var obs)[^<]*)+</script>',
        '',
        html,
        flags=re.DOTALL,
    )
    html = _close_truncated_html(html)
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
