import logging

from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.db.base_db import SessionLocal
from app.models.users import UserDB

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def init_db(db: Session) -> None:
    # Check if we already have users
    user = db.query(UserDB).first()
    if user:
        logger.info("Database already has users, skipping initialization")
        return

    # Create initial admin user
    admin_user = UserDB(
        username="admin",
        hashed_password=get_password_hash("admin123"),
        is_active=True,
    )
    db.add(admin_user)
    db.commit()
    logger.info("Created initial admin user (username: admin, password: admin123)")


def main() -> None:
    logger.info("Creating initial data")
    db = SessionLocal()
    try:
        init_db(db)
    finally:
        db.close()
    logger.info("Initial data created")


if __name__ == "__main__":
    main()
