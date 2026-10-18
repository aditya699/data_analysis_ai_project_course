"""HTTP endpoints for uploads. Thin: translate HTTP <-> UploadService, nothing else."""
from fastapi import APIRouter, Depends, HTTPException, status

from app.dependencies import get_upload_service
from app.schemas import CreateUploadRequest, CreateUploadResponse, UploadInfo
from app.services.upload_service import UploadError, UploadNotFound, UploadService

router = APIRouter(prefix="/api/uploads", tags=["uploads"])


@router.post("", response_model=CreateUploadResponse, status_code=status.HTTP_201_CREATED)
def create_upload(
    request: CreateUploadRequest, service: UploadService = Depends(get_upload_service)
):
    """Step 1: check the file details and return a signed URL to PUT the file to."""
    try:
        return service.create_upload(request)
    except UploadError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc))


@router.post("/{upload_id}/complete", response_model=UploadInfo)
def complete_upload(upload_id: str, service: UploadService = Depends(get_upload_service)):
    """Step 2: after the browser's PUT, confirm the file is really in storage."""
    try:
        return service.complete_upload(upload_id)
    except UploadNotFound as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc))
    except UploadError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc))


@router.get("/{upload_id}", response_model=UploadInfo)
def get_upload(upload_id: str, service: UploadService = Depends(get_upload_service)):
    try:
        return service.get_upload(upload_id)
    except UploadNotFound as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc))
