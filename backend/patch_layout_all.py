"""Apply _fix_close_tags and _fix_sections_outside_main to existing reports in-place."""
import os, sys, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from database import SessionLocal
from models import ReportORM
from services.report_service import _fix_close_tags, _fix_sections_outside_main, _inject_nav_js
from pathlib import Path

OUTPUT_DIR = Path(__file__).parent.parent / "ddia-chapter-reports"

TARGETS = {
    "f89b7eda-4860-4990-8ad7-e75b086c3c91": ("Ch03", "ch03-storage-and-retrieval.html"),
    "69715efa-bef8-4ef8-83fc-336a312c1691": ("Ch08", "ch08-the-trouble-with-distributed-systems.html"),
}


def main():
    db = SessionLocal()
    try:
        for rid, (name, filename) in TARGETS.items():
            r = db.query(ReportORM).filter(ReportORM.id == rid).first()
            if not r:
                print(f"{name}: not found")
                continue

            original = r.html_content
            n_open = len(re.findall(r'<section[^>]*>', original))
            n_close = len(re.findall(r'</section>', original))
            has_bad_main = '</main>' in original and not re.search(r'<main[\s>]', original)
            print(f"{name}: {len(original):,} chars | sections {n_open} open / {n_close} closed | bad </main>: {has_bad_main}")

            fixed = _fix_close_tags(original)
            fixed = _fix_sections_outside_main(fixed)

            n_open2 = len(re.findall(r'<section[^>]*>', fixed))
            n_close2 = len(re.findall(r'</section>', fixed))
            has_bad_main2 = '</main>' in fixed and not re.search(r'<main[\s>]', fixed)
            ends_ok = fixed.strip().endswith('</html>')
            print(f"  → {len(fixed):,} chars | sections {n_open2} open / {n_close2} closed | bad </main>: {has_bad_main2} | ends </html>: {ends_ok}")

            if fixed != original:
                r.html_content = fixed
                db.commit()
                out_path = OUTPUT_DIR / filename
                out_path.write_text(fixed, encoding="utf-8")
                print(f"  ✓ Saved DB + {filename}")
            else:
                print(f"  (no change)")
    finally:
        db.close()


if __name__ == "__main__":
    main()
