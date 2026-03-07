from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.refresh_token import RefreshTokenDB


def create_refresh_token(db: Session, *, user_id: int, token: str, expires_at: datetime) -> RefreshTokenDB:
    """Create a new refresh token record."""
    db_obj = RefreshTokenDB(
        token=token,
        user_id=user_id,
        expires_at=expires_at,
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def get_by_token(db: Session, *, token: str) -> RefreshTokenDB | None:
    """Get a refresh token record by token string."""
    return db.query(RefreshTokenDB).filter(RefreshTokenDB.token == token).first()


def revoke_token(db: Session, *, db_obj: RefreshTokenDB) -> RefreshTokenDB:
    """Revoke a single refresh token."""
    db_obj.is_revoked = True
    db.commit()
    db.refresh(db_obj)
    return db_obj


def revoke_all_for_user(db: Session, *, user_id: int) -> int:
    """Revoke all active refresh tokens for a user. Returns count of revoked tokens."""
    count = (
        db.query(RefreshTokenDB)
        .filter(
            RefreshTokenDB.user_id == user_id,
            RefreshTokenDB.is_revoked == False,  # noqa: E712
        )
        .update({"is_revoked": True})
    )
    db.commit()
    return count


def is_valid(db_obj: RefreshTokenDB) -> bool:
    """Check if a refresh token is valid (not revoked and not expired)."""
    if db_obj.is_revoked:
        return False
    if db_obj.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        return False
    return True
