import re
import anthropic
from models import DocumentORM
from prompts.report_prompt import get_report_prompt, SIGNATURE_COLORS
from config import ANTHROPIC_API_KEY
from services.learnings_service import get_prompt_hints, record_report_generation

# Per-document truncation ceiling — keep high for quality
_MAX_DOC_CHARS = 12000


def pick_signature_color(report_index: int) -> str:
    return SIGNATURE_COLORS[report_index % len(SIGNATURE_COLORS)]


def build_document_context(docs: list[DocumentORM]) -> str:
    parts: list[str] = []
    for i, doc in enumerate(docs, start=1):
        text = doc.extracted_text
        truncated = len(text) > _MAX_DOC_CHARS
        if truncated:
            text = text[:_MAX_DOC_CHARS] + "\n... [truncated] ..."
        parts.append(f"[DOCUMENT {i}: {doc.filename}]\n{text}")
    return "\n\n---\n\n".join(parts)


# Injected into every report before </body> — guaranteed regardless of what the model writes
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


def _inject_nav_js(html: str) -> str:
    """Inject reliable nav JS before </body>, replacing any existing progress/observer scripts."""
    # Remove any script blocks the model wrote that handle scroll/progress/observer
    # (they use href-based navigation which breaks in srcdoc iframes)
    html = re.sub(
        r'<script>\s*(?:(?:window\.addEventListener|document\.querySelectorAll|const obs|var obs)[^<]*)+</script>',
        '',
        html,
        flags=re.DOTALL,
    )
    if '</body>' in html:
        return html.replace('</body>', _NAV_FIX_JS + '\n</body>', 1)
    return html + _NAV_FIX_JS


def generate_report_html(docs: list[DocumentORM], signature_color: str) -> str:
    """Generate a rich HTML report from one or more documents using Claude.

    Raises:
        ValueError: if docs is empty, API key is missing, API call fails,
                    or Claude returns an unusable response.
    """
    if not docs:
        raise ValueError("Need at least one document to generate a report")
    if not ANTHROPIC_API_KEY:
        raise ValueError("ANTHROPIC_API_KEY is not configured")

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    doc_context = build_document_context(docs)
    is_multi = len(docs) > 1
    multi_instruction = (
        "\n\nThis is a MULTI-DOCUMENT report. Include per-doc-analysis, "
        "comparison, and synthesis sections in addition to the standard sections."
    ) if is_multi else ""

    learned_hints = get_prompt_hints()

    try:
        message = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=16000,
            system=get_report_prompt(signature_color, learned_hints=learned_hints),
            messages=[{
                "role": "user",
                "content": (
                    f"Generate a rich HTML report for the following document(s):"
                    f"{multi_instruction}\n\n{doc_context}"
                )
            }]
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
    html = _strip_orphan_nav_links(first_block.text)
    html = _inject_nav_js(html)

    # Record quality signals for retro loop (non-blocking)
    try:
        record_report_generation(html)
    except Exception:
        pass

    return html
