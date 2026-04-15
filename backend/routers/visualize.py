import json
import re
import uuid
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from database import SessionLocal
from models import ReportORM
from prompts.visualize_prompt import get_visualize_prompt, VISUALIZE_COLORS
from services.report_service import make_client, _fix_close_tags, _fix_sections_outside_main
from services.learnings_service import get_prompt_hints

router = APIRouter()

_NAV_JS = """<script>
(function() {
  document.querySelectorAll('#sidebar nav a').forEach(function(link) {
    link.addEventListener('click', function(e) {
      e.preventDefault(); e.stopPropagation();
      var id = this.getAttribute('href').replace(/^#/, '');
      var target = document.getElementById(id);
      if (target) target.scrollIntoView({ behavior: 'smooth', block: 'start' });
    });
  });
  var bar = document.getElementById('progress-bar');
  if (bar) {
    window.addEventListener('scroll', function() {
      var h = document.documentElement;
      var pct = (h.scrollTop / (h.scrollHeight - h.clientHeight)) * 100;
      bar.style.width = pct + '%';
    });
  }
  var sections = document.querySelectorAll('section[id]');
  var links = document.querySelectorAll('#sidebar nav a');
  if (sections.length && links.length && window.IntersectionObserver) {
    var obs = new IntersectionObserver(function(entries) {
      entries.forEach(function(e) {
        if (e.isIntersecting) links.forEach(function(l) {
          l.classList.toggle('active', l.getAttribute('href') === '#' + e.target.id);
        });
      });
    }, { rootMargin: '-20% 0px -70% 0px' });
    sections.forEach(function(s) { obs.observe(s); });
  }
})();
</script>"""


def _pick_color(idx: int) -> str:
    return VISUALIZE_COLORS[idx % len(VISUALIZE_COLORS)]


def _post_process(html: str) -> str:
    """Strip markdown fences, fix structural issues, inject nav JS."""
    html = re.sub(r'^```[a-zA-Z]*\n?', '', html.strip())
    html = re.sub(r'\n?```\s*$', '', html.strip())
    html = _fix_close_tags(html)
    html = _fix_sections_outside_main(html)
    # Inject nav JS before </body> if not already present
    if _NAV_JS[:30] not in html and '</body>' in html:
        html = html.replace('</body>', _NAV_JS + '\n</body>', 1)
    return html


@router.post("/generate")
def generate_visualization(body: dict):
    query: str = (body.get("query") or "").strip()
    if not query:
        return {"error": "query is required"}

    def event_stream():
        db = SessionLocal()
        done_payload = None
        try:
            client = make_client()
            color_idx = db.query(ReportORM).count()
            accent = _pick_color(color_idx)

            yield f"data: {json.dumps({'event': 'progress', 'data': f'✦ Building visualization for: {query}…'})}\n\n"

            system_prompt = get_visualize_prompt(accent)
            user_prompt = f"Generate a rich visual HTML explanation for: {query}"

            yield f"data: {json.dumps({'event': 'progress', 'data': 'Generating diagrams and step-by-step walkthrough…'})}\n\n"

            message = client.messages.create(
                model="claude-haiku-4-5",
                max_tokens=8000,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
            )

            if not message.content or not hasattr(message.content[0], "text"):
                raise ValueError("Claude returned empty response")

            raw_html = message.content[0].text

            def _section_count(html: str) -> int:
                return len(re.findall(r'<section[^>]+id=', html))

            # Continuation loop: fire when cut off (max_tokens) OR when Claude
            # closed early but produced fewer than 10 sections (under-generated).
            pass_num = 0
            while pass_num < 8:
                has_closing = '</html>' in raw_html
                enough_sections = _section_count(raw_html) >= 10
                was_cut_off = message.stop_reason == "max_tokens"
                if has_closing and enough_sections:
                    break   # genuinely complete
                if has_closing and not enough_sections:
                    # Claude closed early — strip the closing tags and force expansion
                    raw_html = re.sub(r'\s*</body>\s*</html>\s*$', '', raw_html.rstrip())
                    yield f"data: {json.dumps({'event': 'progress', 'data': f'Expanding sections ({_section_count(raw_html)} so far, targeting 10+)…'})}\n\n"
                elif was_cut_off:
                    pass_num += 1
                    yield f"data: {json.dumps({'event': 'progress', 'data': f'Completing remaining sections (pass {pass_num})…'})}\n\n"
                else:
                    break   # end_turn + enough sections or unknown state
                pass_num += 1
                try:
                    cont_prompt = (
                        "Continue the HTML exactly where you left off. "
                        "Do NOT repeat anything already written. "
                        "Add ALL remaining sections — you must reach at least 10 fully-written sections total. "
                        "Each section must open with a visual component (diagram, grid, or step-flow), never a bare paragraph. "
                        "End with </body></html> only after all sections are complete."
                    ) if was_cut_off else (
                        "The report is incomplete — only " + str(_section_count(raw_html)) + " sections were generated but the minimum is 10. "
                        "Continue the HTML from where it left off. Add ALL remaining sections now. "
                        "Each new section must open with a visual component. "
                        "End with </body></html> after all sections are complete."
                    )
                    cont = client.messages.create(
                        model="claude-haiku-4-5",
                        max_tokens=8000,
                        system=system_prompt,
                        messages=[
                            {"role": "user", "content": user_prompt},
                            {"role": "assistant", "content": raw_html},
                            {"role": "user", "content": cont_prompt},
                        ],
                    )
                    if cont.content and hasattr(cont.content[0], "text"):
                        raw_html = raw_html + cont.content[0].text
                        message = cont
                    else:
                        break
                except Exception:
                    break

            yield f"data: {json.dumps({'event': 'progress', 'data': 'Polishing visuals…'})}\n\n"

            html = _post_process(raw_html)

            # Extract title: prefer <title> tag (Claude puts the real topic there),
            # fall back to <h1>, then the raw query
            title_tag = re.search(r'<title[^>]*>(.*?)</title>', html, re.S)
            if title_tag:
                title = re.sub(r'<[^>]+>', '', title_tag.group(1)).strip()
                title = re.sub(r'\s*[—–-]+\s*(Lumina.*)?$', '', title, flags=re.I).strip()
            else:
                h1_m = re.search(r'<h1[^>]*>(.*?)</h1>', html, re.S)
                title = re.sub(r'<[^>]+>', '', h1_m.group(1)).strip() if h1_m else query
            # If title is still generic, fall back to query
            if not title or title.lower() in ('visualize', '✦ visualize', 'lumina visualizer'):
                title = query

            report_id = str(uuid.uuid4())
            orm = ReportORM(
                id=report_id,
                title=f"✦ {title}",
                document_ids_json=json.dumps([]),
                html_content=html,
                signature_color=accent,
            )
            db.add(orm)
            db.commit()
            done_payload = {"id": report_id, "title": f"✦ {title}"}

        except Exception as e:
            yield f"data: {json.dumps({'event': 'error', 'data': str(e)})}\n\n"
        finally:
            if done_payload:
                yield f"data: {json.dumps({'event': 'done', 'data': done_payload})}\n\n"
            db.close()

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
