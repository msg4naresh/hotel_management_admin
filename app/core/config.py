from typing import Annotated, Any

from pydantic import AnyHttpUrl, BeforeValidator, computed_field
from pydantic_settings import BaseSettings


def parse_cors(v: Any) -> list[str] | str:
    """Parse CORS origins from comma-separated string or list (FastAPI template pattern)"""
    if isinstance(v, str) and not v.startswith("["):
        return [i.strip() for i in v.split(",") if i.strip()]
    elif isinstance(v, list | str):
        return v
    raise ValueError(v)


class Settings(BaseSettings):
    # API Settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Hotel Management Admin"
    PORT: int = 8000  # Cloud Run compatibility

    # CORS - Supports both comma-separated string and list formats
    # Default includes all common development origins for React Native/Expo
    BACKEND_CORS_ORIGINS: Annotated[list[AnyHttpUrl] | str, BeforeValidator(parse_cors)] = [
        "http://localhost:3000",      # React/Next.js default
        "http://localhost:8080",      # Alternative dev port
        "http://localhost:19000",     # Expo default
        "http://localhost:19001",     # Expo alternative
        "http://localhost:19006",     # Expo web
        "http://localhost:8081",      # Metro bundler
    ]

    # Security (SECRET_KEY required, no default for production safety)
    SECRET_KEY: str = ""  # Must be set via environment variable
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    # Internal dev-only fallback (only used if TESTING=True)
    _DEV_SECRET_KEY: str = "DEV-KEY-INSECURE-TESTING-ONLY"

    # Database Configuration
    PG_HOST: str = "localhost"
    PG_PORT: str = "5432"
    PG_USERNAME: str = "postgres"
    PG_PASSWORD: str = "postgres"
    PG_DB: str = "hotel_management"
    PG_SCHEMA: str = "public"

    # AWS S3 Configuration
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_S3_BUCKET_NAME: str = "hotel-management-uploads"
    AWS_S3_REGION: str = "us-east-1"

    # File Upload Configuration
    MAX_FILE_SIZE: int = 10485760  # 10MB
    ALLOWED_FILE_TYPES: list[str] = ["application/pdf", "image/jpeg", "image/png"]
    ALLOWED_EXTENSIONS: list[str] = ["pdf", "jpg", "jpeg", "png"]

    # Testing flag
    TESTING: bool = False  # Default to production mode

    # Sentry (Error Tracking)
    SENTRY_DSN: str = ""  # Only initializes if set
    ENVIRONMENT: str = "development"  # development, staging, production

    @computed_field  # type: ignore[prop-decorator]
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        return f"postgresql+psycopg2://{self.PG_USERNAME}:{self.PG_PASSWORD}@{self.PG_HOST}:{self.PG_PORT}/{self.PG_DB}?options=-csearch_path%3D{self.PG_SCHEMA}"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def VALIDATED_SECRET_KEY(self) -> str:
        """Validate SECRET_KEY and prevent production usage of dev key"""
        if not self.SECRET_KEY:
            if self.TESTING:
                return self._DEV_SECRET_KEY
            raise ValueError("SECRET_KEY must be set in production environment")

        # Prevent default "changethis" value (FastAPI template pattern)
        if self.SECRET_KEY == "changethis" and self.ENVIRONMENT == "production":
            raise ValueError("Cannot use default SECRET_KEY 'changethis' in production")

        if self.SECRET_KEY == self._DEV_SECRET_KEY and self.ENVIRONMENT == "production":
            raise ValueError("Cannot use development SECRET_KEY in production")

        if len(self.SECRET_KEY) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters")

        return self.SECRET_KEY

    class Config:
        env_file = ".env"
        case_sensitive = False  # Allow AWS_ACCESS_KEY_ID or aws_access_key_id


settings = Settings()
