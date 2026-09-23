import os
import sys
import json
import time
import requests
from pathlib import Path

FIXTURES_DIR = Path(r"C:\Users\TezHealth\Desktop\blood-test-intelligence\backend\tests\fixtures")

TEST_FILES = [
    "Mr.JAYACHANDRAN_KAD393.4 (3).PDF",
    "CBC-with-ESR-test-report-format-example-sample-template-Drlogy-lab-report.pdf",
    "Mrs.LILLY RICHARD_KAD393.2 (1).PDF",
    "Sample-Lab-Report-DBTICBM.pdf",
    "Wellwise Platinum Profile - 5048.pdf",
    "RCY.pdf",
]

API_URL = "http://127.0.0.1:8000/api/reports/upload"

def run_batch_test():
    print(f"==================================================")
    print(f"BATCH REPORT PARSER VERIFICATION (6 REPORTS)")
    print(f"API Endpoint: {API_URL}")
    print(f"==================================================\n")

    summary_results = []

    for filename in TEST_FILES:
        filepath = FIXTURES_DIR / filename
        if not filepath.exists():
            print(f"[MISSING] {filename}")
            continue

        size_kb = filepath.stat().st_size / 1024
        print(f"--> Processing: {filename} ({size_kb:.1f} KB)...")
        start_t = time.time()
        
        try:
            with open(filepath, "rb") as f:
                files = {"file": (filename, f, "application/pdf")}
                # RCY is 12 pages, allow up to 180s timeout
                timeout_sec = 180 if "RCY" in filename else 90
                resp = requests.post(API_URL, files=files, timeout=timeout_sec)
                
            elapsed = time.time() - start_t
            
            if resp.status_code != 200:
                print(f"    [FAIL] HTTP {resp.status_code}: {resp.text[:200]}")
                summary_results.append({
                    "file": filename,
                    "status": f"HTTP {resp.status_code}",
                    "tests": 0,
                    "elapsed": f"{elapsed:.2f}s"
                })
                continue

            resp_json = resp.json()
            data = resp_json.get("data", resp_json)
            patient = data.get("patient_info", {})
            tests = data.get("tests", [])
            profiles = data.get("profiles", {})
            metadata = data.get("metadata", {})
            warnings = data.get("warnings", [])
            
            # Count statuses
            normal_count = sum(1 for t in tests if t.get("status") == "NORMAL")
            abnormal_count = sum(1 for t in tests if t.get("status") in ["HIGH", "LOW", "CRITICAL", "POSITIVE"])
            unknown_count = sum(1 for t in tests if t.get("status") == "UNKNOWN")
            red_flag_count = sum(1 for t in tests if t.get("flag") == "RED_FLAG")
            review_count = sum(1 for t in tests if t.get("flag") == "REVIEW_REQUIRED")
            none_flag_count = sum(1 for t in tests if t.get("flag") == "NONE")
            
            sample_tests = [
                f"{t.get('test_name')}: {t.get('value')} {t.get('raw_unit') or ''} ({t.get('status')})"
                for t in tests[:5]
            ]
            
            res = {
                "file": filename,
                "status": "SUCCESS (200 OK)",
                "elapsed": f"{elapsed:.2f}s",
                "patient_name": patient.get("name") or "N/A",
                "patient_age": patient.get("age") or "N/A",
                "patient_gender": patient.get("gender") or "N/A",
                "lab_name": metadata.get("lab_name") or "N/A",
                "total_tests": len(tests),
                "normal": normal_count,
                "abnormal": abnormal_count,
                "unknown": unknown_count,
                "red_flags": red_flag_count,
                "review_required": review_count,
                "flag_none": none_flag_count,
                "profiles_detected": list(profiles.keys()) if isinstance(profiles, dict) else [],
                "warnings_count": len(warnings),
                "sample_tests": sample_tests
            }
            summary_results.append(res)
            
            print(f"    [OK] Extracted {len(tests)} Tests | Elapsed: {elapsed:.2f}s")
            print(f"         Patient: {res['patient_name']} | Age: {res['patient_age']} | Gender: {res['patient_gender']} | Lab: {res['lab_name']}")
            print(f"         Breakdown: {normal_count} Normal | {abnormal_count} Abnormal | {unknown_count} Unknown | {review_count} Review Required")
            print(f"         Profiles ({len(res['profiles_detected'])}): {', '.join(res['profiles_detected'][:5])}")
            print(f"         Sample tests: {sample_tests[:3]}")
            print()
            
        except Exception as e:
            print(f"    [ERROR] Exception: {e}")
            summary_results.append({
                "file": filename,
                "status": f"ERROR: {e}",
                "tests": 0,
                "elapsed": "N/A"
            })

    print(f"\n==================================================")
    print(f"FINAL CONSOLIDATED BATCH TEST RESULTS (SUMMARY TABLE)")
    print(f"==================================================")
    header = f"{'Filename':<35} | {'Status':<12} | {'Tests':<6} | {'Normal':<6} | {'Abnorm':<6} | {'Time':<7}"
    print(header)
    print("-" * len(header))
    for r in summary_results:
        f_short = r["file"][:33]
        st = r.get("status", "")[:12]
        tot = str(r.get("total_tests", 0))
        norm = str(r.get("normal", 0))
        abn = str(r.get("abnormal", 0))
        el = r.get("elapsed", "N/A")
        print(f"{f_short:<35} | {st:<12} | {tot:<6} | {norm:<6} | {abn:<6} | {el:<7}")
    
    out_file = Path(r"C:\Users\TezHealth\Desktop\blood-test-intelligence\backend\batch_test_summary.json")
    with open(out_file, "w") as f:
        json.dump(summary_results, f, indent=2)
    print(f"\nSaved detailed summary JSON to: {out_file}")

if __name__ == "__main__":
    run_batch_test()
