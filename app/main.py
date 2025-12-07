from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes import api_router
from app.core.config import settings
from app.core.logging import setup_logging

# Initialize logging
setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: logging is already set up, can add DB checks here
    yield
    # Shutdown: cleanup if needed


app = FastAPI(
    title="RS Residency API",
    description="API for RS Residency",
    version="1.0.0",
    docs_url=f"{settings.API_V1_STR}/docs",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)

# Include the API router
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/")
def read_root():
    return {"message": "Welcome to RS Residency!"}
