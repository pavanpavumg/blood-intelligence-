from fastapi import APIRouter, UploadFile, File, status
from app.schemas.report import ReportUploadResponse
from app.services.document_service import DocumentService

router = APIRouter()

@router.post(
    "/upload",
    response_model=ReportUploadResponse,
    status_code=status.HTTP_200_OK,
    summary="Upload & Extract Blood Test Report (v1 Alias)",
    description="Synchronous report processing endpoint delegating directly to DocumentService."
)
async def upload_lab_report(
    file: UploadFile = File(...)
) -> ReportUploadResponse:
    """
    Delegates to authoritative DocumentService pipeline.
    """
    return await DocumentService.process_uploaded_report(file)
