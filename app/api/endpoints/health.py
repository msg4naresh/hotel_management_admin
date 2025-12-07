import logging

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import text

from app.api.dependencies.common import SessionDep

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/health")
async def health():
    """Liveness probe - is the service running?"""
    return {"status": "ok"}


@router.get("/health/ready")
def health_ready(session: SessionDep):
    """Readiness probe - can the service handle requests?"""
    try:
        session.execute(text("SELECT 1"))
        return {"status": "ready", "database": "connected"}
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Service unavailable") from e
