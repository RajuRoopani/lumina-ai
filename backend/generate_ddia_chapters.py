"""Generate one rich HTML report per chapter of DDIA.

Usage: python3 generate_ddia_chapters.py
Outputs: ../ddia-chapter-reports/ch01-*.html ... ch12-*.html
Also saves each report to the DB so it appears in the Lumina UI.
"""
import os
import re
import json
import uuid
import sys
from pathlib import Path

# Add backend to path and load .env
sys.path.insert(0, os.path.dirname(__file__))
os.chdir(os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from database import SessionLocal
from models import DocumentORM, ReportORM
from services.report_service import (
    generate_report_html,
    pick_signature_color,
    make_client,
    split_into_chunks,
    summarize_chunk,
    LARGE_DOC_THRESHOLD,
)

CHAPTER_TITLES = {
    1:  "Reliable, Scalable, and Maintainable Applications",
    2:  "Data Models and Query Languages",
    3:  "Storage and Retrieval",
    4:  "Encoding and Evolution",
    5:  "Replication",
    6:  "Partitioning",
    7:  "Transactions",
    8:  "The Trouble with Distributed Systems",
    9:  "Consistency and Consensus",
    10: "Batch Processing",
    11: "Stream Processing",
    12: "The Future of Data Systems",
}

DOC_ID = "131618c7-cac3-4616-bcd3-016399985a1b"
OUTPUT_DIR = Path(__file__).parent.parent / "ddia-chapter-reports"


class _FakeDoc:
    """Minimal stand-in for DocumentORM — only needs .filename and .extracted_text."""
    def __init__(self, filename: str, text: str):
        self.filename = filename
        self.extracted_text = text


def split_into_chapters(text: str) -> list:
    matches = list(re.finditer(r'\nCHAPTER\s+(\d+)\n', text))
    chapters = []
    for i, m in enumerate(matches):
        num = int(m.group(1))
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        chapters.append((num, text[start:end]))
    return chapters


def generate_chapter_report(client, chapter_num: int, chapter_text: str,
                             color: str, db) -> tuple:
    """Summarize chunks if large, then generate full HTML. Returns (html, report_id, title)."""
    title = CHAPTER_TITLES[chapter_num]
    fake_doc = _FakeDoc(f"DDIA Ch{chapter_num:02d}: {title}", chapter_text)

    # Build context — chunk if large
    if len(chapter_text) > LARGE_DOC_THRESHOLD:
        chunks = split_into_chunks(chapter_text)
        n = len(chunks)
        print(f"    → {n} chunk(s) to summarize", flush=True)
        summaries = []
        for i, chunk in enumerate(chunks, 1):
            print(f"      Summarizing chunk {i}/{n}...", flush=True)
            summary = summarize_chunk(client, chunk, i, n, fake_doc.filename)
            summaries.append(summary)
        doc_context = f"[DOCUMENT: {fake_doc.filename}]\n\n" + "\n\n".join(summaries)
    else:
        doc_context = f"[DOCUMENT: {fake_doc.filename}]\n{chapter_text}"

    print(f"    → Generating HTML report...", flush=True)
    html = generate_report_html([fake_doc], signature_color=color, doc_context=doc_context)

    # Extract title from generated HTML
    title_match = re.search(r"<h1[^>]*>(.*?)</h1>", html, re.S)
    report_title = (
        re.sub(r"<[^>]+>", "", title_match.group(1)).strip()
        if title_match
        else f"DDIA Ch{chapter_num:02d}: {title}"
    )

    # Save to DB so it shows in Lumina UI
    report_id = str(uuid.uuid4())
    orm = ReportORM(
        id=report_id,
        title=report_title,
        document_ids_json=json.dumps([DOC_ID]),
        html_content=html,
        signature_color=color,
    )
    db.add(orm)
    db.commit()

    return html, report_id, report_title


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Output directory: {OUTPUT_DIR}", flush=True)

    db = SessionLocal()
    try:
        doc = db.query(DocumentORM).filter(DocumentORM.id == DOC_ID).first()
        if not doc:
            print("ERROR: DDIA document not found in DB")
            return

        chapters = split_into_chapters(doc.extracted_text)
        print(f"Found {len(chapters)} chapters\n", flush=True)

        client = make_client()
        report_index = db.query(ReportORM).count()

        results = []
        for chapter_num, chapter_text in chapters:
            title = CHAPTER_TITLES.get(chapter_num, f"Chapter {chapter_num}")
            color = pick_signature_color(report_index + chapter_num)
            print(f"[Ch{chapter_num:02d}] {title} ({len(chapter_text):,} chars)", flush=True)

            html, report_id, report_title = generate_chapter_report(
                client, chapter_num, chapter_text, color, db
            )

            # Save HTML file
            safe_title = re.sub(r'[^\w\s-]', '', title).strip().replace(' ', '-').lower()
            filename = f"ch{chapter_num:02d}-{safe_title[:40]}.html"
            out_path = OUTPUT_DIR / filename
            out_path.write_text(html, encoding="utf-8")

            results.append({
                "chapter": chapter_num,
                "title": report_title,
                "report_id": report_id,
                "file": str(out_path),
                "url": f"http://localhost:5173/share/{report_id}",
            })
            print(f"    ✓ Saved: {filename}  |  {results[-1]['url']}\n", flush=True)

        print("\n" + "="*60)
        print("ALL CHAPTERS COMPLETE")
        print("="*60)
        for r in results:
            print(f"Ch{r['chapter']:02d}: {r['url']}")

        # Write index JSON
        index_path = OUTPUT_DIR / "index.json"
        index_path.write_text(json.dumps(results, indent=2))
        print(f"\nIndex: {index_path}")

    finally:
        db.close()


if __name__ == "__main__":
    main()
