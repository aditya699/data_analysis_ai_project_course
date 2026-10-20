"""Everything that talks to Azure Blob Storage (or Azurite locally)."""
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from azure.core.exceptions import ResourceExistsError, ResourceNotFoundError
from azure.storage.blob import (
    BlobSasPermissions,
    BlobServiceClient,
    ContentSettings,
    CorsRule,
    generate_blob_sas,
)

from app.config import Settings


@dataclass
class SignedUpload:
    url: str
    expires_at: datetime


class BlobStorage:
    def __init__(self, settings: Settings):
        self._settings = settings
        self._service = BlobServiceClient.from_connection_string(
            settings.blob_storage_connection_string
        )
        self._container = self._service.get_container_client(settings.upload_container)

    def ensure_ready(self) -> None:
        """Create the container if needed and (optionally) let the browser PUT into it."""
        try:
            self._container.create_container()
        except ResourceExistsError:
            pass

        if self._settings.configure_storage_cors:
            self._add_cors_rule()

    def _add_cors_rule(self) -> None:
        """Add a rule for our frontend origins, keeping any rules already on the account.

        CORS is set per storage account (Blob service), not per container.
        """
        existing = self._service.get_service_properties()["cors"]
        wanted = set(self._settings.cors_origins)
        for rule in existing:
            origins = set(rule.allowed_origins.split(","))
            if wanted <= origins and "PUT" in rule.allowed_methods.split(","):
                return  # already allowed

        rule = CorsRule(
            allowed_origins=self._settings.cors_origins,
            allowed_methods=["PUT", "OPTIONS"],
            allowed_headers=["*"],
            exposed_headers=["*"],
            max_age_in_seconds=3600,
        )
        self._service.set_service_properties(cors=[*existing, rule])

    def create_upload_url(self, blob_name: str) -> SignedUpload:
        """A short-lived URL that allows writing this one blob, nothing else."""
        expires_at = datetime.now(timezone.utc) + timedelta(
            minutes=self._settings.sas_expiry_minutes
        )
        sas_token = generate_blob_sas(
            account_name=self._service.account_name,
            container_name=self._settings.upload_container,
            blob_name=blob_name,
            account_key=self._service.credential.account_key,
            permission=BlobSasPermissions(create=True, write=True),
            expiry=expires_at,
        )
        blob_url = self._container.get_blob_client(blob_name).url
        return SignedUpload(url=f"{blob_url}?{sas_token}", expires_at=expires_at)

    def get_blob_size(self, blob_name: str) -> int | None:
        """Size in bytes, or None if the blob does not exist."""
        try:
            return self._container.get_blob_client(blob_name).get_blob_properties().size
        except ResourceNotFoundError:
            return None

    def download_bytes(self, blob_name: str) -> bytes | None:
        """Whole blob in memory (fine for now; see CLAUDE.md on large files)."""
        try:
            return self._container.get_blob_client(blob_name).download_blob().readall()
        except ResourceNotFoundError:
            return None

    def upload_text(self, blob_name: str, text: str, content_type: str) -> None:
        self._container.get_blob_client(blob_name).upload_blob(
            text.encode("utf-8"),
            overwrite=True,
            content_settings=ContentSettings(content_type=content_type),
        )

    def delete_blob(self, blob_name: str) -> None:
        try:
            self._container.delete_blob(blob_name)
        except ResourceNotFoundError:
            pass
