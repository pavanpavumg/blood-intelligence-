import os
import time
import cv2

os.environ["FLAGS_enable_pir_api"] = "0"
os.environ["FLAGS_use_mkldnn"] = "0"

from paddleocr import PaddleOCR

print("Starting OCR initialization...")
start = time.time()

ocr = PaddleOCR(
    lang="en",
    enable_mkldnn=False,
    use_doc_orientation_classify=False,
    use_doc_unwarping=False,
    use_textline_orientation=False,
)

print(f"OCR initialized in {time.time() - start:.2f} seconds")

image_path = r"C:\Users\TezHealth\Desktop\blood-test-intelligence\backend\test_page.png"

image = cv2.imread(image_path)

if image is None:
    raise RuntimeError("Could not load image")

print("Starting OCR inference...")
start = time.time()

result = list(ocr.predict(image))

print(f"OCR completed in {time.time() - start:.2f} seconds")
print("Result:", result)
