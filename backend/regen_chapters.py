"""Regenerate specific DDIA chapters in-place (updates DB record + HTML file)."""
import os, sys, json, re, uuid
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from database import SessionLocal
from models import DocumentORM, ReportORM
from services.report_service import (
    generate_report_html, pick_signature_color, make_client,
    split_into_chunks, summarize_chunk, LARGE_DOC_THRESHOLD,
)
from pathlib import Path

DOC_ID = "131618c7-cac3-4616-bcd3-016399985a1b"
OUTPUT_DIR = Path(__file__).parent.parent / "ddia-chapter-reports"

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

# Map chapter number → existing report ID (to update in place)
CHAPTER_REPORT_IDS = {
    2: "b834669e-7058-47b2-93b7-b24a3005976a",
    3: "f89b7eda-4860-4990-8ad7-e75b086c3c91",
    5: "5dc368b0-1767-4f92-9449-7b7184049faf",
    7: "e8329553-6edf-44e7-8ae2-60c1b9a8c57a",
}

# Which chapters to regenerate
REGEN = [7]


class _FakeDoc:
    def __init__(self, filename, text):
        self.filename = filename
        self.extracted_text = text


def regen_chapter(chapter_num, chapter_text, client, db, color):
    title = CHAPTER_TITLES[chapter_num]
    doc_name = f"DDIA Ch{chapter_num:02d}: {title}"
    fake_doc = _FakeDoc(doc_name, chapter_text)

    if len(chapter_text) > LARGE_DOC_THRESHOLD:
        chunks = split_into_chunks(chapter_text)
        n = len(chunks)
        print(f"  {n} chunks to summarize", flush=True)
        summaries = []
        for i, chunk in enumerate(chunks, 1):
            print(f"    chunk {i}/{n}...", flush=True)
            summaries.append(summarize_chunk(client, chunk, i, n, doc_name))
        doc_context = f"[DOCUMENT: {doc_name}]\n\n" + "\n\n".join(summaries)
    else:
        doc_context = f"[DOCUMENT: {doc_name}]\n{chapter_text}"

    print(f"  Generating HTML...", flush=True)
    html = generate_report_html([fake_doc], signature_color=color, doc_context=doc_context)

    sections = re.findall(r'data-section-id="([^"]+)"', html)
    ends_ok = html.strip().endswith("</html>")
    print(f"  {len(sections)} sections | {len(html):,} chars | </html>: {ends_ok}")
    if not ends_ok:
        print(f"  WARNING: still not ending with </html>!")

    # Update DB
    report_id = CHAPTER_REPORT_IDS[chapter_num]
    r = db.query(ReportORM).filter(ReportORM.id == report_id).first()
    r.html_content = html
    db.commit()

    # Update file
    safe = re.sub(r'[^\w\s-]', '', title).strip().replace(' ', '-').lower()
    filename = f"ch{chapter_num:02d}-{safe[:40]}.html"
    out_path = OUTPUT_DIR / filename
    out_path.write_text(html, encoding="utf-8")
    print(f"  Saved: {filename}")
    print(f"  URL: http://localhost:5173/share/{report_id}\n", flush=True)


def main():
    db = SessionLocal()
    doc = db.query(DocumentORM).filter(DocumentORM.id == DOC_ID).first()
    text = doc.extracted_text

    matches = list(re.finditer(r'\nCHAPTER\s+(\d+)\n', text))
    chapter_starts = {int(m.group(1)): m.start() for m in matches}

    client = make_client()

    for num in REGEN:
        start = chapter_starts[num]
        end = chapter_starts[num + 1] if num + 1 in chapter_starts else len(text)
        chapter_text = text[start:end]
        color = pick_signature_color(num)
        print(f"[Ch{num:02d}] {CHAPTER_TITLES[num]} ({len(chapter_text):,} chars)", flush=True)
        regen_chapter(num, chapter_text, client, db, color)

    db.close()
    print("Done.")


if __name__ == "__main__":
    main()
