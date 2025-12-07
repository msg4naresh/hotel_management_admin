from app.db.base_db import engine
from app.models.base import Base

# Import all models here


def init_db():
    Base.metadata.create_all(bind=engine)
