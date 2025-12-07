from typing import List, Union

from pydantic import AnyHttpUrl, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # API Settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Hotel Management Admin"
    # CORS
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []

    # Security (SECRET_KEY required in production, has dev default)
    SECRET_KEY: str = "DEV-KEY-INSECURE-CHANGE-IN-PRODUCTION"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

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

    @computed_field
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        return f"postgresql+psycopg2://{self.PG_USERNAME}:{self.PG_PASSWORD}@{self.PG_HOST}:{self.PG_PORT}/{self.PG_DB}?options=-csearch_path%3D{self.PG_SCHEMA}"

    class Config:
        env_file = ".env"
        case_sensitive = False  # Allow AWS_ACCESS_KEY_ID or aws_access_key_id


settings = Settings()
