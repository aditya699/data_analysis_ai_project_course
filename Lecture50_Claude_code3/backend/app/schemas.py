"""Request and response shapes for the API."""
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

UploadStatus = Literal["pending", "uploaded", "failed"]


class CreateUploadRequest(BaseModel):
    filename: str = Field(min_length=1, max_length=255, examples=["upi_transactions.csv"])
    size_bytes: int = Field(examples=[4_812_345])
    content_type: str = Field(default="application/octet-stream", max_length=200)


class CreateUploadResponse(BaseModel):
    upload_id: str
    upload_url: str = Field(description="Signed URL. PUT the file here, directly to blob storage.")
    upload_method: Literal["PUT"] = "PUT"
    upload_headers: dict[str, str] = Field(description="Headers the PUT request must send.")
    expires_at: datetime


class UploadInfo(BaseModel):
    upload_id: str
    original_filename: str
    size_bytes: int
    content_type: str
    blob_name: str
    status: UploadStatus
    error: str | None = None
    created_at: datetime
    uploaded_at: datetime | None = None
