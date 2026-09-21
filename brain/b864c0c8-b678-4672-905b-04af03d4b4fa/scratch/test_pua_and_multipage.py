import fitz
import sys
import io

from app.services.ocr_service import OCRService
from app.services.parser_service import ParserService
from app.services.normalization_service import NormalizationService

def clean_pua_text(text: str) -> str:
    if not text:
        return text
    chars = []
    for char in text:
        code = ord(char)
        if 0xF000 <= code <= 0xF0FF:
            chars.append(chr(code - 0xF000))
        elif 0xE000 <= code <= 0xF8FF:
            ascii_code = code & 0xFF
            if 32 <= ascii_code <= 126:
                chars.append(chr(ascii_code))
            else:
                chars.append(char)
        else:
            chars.append(char)
    return "".join(chars)

def process_file(pdf_path):
    print(f"\n==========================================")
    print(f"PROCESSING: {pdf_path}")
    print(f"==========================================")
    doc = fitz.open(pdf_path)
    all_lines = []
    for page_idx in range(len(doc)):
        page = doc[page_idx]
        d_text = clean_pua_text(page.get_text("text"))
        if len(d_text.strip()) > 30:
            lines = OCRService.extract_layout_sorted_lines(page)
            cleaned = [clean_pua_text(l) for l in lines]
            all_lines.extend(cleaned)
        else:
            img_bytes = OCRService.render_pdf_page_to_bytes(doc, page_idx)
            ocr_lines, _ = OCRService.extract_text_from_image(img_bytes)
            all_lines.extend(ocr_lines)
            
    parsed = ParserService.parse_document_text("test_id", all_lines)
    normalized = NormalizationService.normalize_extracted_report(parsed)
    
    print(f"Patient: Name='{normalized.patient.name}', Age={normalized.patient.age}, Gender='{normalized.patient.gender}', ID='{normalized.patient.patient_id}'")
    print(f"Report Date: '{normalized.report.report_date}', Lab: '{normalized.report.lab_name}'")
    print(f"Tests Extracted: {len(normalized.tests)}")
    for t in normalized.tests:
        ref_str = t.reference_range.raw if t.reference_range else "None"
        print(f"  - {t.test_name} ({t.raw_test_name}): val={t.value} unit={t.raw_unit} status={t.status} range={ref_str}")
    print(f"Profiles ({len(normalized.profiles)}): {[p.profile_name for p in normalized.profiles]}")
    print(f"Completeness: {normalized.completeness}")
    print(f"Warnings ({len(normalized.warnings)}): {normalized.warnings}")

if __name__ == "__main__":
    files = [
        "tests/fixtures/investigationlabreports.pdf",
        "tests/fixtures/Z615.pdf",
        "tests/fixtures/RCY.pdf",
        "tests/fixtures/Wellwise Platinum Profile - 5048.pdf",
    ]
    for f in files:
        try:
            process_file(f)
        except Exception as e:
            print(f"ERROR processing {f}: {e}")
