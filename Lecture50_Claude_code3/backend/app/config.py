"""All settings in one place. Values come from environment variables or backend/.env."""
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent

# Same limits as frontend/src/config/constants.js. The backend enforces them again.
MAX_FILE_SIZE_MB = 100
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
ALLOWED_EXTENSIONS = (".csv", ".xlsx")

# Folder-like prefixes inside the container
UPLOADS_PREFIX = "uploads"   # raw user files
REPORTS_PREFIX = "reports"   # things we generate (profile.json, plan.json)

# Dataset profile sent to the LLM
PROFILE_SAMPLE_ROWS = 5      # example rows included in the prompt
PROFILE_TOP_VALUES = 8       # most common values listed per categorical column
CATEGORICAL_MAX_UNIQUE = 50  # text columns with <= this many distinct values are categories

# Analysis plan
PLAN_MAX_ITEMS = 10
PROMPTS_DIR = BACKEND_DIR / "app" / "prompts"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=BACKEND_DIR / ".env", extra="ignore")

    blob_storage_connection_string: str
    anthropic_api_key: str
    llm_model: str = "claude-opus-5-5"
    upload_container: str = "course-files"
    sas_expiry_minutes: int = 10

    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]
    configure_storage_cors: bool = True  # adds a rule; never removes existing ones

    database_path: Path = BACKEND_DIR / "data" / "uploads.db"


@lru_cache
def get_settings() -> Settings:
    return Settings()
