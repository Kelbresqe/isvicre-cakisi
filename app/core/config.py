from enum import Enum
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(str, Enum):
    """Application environment enum."""

    DEV = "dev"
    STAGING = "staging"
    PROD = "prod"


class Settings(BaseSettings):
    """
    Centralized application settings using Pydantic BaseSettings.
    Reads from environment variables and .env file.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application Metadata
    PROJECT_NAME: str = "İsviçre Çakısı"
    VERSION: str = "1.2.0"
    ENV: Environment = Field(default=Environment.DEV, description="Runtime environment")

    # Directories
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    TEMP_DIR: Path = Field(
        default_factory=lambda: Path(__file__).resolve().parent.parent.parent / "temp"
    )

    # Redis Configuration (v1.0.0)
    REDIS_URL: str = Field(
        default="redis://localhost:6380/0", description="Redis connection URL"
    )
    REDIS_ENABLED: bool = Field(
        default=True, description="Enable Redis for caching and rate limiting"
    )
    REDIS_KEY_PREFIX: str = Field(
        default="isvicre:", description="Redis key prefix for namespacing"
    )
    REDIS_TTL_SECONDS: int = Field(
        default=3600, description="Default TTL for Redis keys in seconds"
    )

    # Security & Limits
    MAX_IMAGE_SIZE_MB: int = Field(
        default=10, description="Maximum image upload size in MB"
    )
    MAX_PDF_SIZE_MB: int = Field(
        default=25, description="Maximum PDF upload size in MB"
    )
    MAX_UPLOAD_SIZE_MB: int = Field(
        default=50, description="Default maximum upload size in MB for general files"
    )
    MAX_TEXT_INPUT_MB: int = Field(
        default=1, description="Maximum text input size in MB for dev tools"
    )

    # Rate Limiting (Phase 5)
    MAX_REQUESTS_PER_MINUTE: int = Field(
        default=60, description="Max requests per IP per minute"
    )
    MAX_UPLOAD_MB_PER_HOUR: int = Field(
        default=100, description="Max upload MB per IP per hour"
    )

    # SEO & Content (v0.7.0)
    SITE_NAME: str = Field(default="İsviçre Çakısı", description="Site name for SEO")
    SITE_TAGLINE: str = Field(
        default="Günlük Dijital İşler İçin Hepsi Bir Arada Araçlar",
        description="Site tagline",
    )
    DEFAULT_SEO_DESCRIPTION: str = Field(
        default="İsviçre Çakısı ile resim dönüştürme, PDF birleştirme, JSON formatlama ve daha fazlası. "
        "Ücretsiz, hızlı ve kullanımı kolay web araçları.",
        description="Default meta description for pages without specific SEO content",
    )
    TEXT_TOOL_CACHE_SIZE: int = Field(
        default=100, description="LRU cache size for text-based tools"
    )

    # CORS & Trusted Hosts
    TRUSTED_HOSTS: list[str] = Field(
        default_factory=lambda: ["localhost", "127.0.0.1", "*.vercel.app"],
        description="List of trusted host patterns",
    )
    CORS_ORIGINS: list[str] = Field(
        default_factory=lambda: ["http://localhost:3000", "http://localhost:8000"],
        description="Allowed CORS origins",
    )

    # Allowed MIME Types
    ALLOWED_IMAGE_MIME_TYPES: set[str] = Field(
        default_factory=lambda: {
            "image/jpeg",
            "image/png",
            "image/webp",
            "image/bmp",
            "image/tiff",
            "image/gif",
            "image/x-icon",
        },
        description="Whitelist of allowed image MIME types",
    )
    ALLOWED_PDF_MIME_TYPES: set[str] = Field(
        default_factory=lambda: {"application/pdf"},
        description="Whitelist of allowed PDF MIME types",
    )

    # FastAPI Configuration
    DEBUG: bool = Field(default=True, description="Enable debug mode")
    DOCS_ENABLED: bool = Field(default=True, description="Enable /docs endpoint")
    REDOC_ENABLED: bool = Field(default=True, description="Enable /redoc endpoint")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Ensure temp directory exists
        self.TEMP_DIR.mkdir(exist_ok=True)

    @property
    def is_dev(self) -> bool:
        """Check if running in development mode."""
        return self.ENV == Environment.DEV

    @property
    def is_prod(self) -> bool:
        """Check if running in production mode."""
        return self.ENV == Environment.PROD

    @property
    def docs_url(self) -> str | None:
        """Return docs URL based on environment and settings."""
        return "/docs" if self.DOCS_ENABLED and not self.is_prod else None

    @property
    def redoc_url(self) -> str | None:
        """Return redoc URL based on environment and settings."""
        return "/redoc" if self.REDOC_ENABLED and not self.is_prod else None


# Global settings instance
settings = Settings()
