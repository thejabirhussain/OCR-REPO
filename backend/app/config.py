"""Application configuration using Pydantic Settings."""

from functools import lru_cache
from pathlib import Path
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Application
    api_host: str = Field(default="0.0.0.0", alias="API_HOST")
    api_port: int = Field(default=8000, alias="API_PORT")
    debug: bool = Field(default=False, alias="DEBUG")
    secret_key: str = Field(default="change-me-in-production", alias="SECRET_KEY")
    allowed_origins: List[str] = Field(
        default=["http://localhost:5173", "http://localhost:3000"],
        alias="ALLOWED_ORIGINS",
    )

    # Database
    database_url: str = Field(
        default="postgresql://user:password@postgres:5432/arabic_ocr",
        alias="DATABASE_URL",
    )

    # Redis
    redis_url: str = Field(default="redis://redis:6379/0", alias="REDIS_URL")

    # File Upload
    max_file_size_mb: int = Field(default=50, alias="MAX_FILE_SIZE_MB")
    upload_dir: Path = Field(default=Path("/uploads"), alias="UPLOAD_DIR")
    model_path: Path = Field(default=Path("/models"), alias="MODEL_PATH")

    # OCR Configuration
    ocr_engine: str = Field(default="paddleocr", alias="OCR_ENGINE")
    use_tesseract_fallback: bool = Field(default=True, alias="USE_TESSERACT_FALLBACK")
    tesseract_lang: str = Field(default="ara", alias="TESSERACT_LANG")

    # Translation Configuration
    translation_model: str = Field(
        default="facebook/nllb-200-3.3B",
        alias="TRANSLATION_MODEL",
    )
    source_language: str = Field(default="ara_Arab", alias="SOURCE_LANGUAGE")
    target_language: str = Field(default="eng_Latn", alias="TARGET_LANGUAGE")
    batch_size: int = Field(default=32, alias="BATCH_SIZE")
    max_length: int = Field(default=512, alias="MAX_LENGTH")

    # Job Configuration
    job_timeout_minutes: int = Field(default=30, alias="JOB_TIMEOUT_MINUTES")
    celery_broker_url: str = Field(default="redis://redis:6379/0", alias="CELERY_BROKER_URL")
    celery_result_backend: str = Field(
        default="redis://redis:6379/0",
        alias="CELERY_RESULT_BACKEND",
    )

    # Logging
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    def __init__(self, **kwargs):
        """Initialize settings and create directories."""
        super().__init__(**kwargs)
        # Ensure directories exist
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.model_path.mkdir(parents=True, exist_ok=True)

    @property
    def max_file_size_bytes(self) -> int:
        """Get max file size in bytes."""
        return self.max_file_size_mb * 1024 * 1024

    @property
    def allowed_file_extensions(self) -> List[str]:
        """Get allowed file extensions."""
        return [".pdf", ".docx", ".jpg", ".jpeg", ".png", ".tiff", ".tif"]


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()

