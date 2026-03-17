"""
Persistent learning service for Lumina retro loop.

After each report generation and chat interaction, observations are logged
to learnings.json. These are distilled into prompt hints that make
subsequent reports progressively better — a continuous improvement loop.
"""
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

_LEARNINGS_PATH = Path(__file__).parent.parent / "learnings.json"

_CSS_CLASSES = [
    "callout", "pill", "box-row", "box", "arrow",
    "timeline", "approach-card", "stat-grid",
    "pro-con-grid", "tag", "seq-row", "seq-block",
]

_DEFAULT: dict = {
    "report_stats": {
        "total_generated": 0,
        "avg_section_count": 0.0,
        "component_usage": {},
    },
    "chat_stats": {
        "total_chats": 0,
        "section_updates": 0,
        "most_updated_sections": {},
        "qa_count": 0,
    },
    "prompt_hints": [],
    "version": 1,
}


def _load() -> dict:
    if _LEARNINGS_PATH.exists():
        try:
            with open(_LEARNINGS_PATH) as f:
                data = json.load(f)
            # Backfill missing keys from defaults
            for k, v in _DEFAULT.items():
                if k not in data:
                    data[k] = json.loads(json.dumps(v))
            return data
        except Exception:
            pass
    return json.loads(json.dumps(_DEFAULT))


def _save(data: dict) -> None:
    data["last_updated"] = datetime.now(timezone.utc).isoformat()
    with open(_LEARNINGS_PATH, "w") as f:
        json.dump(data, f, indent=2)


def record_report_generation(html: str) -> None:
    """Log quality signals from a newly generated report and refresh hints."""
    data = _load()
    rs = data["report_stats"]
    rs["total_generated"] += 1

    # Section count
    section_count = len(re.findall(r'data-section-id=', html))
    n = rs["total_generated"]
    rs["avg_section_count"] = round(
        (rs["avg_section_count"] * (n - 1) + section_count) / n, 1
    )

    # CSS component usage
    usage: dict = rs.setdefault("component_usage", {})
    for cls in _CSS_CLASSES:
        if cls in html:
            usage[cls] = usage.get(cls, 0) + 1

    _refresh_hints(data)
    _save(data)


def record_chat_interaction(
    action_taken: Optional[str],
    section_id: Optional[str] = None,
) -> None:
    """Log a chat interaction outcome and refresh hints."""
    data = _load()
    cs = data["chat_stats"]
    cs["total_chats"] += 1

    if action_taken == "section_update" and section_id:
        cs["section_updates"] += 1
        su: dict = cs.setdefault("most_updated_sections", {})
        su[section_id] = su.get(section_id, 0) + 1
    else:
        cs["qa_count"] += 1

    _refresh_hints(data)
    _save(data)


def _refresh_hints(data: dict) -> None:
    """Derive actionable prompt hints from accumulated stats."""
    hints: list[str] = []
    rs = data["report_stats"]
    cs = data["chat_stats"]

    # ── Section depth ─────────────────────────────────────────────────────────
    avg = rs["avg_section_count"]
    if avg > 0:
        if avg < 7:
            hints.append(
                f"DEPTH: Past reports averaged only {avg} sections — generate 9-12 distinct "
                "sections to give a comprehensive, multi-angle analysis."
            )
        else:
            hints.append(f"DEPTH: Good — keep {avg}+ sections per report.")

    # ── Component diversity ────────────────────────────────────────────────────
    total = rs["total_generated"]
    usage = rs.get("component_usage", {})
    if total >= 2:
        never_used = [c for c in _CSS_CLASSES if usage.get(c, 0) == 0]
        if never_used:
            sample = ", ".join(f".{c}" for c in never_used[:5])
            hints.append(
                f"VARIETY: These CSS components have NEVER appeared — use them: {sample}."
            )
        underused = [
            c for c in _CSS_CLASSES
            if 0 < usage.get(c, 0) <= max(1, total // 3)
        ]
        if underused:
            sample = ", ".join(f".{c}" for c in underused[:4])
            hints.append(f"VARIETY: Use these components more frequently: {sample}.")

    # ── Sections users update most ─────────────────────────────────────────────
    most_updated = cs.get("most_updated_sections", {})
    if most_updated:
        top = sorted(most_updated.items(), key=lambda x: x[1], reverse=True)[:4]
        top_ids = ", ".join(s[0] for s in top)
        hints.append(
            f"RICHNESS: Users most often ask AI to improve: {top_ids}. "
            "Make these sections exceptionally detailed in the initial report."
        )

    data["prompt_hints"] = hints


def get_prompt_hints() -> str:
    """Return formatted prompt hints for injection into the report generation prompt."""
    data = _load()
    hints = data.get("prompt_hints", [])
    if not hints:
        return ""
    lines = "\n".join(f"• {h}" for h in hints)
    return f"\n\nLEARNED IMPROVEMENTS (retro loop — apply these in every report):\n{lines}"
