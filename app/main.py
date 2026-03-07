import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware

from app.api.routes import api_router
from app.core.config import settings
from app.core.logging import setup_logging

# Initialize logging
setup_logging()

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware to add security headers to all responses"""

    async def dispatch(self, request, call_next):
        response = await call_next(request)
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # HSTS only in production with HTTPS
        if settings.ENVIRONMENT == "production":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        # CSP: Allow Swagger UI resources in development, restrictive in production
        if settings.ENVIRONMENT == "development":
            # Allow Swagger UI CDN resources and inline scripts for /docs endpoints
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
                "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
                "img-src 'self' https://fastapi.tiangolo.com data:; "
                "frame-ancestors 'none'"
            )
        else:
            # Restrictive CSP for production API
            response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'"

        return response


# Initialize Sentry for error tracking (only if DSN is configured)
if settings.SENTRY_DSN:
    import sentry_sdk
    from sentry_sdk.integrations.fastapi import FastApiIntegration
    from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        environment=settings.ENVIRONMENT,
        traces_sample_rate=1.0 if settings.ENVIRONMENT == "development" else 0.1,
        profiles_sample_rate=1.0 if settings.ENVIRONMENT == "development" else 0.1,
        integrations=[
            FastApiIntegration(),
            SqlalchemyIntegration(),
        ],
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: validate critical security settings
    try:
        _ = settings.VALIDATED_SECRET_KEY  # Raises if invalid
        logger.info("SECRET_KEY validation passed")
    except ValueError as e:
        logger.error(f"SECRET_KEY validation failed: {e}")
        raise

    storage_mode = settings.RESOLVED_STORAGE_MODE
    logger.info(f"Storage mode: {storage_mode}")

    if storage_mode == "s3":
        if not settings.AWS_ACCESS_KEY_ID or not settings.AWS_SECRET_ACCESS_KEY:
            if settings.ENVIRONMENT == "production":
                logger.error("AWS credentials must be configured in production")
                raise ValueError("AWS credentials must be configured in production")
            logger.warning("AWS credentials not configured - S3 operations will fail")
    else:
        # Local storage — ensure upload directory exists
        upload_dir = Path(settings.LOCAL_UPLOAD_DIR)
        upload_dir.mkdir(parents=True, exist_ok=True)
        # Set the base URL for serving static uploads if not explicitly set
        if not settings.LOCAL_UPLOAD_BASE_URL:
            settings.LOCAL_UPLOAD_BASE_URL = f"http://0.0.0.0:{settings.PORT}/uploads"
        logger.info(f"Local uploads dir: {upload_dir} | URL: {settings.LOCAL_UPLOAD_BASE_URL}")

    yield
    # Shutdown: cleanup if needed


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="API for RS Residency",
    version="1.0.0",
    docs_url=f"{settings.API_V1_STR}/docs",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)

# Add security headers middleware
app.add_middleware(SecurityHeadersMiddleware)

# Set all CORS enabled origins
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin).rstrip("/") for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization", "Accept"],
        expose_headers=["Content-Type", "X-Total-Count"],
    )

# Include the API router
app.include_router(api_router, prefix=settings.API_V1_STR)

# Mount local upload directory as static files when using local storage
if settings.RESOLVED_STORAGE_MODE == "local":
    _upload_dir = Path(settings.LOCAL_UPLOAD_DIR)
    _upload_dir.mkdir(parents=True, exist_ok=True)
    app.mount("/uploads", StaticFiles(directory=str(_upload_dir)), name="uploads")


@app.get("/")
def read_root():
    return {"message": "Welcome to RS Residency!"}
