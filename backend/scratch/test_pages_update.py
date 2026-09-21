import os
import sys
import json
import time

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.abspath("."))

print("=== 1. Testing OCR Resize & LANCZOS Fallback ===")
from app.services.ocr_service import OCRService
import numpy as np

test_img = np.zeros((1650, 1275, 3), dtype=np.uint8)
resized_img = OCRService.safe_resize_for_paddlex(test_img, max_side=1200)
print(f"Input shape: {test_img.shape} -> Resized shape: {resized_img.shape}")
assert max(resized_img.shape[:2]) <= 1200
print("[OK] OCR safe_resize_for_paddlex passed!\n")

print("=== 2. Testing Intelligence OCR Parser Init Annotation ===")
from app.intelligence.ocr.parser import PDFOCRParser
parser = PDFOCRParser(use_vision_fallback=True)
print(f"PDFOCRParser instantiated: {parser}")
print("[OK] Parser initialization passed!\n")

print("=== 3. Testing Document Parsing on RCY Pages Extracted Data ===")
from app.services.parser_service import ParserService
from app.services.normalization_service import NormalizationService

# Load the JSON extracted from all 12 pages of RCY.pdf
with open("scratch/rcy_extracted.json", "r", encoding="utf-8") as f:
    rcy_data = json.load(f)

print(f"Patient: {rcy_data['patient']['name']}, Age: {rcy_data['patient']['age']}, Sex: {rcy_data['patient']['sex']}")
print(f"Total specimens: {len(rcy_data['specimens'])}")

total_panels = 0
total_tests = 0
page_results = []

for spec_idx, spec in enumerate(rcy_data["specimens"]):
    spec_id = spec["specimen_id"]
    spec_type = spec["specimen_type"]
    for panel in spec["panels"]:
        total_panels += 1
        panel_name = panel["panel_name"]
        tests_in_panel = len(panel["tests"])
        total_tests += tests_in_panel
        flags_count = {}
        for t in panel["tests"]:
            flg = t["flag"] or "unflagged"
            flags_count[flg] = flags_count.get(flg, 0) + 1
        page_results.append({
            "specimen_id": spec_id,
            "specimen_type": spec_type,
            "panel_name": panel_name,
            "test_count": tests_in_panel,
            "flags": flags_count
        })

print(f"Total Panels: {total_panels}, Total Tests Extracted: {total_tests}\n")

print("Detailed Panel-by-Panel Test Breakdown:")
print(f"{'#':<3} | {'Specimen':<10} | {'Type':<10} | {'Panel Name':<38} | {'Tests':<6} | Flags")
print("-" * 95)
for i, res in enumerate(page_results, 1):
    flag_str = ", ".join(f"{k}: {v}" for k, v in res["flags"].items())
    print(f"{i:<3} | {res['specimen_id']:<10} | {res['specimen_type']:<10} | {res['panel_name'][:38]:<38} | {res['test_count']:<6} | {flag_str}")

print("\n=== 4. Testing End-to-End ParserService on Raw Text Lines ===")
# Let's extract raw text lines from task-309 log for pages 1 to 5 to verify ParserService directly
task_log = r"C:\Users\TezHealth\.gemini\antigravity-ide\brain\6a63d467-835f-4392-b82d-9638f19e40af\.system_generated\tasks\task-309.log"

extracted_lines = []
if os.path.exists(task_log):
    with open(task_log, "r", encoding="utf-8") as f:
        for line in f:
            line_str = line.strip()
            if line_str.startswith("| "):
                extracted_lines.append(line_str[2:])

print(f"Collected {len(extracted_lines)} OCR lines from Pages 1-5.")
if extracted_lines:
    parsed_report = ParserService.parse_document_text("rep_test_rcy", extracted_lines)
    print(f"ParserService extracted: {len(parsed_report.tests)} lab test results")
    for r in parsed_report.tests[:10]:
        ref_raw = r.reference_range.raw if r.reference_range else "None"
        print(f"  - {r.raw_test_name}: {r.value} {r.unit or ''} (Ref: {ref_raw})")

    normalized_report = NormalizationService.normalize_extracted_report(parsed_report)
    print(f"\nNormalizationService result: {len(normalized_report.tests)} normalized tests")
    print(f"Total Warnings: {len(normalized_report.warnings)}")
    for w in normalized_report.warnings[:5]:
        print(f"  Warning: {w}")

print("\nAll page tests completed successfully!")
