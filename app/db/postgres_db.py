from app.core.config import settings


def get_database_uri() -> str:
    return settings.SQLALCHEMY_DATABASE_URI
