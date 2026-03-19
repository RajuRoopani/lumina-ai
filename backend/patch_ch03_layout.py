"""Patch Ch03 in-place to fix sections rendering behind sidebar."""
import os, sys, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from database import SessionLocal
from models import ReportORM
from services.report_service import _fix_sections_outside_main, _inject_nav_js
from pathlib import Path

REPORT_ID = "f89b7eda-4860-4990-8ad7-e75b086c3c91"  # Ch03
OUTPUT_DIR = Path(__file__).parent.parent / "ddia-chapter-reports"


def main():
    db = SessionLocal()
    try:
        r = db.query(ReportORM).filter(ReportORM.id == REPORT_ID).first()
        if not r:
            print("Report not found")
            return

        original = r.html_content
        print(f"Ch03: {len(original):,} chars")

        # Count sections before fix
        sections_before = len(re.findall(r'data-section-id="[^"]+"', original))
        # Check how many are inside #main before fix
        main_pos = original.find('<div id="main">')
        sections_outside = 0
        if main_pos != -1:
            before_main = original[:main_pos]
            # rough check: any sections before #main opening
            sections_outside = len(re.findall(r'<section', original[original.find('</div>', main_pos + 100):original.find('</div>', main_pos + 100) + 200]))

        fixed = _fix_sections_outside_main(original)
        # Re-inject nav JS (uses updated fixed HTML)
        # _inject_nav_js calls _fix_sections_outside_main internally now, but let's apply directly
        fixed = fixed

        sections_after = len(re.findall(r'data-section-id="[^"]+"', fixed))
        changed = "CHANGED" if fixed != original else "no change"
        print(f"  Sections: {sections_before} → {sections_after} | {changed}")

        if fixed != original:
            r.html_content = fixed
            db.commit()
            print("  DB updated")

            # Update HTML file on disk
            safe = re.sub(r'[^\w\s-]', '', "Storage and Retrieval").strip().replace(' ', '-').lower()
            filename = f"ch03-{safe[:40]}.html"
            out_path = OUTPUT_DIR / filename
            if out_path.exists():
                out_path.write_text(fixed, encoding="utf-8")
                print(f"  File updated: {filename}")
            else:
                # Try glob
                files = list(OUTPUT_DIR.glob("ch03-*.html"))
                if files:
                    files[0].write_text(fixed, encoding="utf-8")
                    print(f"  File updated: {files[0].name}")
        else:
            print("  No structural change needed (or fix didn't apply)")
    finally:
        db.close()


if __name__ == "__main__":
    main()
