"""Builds shared service objects once and hands them to routes via Depends()."""
from functools import lru_cache

from app.config import get_settings
from app.services.analysis_planner import AnalysisPlanner
from app.services.blob_storage import BlobStorage
from app.services.llm_client import LLMClient
from app.services.upload_registry import UploadRegistry
from app.services.upload_service import UploadService


@lru_cache
def get_blob_storage() -> BlobStorage:
    return BlobStorage(get_settings())


@lru_cache
def get_upload_registry() -> UploadRegistry:
    return UploadRegistry(get_settings().database_path)


@lru_cache
def get_upload_service() -> UploadService:
    return UploadService(get_blob_storage(), get_upload_registry())


@lru_cache
def get_analysis_planner() -> AnalysisPlanner:
    return AnalysisPlanner(get_blob_storage(), get_upload_registry(), LLMClient(get_settings()))
