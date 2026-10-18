"""Builds shared service objects once and hands them to routes via Depends()."""
from functools import lru_cache

from app.config import get_settings
from app.services.blob_storage import BlobStorage
from app.services.upload_registry import UploadRegistry
from app.services.upload_service import UploadService


@lru_cache
def get_blob_storage() -> BlobStorage:
    return BlobStorage(get_settings())


@lru_cache
def get_upload_service() -> UploadService:
    return UploadService(get_blob_storage(), UploadRegistry(get_settings().database_path))
