from pydantic_settings import BaseSettings
import os
from typing import List

class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-actual-secure-random-key-here")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

    # S3 Configuration
    AWS_ACCESS_KEY_ID: str = os.getenv("AWS_ACCESS_KEY_ID", "")
    AWS_SECRET_ACCESS_KEY: str = os.getenv("AWS_SECRET_ACCESS_KEY", "")
    AWS_S3_BUCKET_NAME: str = os.getenv("AWS_S3_BUCKET_NAME", "hotel-management-uploads")
    AWS_S3_REGION: str = os.getenv("AWS_S3_REGION", "us-east-1")

    # File Configuration
    MAX_FILE_SIZE: int = int(os.getenv("MAX_FILE_SIZE", "10485760"))  # 10MB default
    # Single source of truth for allowed file types (extension -> MIME type mapping)
    ALLOWED_FILE_TYPES: List[str] = ["application/pdf", "image/jpeg", "image/png"]
    ALLOWED_EXTENSIONS: List[str] = ["pdf", "jpg", "jpeg", "png"]

    class Config:
        env_file = ".env"

settings = Settings()