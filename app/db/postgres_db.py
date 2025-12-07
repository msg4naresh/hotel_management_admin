from app.core.config import settings


def get_database_uri() -> str:
    return f"postgresql+psycopg2://{settings.PG_USERNAME}:{settings.PG_PASSWORD}@{settings.PG_HOST}:{settings.PG_PORT}/{settings.PG_DB}?options=-csearch_path%3D{settings.PG_SCHEMA}"

