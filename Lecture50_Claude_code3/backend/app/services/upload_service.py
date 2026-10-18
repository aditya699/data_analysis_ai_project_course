"""The upload flow: validate -> hand out a signed URL -> verify the blob arrived."""
import uuid

from app.config import MAX_FILE_SIZE_BYTES, MAX_FILE_SIZE_MB
from app.schemas import CreateUploadRequest, CreateUploadResponse, UploadInfo
from app.services.blob_storage import BlobStorage
from app.services.upload_registry import UploadRegistry
from app.utils.file_rules import build_blob_name, get_extension, validate_upload_request


class UploadError(Exception):
    """The request breaks an upload rule (400)."""


class UploadNotFound(Exception):
    """No upload with that id (404)."""


class UploadService:
    def __init__(self, storage: BlobStorage, registry: UploadRegistry):
        self._storage = storage
        self._registry = registry

    def create_upload(self, request: CreateUploadRequest) -> CreateUploadResponse:
        error = validate_upload_request(request.filename, request.size_bytes)
        if error:
            raise UploadError(error)

        upload_id = uuid.uuid4().hex
        blob_name = build_blob_name(upload_id, get_extension(request.filename))
        self._registry.create(
            upload_id=upload_id,
            original_filename=request.filename,
            size_bytes=request.size_bytes,
            content_type=request.content_type,
            blob_name=blob_name,
        )
        signed = self._storage.create_upload_url(blob_name)
        return CreateUploadResponse(
            upload_id=upload_id,
            upload_url=signed.url,
            upload_headers={
                "x-ms-blob-type": "BlockBlob",  # required by Azure for a single PUT
                "Content-Type": request.content_type,
            },
            expires_at=signed.expires_at,
        )

    def complete_upload(self, upload_id: str) -> UploadInfo:
        upload = self.get_upload(upload_id)
        if upload.status == "uploaded":
            return upload

        actual_size = self._storage.get_blob_size(upload.blob_name)
        if actual_size is None:
            raise UploadError("The file has not reached storage yet. Upload it, then try again.")

        # A signed URL can't limit size, so check what actually arrived.
        if actual_size > MAX_FILE_SIZE_BYTES or actual_size != upload.size_bytes:
            self._storage.delete_blob(upload.blob_name)
            message = (
                f"File is larger than {MAX_FILE_SIZE_MB} MB."
                if actual_size > MAX_FILE_SIZE_BYTES
                else f"Expected {upload.size_bytes} bytes but storage has {actual_size}."
            )
            self._registry.mark_failed(upload_id, message)
            raise UploadError(message)

        return self._registry.mark_uploaded(upload_id)

    def get_upload(self, upload_id: str) -> UploadInfo:
        upload = self._registry.get(upload_id)
        if upload is None:
            raise UploadNotFound(f"Upload {upload_id} not found.")
        return upload
