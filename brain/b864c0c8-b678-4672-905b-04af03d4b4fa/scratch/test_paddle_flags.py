import fitz
import cv2
import numpy as np
from paddleocr import PaddleOCR

def test_ocr():
    doc = fitz.open("tests/fixtures/investigationlabreports.pdf")
    page = doc[0]
    pix = page.get_pixmap(dpi=150)
    img_bytes = pix.tobytes("png")
    nparr = np.frombuffer(img_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    print("Testing PaddleOCR(enable_mkldnn=False)...")
    try:
        ocr = PaddleOCR(enable_mkldnn=False)
        res = ocr.ocr(img)
        print("Success! Result len:", len(res))
    except Exception as e:
        print("Failed with enable_mkldnn=False:", e)

    print("\nTesting PaddleOCR(use_gpu=False)...")
    try:
        ocr2 = PaddleOCR(use_gpu=False)
        res2 = ocr2.ocr(img)
        print("Success with use_gpu=False! Result len:", len(res2))
    except Exception as e:
        print("Failed with use_gpu=False:", e)

if __name__ == "__main__":
    test_ocr()
