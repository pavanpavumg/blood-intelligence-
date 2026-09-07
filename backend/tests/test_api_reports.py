import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_upload_pdf_report_success(
    async_client: AsyncClient, sample_pdf_bytes: bytes
):
    files = {"file": ("blood_test_report.pdf", sample_pdf_bytes, "application/pdf")}

    response = await async_client.post("/api/reports/upload", files=files)
    assert response.status_code == 200

    body = response.json()
    assert "report_id" in body
    assert body["status"] in ["VALIDATED", "VALIDATED_WITH_WARNINGS", "EXTRACTED"]

    data = body["data"]
    assert data["schema_version"] == "2.1"
    assert data["patient"]["name"] == "John Doe"
    assert data["patient"]["age"] == 45
    assert data["patient"]["gender"] == "Male"

    tests = data["tests"]
    assert len(tests) >= 5

    # Check normalized attributes on Fasting Blood Glucose
    t0 = next(t for t in tests if t["raw_test_name"] == "Fasting Blood Glucose")
    assert t0["raw_test_name"] == "Fasting Blood Glucose"
    assert t0["loinc_code"] == "1558-6"
    assert t0["value"] == 95.0
    assert t0["status"] == "NORMAL"
    assert t0["flag"] == "NONE"


@pytest.mark.asyncio
async def test_upload_image_report_success(
    async_client: AsyncClient, sample_image_bytes: bytes
):
    files = {"file": ("blood_report_scanned.png", sample_image_bytes, "image/png")}

    response = await async_client.post("/api/reports/upload", files=files)
    assert response.status_code == 200

    body = response.json()
    assert body["status"] in ["VALIDATED", "VALIDATED_WITH_WARNINGS", "EXTRACTED"]
    assert "report_id" in body


@pytest.mark.asyncio
async def test_upload_invalid_file_extension(async_client: AsyncClient):
    files = {
        "file": (
            "unsupported_file.docx",
            b"dummy content",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
    }

    response = await async_client.post("/api/reports/upload", files=files)
    assert response.status_code in (400, 415)
    data = response.json()
    assert "Unsupported file" in data["detail"]
