import os
import sys
import json
import time
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(backend_dir))

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import pymupdf
from app.services.ocr_service import OCRService
from app.services.parser_service import ParserService
from app.services.normalization_service import NormalizationService
from app.profiles.profile_service import ProfileService

FIXTURES_DIR = backend_dir / "tests" / "fixtures"

TEST_FILES = [
    "Mr.JAYACHANDRAN_KAD393.4 (3).PDF",
    "CBC-with-ESR-test-report-format-example-sample-template-Drlogy-lab-report.pdf",
    "Mrs.LILLY RICHARD_KAD393.2 (1).PDF",
    "1724_fid.pdf",
    "Sample-Lab-Report-DBTICBM.pdf",
    "Wellwise Platinum Profile - 5048.pdf",
]

def verify_reports():
    print("=" * 70, flush=True)
    print("END-TO-END MEDICAL REPORT PARSING VERIFICATION (6 REPORTS)", flush=True)
    print("=" * 70 + "\n", flush=True)

    report_summaries = []

    for idx, filename in enumerate(TEST_FILES, 1):
        filepath = FIXTURES_DIR / filename
        if not filepath.exists():
            print(f"[{idx}/6] MISSING FILE: {filename}", flush=True)
            continue

        size_kb = filepath.stat().st_size / 1024
        print(f"[{idx}/6] Parsing: {filename} ({size_kb:.1f} KB)...", flush=True)
        t0 = time.time()

        doc = pymupdf.open(filepath)
        page_count = len(doc)
        
        # Check if digital PDF or needs OCR
        digital_text_parts = []
        for page in doc:
            t = page.get_text("text")
            if t and t.strip():
                digital_text_parts.append(t.strip())
        digital_text = "\n".join(digital_text_parts)
        is_digital = len(digital_text.strip()) > 50

        extracted_lines = []
        if is_digital:
            for page in doc:
                page_lines = OCRService.extract_layout_sorted_lines(page)
                extracted_lines.extend(page_lines)
            doc_type = "DIGITAL_PDF"
        else:
            doc_type = "SCANNED_OCR"
            # For scanned, run OCR on pages (limit to first 4 pages for large files like RCY if needed)
            max_pages = min(page_count, 6)
            for page_idx in range(max_pages):
                pix = doc[page_idx].get_pixmap(dpi=150)
                img_bytes = pix.tobytes("png")
                lines, _ = OCRService.extract_text_from_image(img_bytes, page_num=page_idx+1)
                extracted_lines.extend(lines)

        doc.close()

        # Run parsing
        report_id = f"test_rep_{idx}"
        parsed = ParserService.parse_document_text(report_id, extracted_lines)
        normalized = NormalizationService.normalize_extracted_report(parsed)
        
        # Run profile grouping
        active_profiles, _ = ProfileService.group_tests(normalized.tests)
        profile_names = [p.profile_name for p in active_profiles]
        elapsed = time.time() - t0

        # Stats
        total_tests = len(normalized.tests)
        normal_tests = sum(1 for t in normalized.tests if t.status == "NORMAL")
        abnormal_tests = sum(1 for t in normalized.tests if t.status in ["HIGH", "LOW", "CRITICAL", "POSITIVE"])
        unknown_tests = sum(1 for t in normalized.tests if t.status == "UNKNOWN")
        review_required = sum(1 for t in normalized.tests if t.flag == "REVIEW_REQUIRED")
        red_flags = sum(1 for t in normalized.tests if t.flag == "RED_FLAG")
        
        # Sample tests
        samples = [
            f"{t.test_name}: {t.value} {t.normalized_unit or t.raw_unit or ''} [{t.status}]"
            for t in normalized.tests[:4]
        ]

        summary = {
            "index": idx,
            "filename": filename,
            "doc_type": doc_type,
            "pages": page_count,
            "elapsed_seconds": round(elapsed, 2),
            "patient_name": normalized.patient.name or "Not Specified",
            "patient_age": normalized.patient.age or "N/A",
            "patient_gender": normalized.patient.gender or "N/A",
            "total_tests": total_tests,
            "normal": normal_tests,
            "abnormal": abnormal_tests,
            "unknown": unknown_tests,
            "red_flags": red_flags,
            "review_required": review_required,
            "profiles_count": len(profile_names),
            "profiles": profile_names,
            "sample_tests": samples,
            "status": "PASSED" if total_tests > 0 else "WARNING_NO_TESTS"
        }
        report_summaries.append(summary)

        print(f"    --> Status: {summary['status']} ({elapsed:.2f}s)")
        print(f"    --> Patient: {summary['patient_name']}, Age: {summary['patient_age']}, Gender: {summary['patient_gender']}")
        print(f"    --> Tests Extracted: {total_tests} (Normal: {normal_tests}, Abnormal: {abnormal_tests}, Review: {review_required})")
        print(f"    --> Profiles ({len(profile_names)}): {', '.join(profile_names[:4])}...")
        print(f"    --> Samples: {'; '.join(samples[:2])}")
        print("-" * 70, flush=True)

    print("\n" + "=" * 70, flush=True)
    print("CONSOLIDATED SUMMARY MATRIX (6 REPORTS)", flush=True)
    print("=" * 70, flush=True)
    header = f"{'#':<2} | {'Filename':<32} | {'Pages':<5} | {'Tests':<5} | {'Norm':<5} | {'Abnorm':<6} | {'Profiles':<8} | {'Time':<6}"
    print(header, flush=True)
    print("-" * len(header), flush=True)
    for s in report_summaries:
        fn = s['filename'][:30]
        print(f"{s['index']:<2} | {fn:<32} | {s['pages']:<5} | {s['total_tests']:<5} | {s['normal']:<5} | {s['abnormal']:<6} | {s['profiles_count']:<8} | {s['elapsed_seconds']:<5}s", flush=True)

    out_json = backend_dir / "verified_batch_results.json"
    with open(out_json, "w") as f:
        json.dump(report_summaries, f, indent=2)
    print(f"\nSaved verified batch results to: {out_json}", flush=True)

if __name__ == "__main__":
    verify_reports()
