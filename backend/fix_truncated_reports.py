"""Fix all chapter reports that were truncated at the Claude token limit.

Finds reports missing </html>, does a continuation call, updates DB + HTML file.
Usage: python3 fix_truncated_reports.py
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
os.chdir(os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from database import SessionLocal
from models import ReportORM
from services.report_service import complete_truncated_report

OUTPUT_DIR = Path(__file__).parent.parent / "ddia-chapter-reports"

DOC_ID = "131618c7-cac3-4616-bcd3-016399985a1b"


def main():
    db = SessionLocal()
    try:
        # Find all reports linked to the DDIA document
        all_reports = db.query(ReportORM).all()
        ddia_reports = [
            r for r in all_reports
            if DOC_ID in r.document_ids_json
        ]
        print(f"Found {len(ddia_reports)} DDIA-linked reports")

        truncated = [r for r in ddia_reports if not r.html_content.strip().endswith("</html>")]
        print(f"  {len(truncated)} truncated (missing </html>)\n")

        for r in truncated:
            print(f"  Fixing: {r.title} ({len(r.html_content):,} chars)...", flush=True)
            completed = complete_truncated_report(r.html_content, r.signature_color)
            added = len(completed) - len(r.html_content)
            print(f"    +{added:,} chars → ends with </html>: {completed.strip().endswith('</html>')}")

            # Update DB
            r.html_content = completed
            db.commit()

            # Update HTML file on disk
            html_files = list(OUTPUT_DIR.glob(f"ch*{r.id[:8]}*.html"))
            # Try matching by title slug
            import re
            safe = re.sub(r'[^\x00-\x7F]', '', r.title)
            safe = re.sub(r'[^a-zA-Z0-9\s]', '', safe).strip()
            slug = re.sub(r'\s+', '-', safe).lower()[:40]
            html_files = list(OUTPUT_DIR.glob(f"ch*{slug[:15]}*.html"))
            if html_files:
                html_files[0].write_text(completed, encoding="utf-8")
                print(f"    Updated: {html_files[0].name}")
            print(f"    ✓ Done\n", flush=True)

    finally:
        db.close()

    print("All truncated reports fixed.")


if __name__ == "__main__":
    main()
