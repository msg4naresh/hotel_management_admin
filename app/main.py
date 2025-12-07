from fastapi import FastAPI
from app.core.config import settings
from app.db.init_db import init_db
from app.api.routes import api_router
from app.core.logging import setup_logging

# Initialize logging
setup_logging()

app = FastAPI(
    title="RS Residency API",
    description="API for RS Residency",
    version="1.0.0",
    docs_url=f"{settings.API_V1_STR}/docs",
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Include the API router
app.include_router(api_router, prefix=settings.API_V1_STR)

# Initialize database tables (skip during testing)
if not settings.TESTING:
    init_db()


@app.get("/")
def read_root():
    return {"message": "Welcome to RS Residency!"}