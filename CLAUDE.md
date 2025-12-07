# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

FastAPI-based hotel management admin system with PostgreSQL database, AWS S3 document storage, and JWT authentication. Designed for minimalism and simplicity.

**Python 3.14** - Uses modern Python 3.10+ syntax throughout. No legacy typing imports.

## Architecture Principles

**CRITICAL**: Follow these principles when making changes:

1. **Minimalism First** - Only add essential code. Every line must serve a clear purpose.
2. **No Over-Engineering** - Prefer simple solutions over complex abstractions. Three similar lines are better than a premature abstraction.
3. **Database-First Pattern** - Always validate database records exist before S3 operations to prevent orphaned files.
4. **Single Transaction** - Keep related database operations in one transaction to prevent race conditions.
5. **Best-Effort Cleanup** - S3 file cleanup is synchronous and best-effort. No queues, no retries, no background workers.

## Core Architecture

### Request Flow (Critical Path)

```
1. HTTP Request → FastAPI app
2. JWT token extracted from Authorization header
3. get_current_user() dependency validates token via app/api/dependencies/auth_deps.py
4. Database session created via get_session() context manager
5. Endpoint handler executes business logic
6. SQLAlchemy models converted to Pydantic response schemas
7. JSON response returned
```

### Database Session Pattern

**ALWAYS use context manager** - Never manually manage sessions:

```python
# CORRECT
with get_session() as session:
    customer = session.query(CustomerDB).filter(...).first()
    # session auto-closes on exit

# WRONG - Don't do this
session = SessionLocal()
customer = session.query(CustomerDB).filter(...).first()
session.close()  # Easy to forget, creates leaks
```

For row-level locking (prevent race conditions):
```python
with get_session() as session:
    customer = session.query(CustomerDB).filter(...).with_for_update().first()
    # Row locked until transaction commits
    customer.field = new_value
    session.commit()
```

### File Upload Architecture (S3 Integration)

**Database-First Pattern** (prevents orphaned S3 files):

```python
# 1. Validate file (magic bytes, size, sanitization)
safe_filename, ext, content_type = file_validator.validate_file(filename, content)

# 2. Single transaction: check DB, upload S3, update DB
with get_session() as session:
    customer = session.query(CustomerDB).filter(...).with_for_update().first()
    if not customer:
        raise HTTPException(404)

    # Upload to S3 WITHIN transaction lock
    s3_url = s3_service.upload_file(content, safe_filename, customer_id, content_type)

    # Update database
    customer.proof_image_url = s3_url
    session.commit()

# 3. Best-effort cleanup of old file (after commit)
if old_s3_key:
    delete_old_file_best_effort(s3_service, old_s3_key)
```

