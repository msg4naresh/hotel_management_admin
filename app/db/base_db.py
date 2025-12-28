from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.postgres_db import get_database_uri

engine = create_engine(get_database_uri(), pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
