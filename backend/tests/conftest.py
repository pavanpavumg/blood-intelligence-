import pytest
import fitz  # PyMuPDF
import cv2
import numpy as np
from typing import AsyncGenerator
from httpx import AsyncClient, ASGITransport
from pathlib import Path

from app.main import app

@pytest.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """
    Async TestClient fixture for FastAPI endpoints.
    """
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver"
    ) as client:
        yield client

@pytest.fixture
def sample_pdf_bytes() -> bytes:
    """
    Generates a valid digital PDF blood report fixture in memory using PyMuPDF.
    """
    doc = fitz.open()
    page = doc.new_page()
    
    text = (
        "Quest Diagnostics Lab Report\n"
        "Patient Name: John Doe\n"
        "Age: 45 Years\n"
        "Gender: Male\n"
        "Report Date: 2026-08-24\n"
        "Patient ID: P-98765\n"
        "\n"
        "LABORATORY TEST RESULTS:\n"
        "Fasting Blood Glucose 95 mg/dL 70 - 100\n"
        "Hemoglobin A1c 5.8 % 4.0 - 5.6\n"
        "Thyroid Stimulating Hormone 2.45 uIU/mL 0.45 - 4.5\n"
        "Total Cholesterol 185 mg/dL < 200\n"
        "HDL Cholesterol 48 mg/dL > 40\n"
        "Triglycerides 135 mg/dL < 150\n"
    )
    
    page.insert_text((50, 50), text, fontsize=12)
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes

@pytest.fixture
def sample_image_bytes() -> bytes:
    """
    Generates a valid blood report image fixture (PNG) using OpenCV.
    """
    # Create white canvas (800x600)
    img = np.full((600, 800, 3), 255, dtype=np.uint8)
    
    lines = [
        "Metropolis Health Laboratory",
        "Patient Name: Alice Smith",
        "Age: 32  Gender: Female",
        "Date: 2026-08-24",
        "Fasting Glucose 92 mg/dL 70-100",
        "Total Cholesterol 175 mg/dL < 200"
    ]
    
    y = 50
    for line in lines:
        cv2.putText(img, line, (40, y), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
        y += 45
        
    is_success, buffer = cv2.imencode(".png", img)
    return buffer.tobytes()