**Why this pattern?**
- Transaction ensures atomicity (DB ↔ S3 consistency)
- with_for_update() prevents concurrent uploads to same customer
- Cleanup happens after commit (doesn't block transaction)
- If S3 upload fails, transaction rolls back automatically

### Configuration (Pydantic BaseSettings)

All config in `app/core/config.py`. **Let Pydantic handle environment variables**:

```python
# CORRECT - Pydantic loads from env automatically
class Settings(BaseSettings):
    SECRET_KEY: str = "dev-default"
    AWS_ACCESS_KEY_ID: str = ""

    class Config:
        env_file = ".env"
        case_sensitive = False  # Allows AWS_ACCESS_KEY_ID or aws_access_key_id

# WRONG - Don't use os.getenv() with BaseSettings
SECRET_KEY: str = os.getenv("SECRET_KEY", "default")  # Defeats Pydantic validation
```

## Development Commands

### Setup & Running

```bash
# Install UV (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies (uses UV for speed)
uv sync

# Run database migrations
uv run alembic upgrade head

# Start development server
uv run uvicorn app.main:app --reload

# Interactive API documentation available at:
# http://localhost:8000/docs (Swagger UI)
# http://localhost:8000/redoc (ReDoc)

# Docker deployment
docker compose up -d  # Exposes on http://localhost:8050
```

### Testing

```bash
# Run all tests
uv run pytest tests/ -v

# Run specific test type
uv run pytest tests/unit/ -v              # Unit tests only
uv run pytest tests/integration/ -v       # Integration tests
uv run pytest tests/e2e/ -v               # End-to-end tests

# Run single test file
uv run pytest tests/unit/test_file_validator.py -v

# Run single test function
uv run pytest tests/unit/test_file_validator.py::test_validate_file_success -v

# Run with coverage
uv run pytest tests/ --cov=app --cov-report=html
```

### Database Migrations

```bash
# Create migration after modifying models
uv run alembic revision --autogenerate -m "description"

# Apply migrations
uv run alembic upgrade head

# Rollback one migration
uv run alembic downgrade -1

# Check current migration
uv run alembic current

# View migration history
uv run alembic history
```

### Code Quality

```bash
# Format code
uv run black app/ tests/
uv run isort app/ tests/

# Lint with auto-fix
uv run ruff check --fix app/ tests/

# Type check
uv run mypy app/
```

### Package Management (UV)

```bash
# Add runtime dependency
uv add package-name

# Add dev dependency
uv add --dev package-name

# Update dependencies
uv lock --upgrade

# Sync environment with lockfile
uv sync
```

## Project Structure (Critical Components)

```
app/
├── main.py                      # FastAPI app, no background workers
├── core/
│   ├── config.py                # Pydantic Settings (NO os.getenv!)
│   ├── security.py              # JWT token utilities
│   └── logging.py               # Structured logging setup
├── db/
│   ├── base_db.py               # get_session() context manager (ALWAYS USE THIS)
│   ├── postgres_db.py           # Database URI from env
│   └── init_db.py               # Table creation
├── models/
│   ├── users.py, rooms.py, bookings.py, customer.py  # SQLAlchemy ORM
│   ├── enums.py                 # Python enums for room types, statuses
│   └── schemas/                 # Pydantic response models
│       ├── auth.py
│       └── file_upload.py
├── api/
│   ├── routes.py                # Combines all routers
│   ├── endpoints/               # One file per feature
│   │   ├── auth.py              # Login, register
│   │   ├── documents.py         # S3 upload/delete (database-first!)
│   │   ├── health.py            # /health (liveness), /health/ready (readiness)
│   │   └── rooms.py, customers.py, bookings.py
│   └── dependencies/
│       └── auth_deps.py         # get_current_user() dependency
└── services/
    ├── s3_service.py            # AWS S3 operations (no caching!)
    ├── file_validator.py        # Module-level functions (NOT class)
    └── s3_cleanup.py            # Best-effort delete (24 lines, no queue)

tests/
├── conftest.py                  # Shared fixtures
├── unit/                        # Test individual functions
├── integration/                 # Test API endpoints with DB
└── e2e/                         # Test complete workflows
```

## API Endpoints

All prefixed with `/api/v1`:

**Authentication**
- `POST /auth/login` - Get JWT token
- `POST /auth/register` - Create user

**Resources** (all require JWT)
- `GET /rooms`, `POST /create-room`
- `GET /customers`, `POST /create-customer`
- `GET /bookings`, `POST /create-booking`
- `PATCH /bookings/{id}/check-in`, `PATCH /bookings/{id}/check-out`

**Documents**
- `POST /upload-document/{customer_id}` - Upload to S3 (database-first pattern)
- `DELETE /documents/{customer_id}` - Delete from S3

**Health**
- `GET /health` - Liveness (always returns 200)
- `GET /health/ready` - Readiness (checks database)

## Important Patterns

### Adding New Endpoints

1. Create endpoint in `app/api/endpoints/{feature}.py`
2. Add router to `app/api/routes.py`
3. Use `Depends(get_current_user)` for authentication
4. Use `with get_session()` for database access
5. Return Pydantic response models

### Authentication Dependency

```python
from app.api.dependencies.auth_deps import get_current_user

@router.get("/protected")
async def protected_endpoint(current_user: UserDB = Depends(get_current_user)):
    # current_user is validated UserDB from database
    return {"user_id": current_user.id}
```

### File Validation (Module-Level Functions)

```python
from app.services import file_validator

# Call validate_file() directly (no class instantiation)
safe_filename, ext, content_type = file_validator.validate_file(filename, file_bytes)
```

### Adding New Database Models

When creating a new model, follow this checklist:

1. **Create SQLAlchemy model** in `app/models/{model_name}.py`:
   ```python
   from app.models.base import Base
   from sqlalchemy import Column, Integer, String, DateTime

   class MyModelDB(Base):
       __tablename__ = "my_models"

       id = Column(Integer, primary_key=True, index=True)
       name = Column(String, nullable=False)
       created_at = Column(DateTime, default=datetime.utcnow)
   ```

2. **Create Pydantic schemas** in `app/models/schemas/{model_name}.py`:
   ```python
   from pydantic import BaseModel

   class MyModelCreate(BaseModel):
       name: str

   class MyModelResponse(BaseModel):
       id: int
       name: str
       created_at: datetime
   ```

3. **Update imports** (critical for migrations):
   - Add to `app/models/__init__.py`: `from app.models.my_model import MyModelDB`
   - Add to `alembic/env.py`: `from app.models import my_model  # noqa`

4. **Generate migration**:
   ```bash
   uv run alembic revision --autogenerate -m "add my_model table"
   uv run alembic upgrade head
   ```

5. **Create endpoint** in `app/api/endpoints/{model_name}.py`

6. **Add router** to `app/api/routes.py`:
   ```python
   from app.api.endpoints import my_model
   api_router.include_router(my_model.router, tags=["my_models"])
   ```

## Environment Variables

Required in `.env` or environment:

```bash
# Database
DATABASE_URL=postgresql://user:pass@host:5432/dbname

# AWS S3
AWS_ACCESS_KEY_ID=xxx
AWS_SECRET_ACCESS_KEY=xxx
AWS_S3_BUCKET_NAME=bucket-name
AWS_S3_REGION=us-east-1

# Security
SECRET_KEY=your-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Server (for Cloud Run)
PORT=8080
```

## Python 3.10+ Type Hint Syntax

**CRITICAL**: Always use modern type hint syntax (available since Python 3.10):

```python
# CORRECT - Modern syntax (3.10+)
def get_users() -> list[User]:
    ...

def find_user(user_id: int) -> User | None:
    ...

def process_data(items: dict[str, int]) -> tuple[str, ...]:
    ...

# WRONG - Old syntax (pre-3.10)
from typing import List, Dict, Optional, Tuple

def get_users() -> List[User]:  # Don't use typing.List
    ...

def find_user(user_id: int) -> Optional[User]:  # Don't use typing.Optional
    ...

def process_data(items: Dict[str, int]) -> Tuple[str, ...]:  # Don't use typing.Dict, Tuple
    ...
```

**Built-in types to use**:
- `list[T]` instead of `List[T]`
- `dict[K, V]` instead of `Dict[K, V]`
- `set[T]` instead of `Set[T]`
- `tuple[T, ...]` instead of `Tuple[T, ...]`
- `T | None` instead of `Optional[T]`
- `X | Y` instead of `Union[X, Y]`

**Keep using `typing` for**:
- `Any`, `TypeVar`, `Generic`, `Protocol`, `Literal`, `TypedDict`, `Callable`

## Common Pitfalls to Avoid

1. **Don't use old-style type hints** - Use `list[T]`, `dict[K, V]`, `X | None` (not `List`, `Dict`, `Optional`)
2. **Don't cache S3Service instances** - Creates credential rotation issues
3. **Don't split related DB operations** - Causes race conditions
4. **Don't use os.getenv() with Pydantic Settings** - Defeats validation
5. **Don't create classes with only static methods** - Use module-level functions
6. **Don't add background workers/queues** - Keep it simple (best-effort is enough)
7. **Don't forget with_for_update()** - Prevents concurrent modification issues
8. **Don't use deprecated @app.on_event()** - Use lifespan context manager if needed

## Deployment Notes

- Application uses `${PORT}` environment variable for Cloud Run compatibility
- No HEALTHCHECK in Dockerfile (Cloud Run handles this)
- Production Docker image uses `uv sync --no-dev` to exclude test dependencies
- Structured JSON logging enabled via `app/core/logging.py`

## Testing Strategy

- **Unit tests** (~150): Test services, validators, models in isolation
- **Integration tests** (~34): Test API endpoints with real database (mocked S3 via moto)
- **E2E tests** (~9): Test complete workflows (login → upload → verify)

Target: 75%+ code coverage

## Database Migration Internals

**How Alembic autogenerate works**:

1. `alembic/env.py` automatically imports all model files:
   ```python
   from app.models import customer, users, bookings, rooms
   ```
2. Models register themselves with `Base.metadata` on import
3. Alembic compares `Base.metadata` against current database schema
4. Generates migration with detected differences

**When adding new models**:
- Create model file in `app/models/`
- Add import to `alembic/env.py` (otherwise autogenerate won't detect it)
- Add import to `app/models/__init__.py` (for runtime use)
- Run `uv run alembic revision --autogenerate -m "add {model}"`

**Database URL resolution**:
- `alembic/env.py` calls `get_database_uri()` from `app/db/postgres_db.py`
- Uses environment variables: `PG_HOST`, `PG_PORT`, `PG_USERNAME`, `PG_PASSWORD`, `PG_DB`, `PG_SCHEMA`
- Falls back to `DATABASE_URL` if direct variables not set

## CI/CD (GitHub Actions)

**Workflow**: `.github/workflows/tests.yml` runs on every push to `main` or `develop`

**Three parallel jobs**:

1. **test** (Python 3.14)
   - Runs linting (ruff), formatting (black), type checking (mypy)
   - Executes unit, integration, and e2e tests with coverage
   - Uploads coverage to Codecov
   - Uses PostgreSQL 17 service container for integration tests

2. **security** (Python 3.14)
   - Runs Bandit for Python security issues
   - Runs Semgrep security audit
   - Uploads security reports as artifacts

3. **migrations** (Python 3.14)
   - Tests migration integrity
   - Verifies `alembic upgrade head` works on clean database
   - Uses PostgreSQL 17 service container

**Python version notes**:
- All environments use Python 3.14 (with free-threaded mode + JIT)
- PostgreSQL 17 used everywhere (CI, Docker, development)