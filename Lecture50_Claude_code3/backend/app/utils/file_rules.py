"""Pure helpers for upload rules. No FastAPI, no Azure."""
from pathlib import PurePath

from app.config import ALLOWED_EXTENSIONS, MAX_FILE_SIZE_BYTES, MAX_FILE_SIZE_MB, UPLOADS_PREFIX


def get_extension(filename: str) -> str:
    return PurePath(filename).suffix.lower()


def validate_upload_request(filename: str, size_bytes: int) -> str | None:
    """Return an error message, or None if the file is allowed."""
    if not filename.strip():
        return "File name is missing."
    if get_extension(filename) not in ALLOWED_EXTENSIONS:
        return f"Only {', '.join(ALLOWED_EXTENSIONS)} files are allowed."
    if size_bytes <= 0:
        return "The file is empty."
    if size_bytes > MAX_FILE_SIZE_BYTES:
        return f"File is larger than {MAX_FILE_SIZE_MB} MB."
    return None


def build_blob_name(upload_id: str, extension: str) -> str:
    # Never use the user's file name as the key: names clash and can be unsafe.
    return f"{UPLOADS_PREFIX}/{upload_id}/original{extension}"
