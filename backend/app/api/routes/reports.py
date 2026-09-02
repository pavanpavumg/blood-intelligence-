from fastapi import APIRouter, UploadFile, File, status
from app.schemas.report import ReportUploadResponse
from app.services.document_service import DocumentService

router = APIRouter()

@router.post(
    "/upload",
    response_model=ReportUploadResponse,
    status_code=status.HTTP_200_OK,
    summary="Upload & Extract Blood Test Report",
    description="Uploads a blood test report (PDF, PNG, JPG, JPEG) and extracts structured laboratory data without using an LLM."
)
async def upload_report(
    file: UploadFile = File(..., description="Report document file (PDF or Image)")
) -> ReportUploadResponse:
    """
    Handles report upload, document type detection, OCR preprocessing, non-LLM field parsing,
    and returns validated v1.0 JSON payload.
    """
    return await DocumentService.process_uploaded_report(file)
