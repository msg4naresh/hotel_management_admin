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

### ORM Choice: SQLAlchemy vs SQLModel

**Why SQLAlchemy over SQLModel?**

This project uses **SQLAlchemy 2.0 + Pydantic** instead of SQLModel (the official FastAPI template's ORM). This decision was made for the following reasons:

**SQLModel Advantages:**
- Single model for both database and API validation (less duplication)
- Simpler for basic CRUD operations
- Tighter Pydantic integration out of the box

**SQLAlchemy Advantages (Why We Chose It):**
1. **Advanced Concurrency Control** - Critical for this application
   - Full support for row-level locking (`with_for_update()`)
   - Prevents race conditions in booking system (double-booking prevention)
   - Essential for financial transactions and inventory management

2. **Complex Query Support**
   - Advanced joins and subqueries
   - Custom SQL when needed
   - Better performance optimization options

3. **Flexibility & Separation of Concerns**
   - Database models separate from API schemas
   - Different validation rules for create/update/response
   - Easier to evolve schemas independently

4. **Production-Hardened**
   - More mature ecosystem (20+ years)
   - Better tooling and debugging support
   - Extensive documentation for edge cases

**Trade-off**: More code duplication (separate SQLAlchemy models and Pydantic schemas), but this is acceptable given the critical need for advanced concurrency control.

**When to use SQLModel instead:**
- Simple CRUD applications without complex transactions
- Rapid prototyping
- Applications that don't need row-level locking
- Teams preferring minimalism over flexibility

### Request Flow (Critical Path)

```
1. HTTP Request → FastAPI app
2. JWT token extracted from Authorization header
3. get_current_user() dependency validates token via app/api/dependencies/auth_deps.py
4. Database session injected via get_db() dependency
5. Endpoint handler executes business logic
6. SQLAlchemy models converted to Pydantic response schemas
7. JSON response returned
```

### Database Session Pattern

**ALWAYS use FastAPI dependency injection** - Let the framework manage sessions:

```python
# CORRECT - FastAPI dependency injection
from app.db.base_db import get_db
from sqlalchemy.orm import Session
from fastapi import Depends

@router.get("/items")
def read_items(session: Session = Depends(get_db)):
    items = session.query(ItemDB).all()
    return items

# MODERN (Python 3.10+) - Use Annotated for better type safety
from typing import Annotated

@router.get("/items")
def read_items(session: Annotated[Session, Depends(get_db)]):
    items = session.query(ItemDB).all()
    return items

# WRONG - Manual session management
session = SessionLocal()
try:
    items = session.query(ItemDB).all()
finally:
    session.close()  # Easy to forget, creates leaks
```

**Row-level locking** (prevent race conditions):
```python
@router.post("/items/{item_id}")
def update_item(
    item_id: int,
    session: Session = Depends(get_db)
):
    # Lock row until transaction commits
    item = session.query(ItemDB).filter(
        ItemDB.id == item_id
    ).with_for_update().first()

    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    # Modify and commit
    item.field = new_value
    session.commit()
    return item
```

### File Upload Architecture (S3 Integration)

**Database-First Pattern** (prevents orphaned S3 files):

```python
# 1. Validate file (magic bytes, size, sanitization)
safe_filename, ext, content_type = file_validator.validate_file(filename, content)

# 2. Single transaction: check DB, upload S3, update DB
# Inject session via dependency
@router.post("/upload")
def upload_file(session: Session = Depends(get_db)):
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
```

### Docker Setup Options

The project supports three development modes:

**Hybrid Setup** (Recommended - Fast iteration):
```bash
# 1. Start only database in Docker
docker compose up -d db

# 2. Run app locally (hot-reload enabled)
uv run alembic upgrade head
uv run uvicorn app.main:app --reload
```

**Full Docker Setup** (Production-like):
```bash
# Start all services (app + db)
docker compose up -d
# App available at http://localhost:8050
```

**Full Local Setup** (No Docker):
```bash
# Requires local PostgreSQL installation
export PG_HOST=localhost PG_PORT=5432
uv sync
uv run alembic upgrade head
uv run uvicorn app.main:app --reload
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
uv run ruff format app/ tests/

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
│   ├── base_db.py               # get_db() dependency (ALWAYS USE THIS)
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
│       ├── auth_deps.py         # get_current_user() dependency
│       ├── s3_deps.py           # get_s3_service() dependency
│       └── common.py            # SessionDep, CurrentUserDep, S3ServiceDep type aliases
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

## CRUD Pattern (Repository Layer)

This project uses a **Repository Pattern** via CRUD base classes to encapsulate database operations:

### CRUDBase Class (`app/crud/base.py`)

Generic CRUD operations for all models:

```python
from app.crud import user, room  # Pre-instantiated CRUD objects

# Standard operations available:
user.get(db, id_)                    # Get single record
user.get_multi(db, skip=0, limit=100) # Get multiple with pagination
user.create(db, obj_in=user_create)   # Create new record
user.update(db, db_obj=user, obj_in=updates)  # Update existing
user.remove(db, id_=user_id)          # Delete record
```

### Custom CRUD Methods

Entity-specific operations extend CRUDBase:

```python
# app/crud/crud_user.py
class CRUDUser(CRUDBase[UserDB, UserCreate, UserUpdate]):
    def authenticate(self, db: Session, username: str, password: str) -> UserDB | None:
        # Custom authentication logic
        user = self.get_by_username(db, username=username)
        if not user or not user.verify_password(password):
            return None
        return user

    def get_by_username(self, db: Session, username: str) -> UserDB | None:
        return db.query(UserDB).filter(UserDB.username == username).first()

# Usage in endpoints
from app.crud import user as crud_user

@router.post("/token")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = crud_user.authenticate(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(401, "Invalid credentials")
```

### When to Use CRUD vs Direct Queries

- **Use CRUD**: For standard operations (get, create, update, delete, common queries)
- **Use Direct Queries**: For complex joins, aggregations, or operations needing `with_for_update()`

```python
# GOOD - Use CRUD for simple operations
user = crud_user.get(db, user_id)

# GOOD - Use direct query for row locking
customer = db.query(CustomerDB).filter(
    CustomerDB.id == customer_id
).with_for_update().first()
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
- `PATCH /bookings/{id}/check-in`, `PATCH /bookings/{id}/check-out`, `PATCH /bookings/{id}/cancel`

**Documents**
- `POST /upload-document/{customer_id}` - Upload to S3 (database-first pattern)
- `DELETE /documents/{customer_id}` - Delete from S3

**Health**
- `GET /health` - Liveness (always returns 200)
- `GET /health/ready` - Readiness (checks database)

## Important Patterns

### Dependency Type Aliases (PREFERRED PATTERN)

**USE THIS PATTERN** for all new endpoints - it's more concise and type-safe:

```python
# Import pre-configured dependency type aliases
from app.api.dependencies.common import SessionDep, CurrentUserDep, S3ServiceDep

@router.get("/items")
def get_items(
    session: SessionDep,           # Database session
    current_user: CurrentUserDep   # Authenticated user
):
    items = session.query(ItemDB).all()
    return items

@router.post("/upload")
def upload_file(
    session: SessionDep,
    current_user: CurrentUserDep,
    s3_service: S3ServiceDep       # S3 service instance
):
    # S3 operations here
    pass
```

**Why this pattern?**
- Defined once in `app/api/dependencies/common.py` - DRY principle
- Type-safe with `Annotated[Type, Depends(func)]`
- Cleaner endpoint signatures
- Easier to refactor (change dependency in one place)

**Available dependency aliases**:
- `SessionDep` - `Annotated[Session, Depends(get_db)]`
- `CurrentUserDep` - `Annotated[UserDB, Depends(get_current_user)]`
- `S3ServiceDep` - `Annotated[S3Service, Depends(get_s3_service)]`

### Adding New Endpoints

1. Create endpoint in `app/api/endpoints/{feature}.py`
2. Import dependency aliases: `from app.api.dependencies.common import SessionDep, CurrentUserDep`
3. Use type aliases in endpoint signatures (preferred over direct `Depends()`)
4. Add router to `app/api/routes.py`
5. Return Pydantic response models

### Alternative: Direct Dependency Injection (Legacy Pattern)

**NOTE**: While this pattern still works, prefer the `SessionDep`/`CurrentUserDep` aliases above.

```python
from app.api.dependencies.auth_deps import get_current_user
from fastapi import Depends

@router.get("/protected")
async def protected_endpoint(current_user: UserDB = Depends(get_current_user)):
    # current_user is validated UserDB from database
    return {"user_id": current_user.id}
```

### OAuth2 JWT Authentication Pattern (FastAPI Official)

**Reference**: [FastAPI OAuth2 with JWT](https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/)

Follow FastAPI's recommended OAuth2 pattern for all authentication:

```python
# app/api/dependencies/auth_deps.py
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: Session = Depends(get_db)
) -> UserDB:
    """
    Validates JWT token and returns authenticated user.
    Raises HTTPException with WWW-Authenticate header on failure.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},  # OAuth2 standard
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")  # Standard JWT claim
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = session.query(UserDB).filter(UserDB.username == username).first()
    if user is None:
        raise credentials_exception

    return user
```

**Login endpoint pattern**:
```python
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta

@router.post("/token")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: Session = Depends(get_db)
):
    user = session.query(UserDB).filter(
        UserDB.username == form_data.username
    ).first()

    if not user or not user.verify_password(form_data.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}
```

### Exception Handling Pattern

**CRITICAL**: Follow FastAPI's minimalist exception handling approach.

**DO**: Let HTTPException bubble up naturally
```python
@router.get("/customers/{customer_id}")
def get_customer(
    customer_id: int,
    session: Session = Depends(get_db),
    current_user: UserDB = Depends(get_current_user)
):
    customer = session.query(CustomerDB).filter(
        CustomerDB.id == customer_id
    ).first()

    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Customer {customer_id} not found"
        )

    return customer
    # FastAPI handles uncaught exceptions automatically
```

**DON'T**: Wrap every endpoint in generic try/except
```python
# ANTI-PATTERN - Violates minimalism principle
@router.get("/customers/{customer_id}")
def get_customer(customer_id: int, session: Session = Depends(get_db)):
    try:
        customer = session.query(CustomerDB).filter(...).first()
        if not customer:
            raise HTTPException(404, "Not found")
        return customer
    except HTTPException:
        raise  # Unnecessary pass-through
    except Exception as e:  # Too broad, masks real errors
        logger.exception(f"Error fetching customer {customer_id}")
        raise HTTPException(500, "Internal error")  # Loses valuable error info
```

**When to use try/except**:
1. **External service failures** (S3, third-party APIs) - catch specific exceptions
2. **Validation errors** - when you need custom error messages
3. **Database integrity errors** - to provide user-friendly messages

**Example - Proper exception handling for S3 operations**:
```python
from botocore.exceptions import ClientError

@router.post("/upload/{customer_id}")
def upload_file(
    customer_id: int,
    file: UploadFile,
    session: Session = Depends(get_db)
):
    customer = session.query(CustomerDB).filter(
        CustomerDB.id == customer_id
    ).with_for_update().first()

    if not customer:
        raise HTTPException(404, "Customer not found")

    try:
        # S3 operation - catch specific exception
        s3_url = s3_service.upload_file(file.file.read(), file.filename)
        customer.document_url = s3_url
        session.commit()
        return {"url": s3_url}

    except ClientError as e:
        # Specific S3 error handling
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"File upload failed: {e.response['Error']['Message']}"
        )
    # No generic Exception handler - let FastAPI handle unexpected errors
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

## Security Considerations

**Authentication & Authorization**:
- All JWT tokens expire after 30 minutes (configurable via `ACCESS_TOKEN_EXPIRE_MINUTES`)
- Passwords hashed with bcrypt cost factor 12 (2^12 = 4,096 iterations)
- Never commit `.env` files with real credentials
- Always include `WWW-Authenticate: Bearer` header in 401 responses

**File Upload Security**:
- MIME type validation via magic bytes (not file extension)
- Filename sanitization prevents path traversal attacks (`../../../etc/passwd`)
- Maximum file size: 10MB (configurable via `MAX_FILE_SIZE`)
- Allowed formats: PDF, JPEG, PNG only
- Files stored in S3 with unique keys: `customer_proofs/{customer_id}/{timestamp}_{filename}`

**Database Security**:
- Use parameterized queries (SQLAlchemy prevents SQL injection)
- Row-level locking (`with_for_update()`) prevents race conditions
- Never expose internal error messages in production
- Use transactions for multi-step operations

**API Security**:
- CORS configured via `BACKEND_CORS_ORIGINS` environment variable
- All protected endpoints require valid JWT token
- Input validation via Pydantic schemas
- Rate limiting should be implemented at infrastructure level (load balancer/API gateway)

## Common Pitfalls to Avoid

1. **Don't use old-style type hints** - Use `list[T]`, `dict[K, V]`, `X | None` (not `List`, `Dict`, `Optional`)
2. **Don't wrap endpoints in generic try/except** - Let FastAPI handle exceptions; only catch specific ones (ClientError, IntegrityError)
3. **Don't forget WWW-Authenticate header** - Include `headers={"WWW-Authenticate": "Bearer"}` in 401 responses
4. **Don't cache S3Service instances** - Creates credential rotation issues
5. **Don't split related DB operations** - Causes race conditions
6. **Don't use os.getenv() with Pydantic Settings** - Defeats validation
7. **Don't create classes with only static methods** - Use module-level functions
8. **Don't add background workers/queues** - Keep it simple (best-effort is enough)
9. **Don't forget with_for_update()** - Prevents concurrent modification issues
10. **Don't use deprecated @app.on_event()** - Use lifespan context manager if needed

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
   - Runs linting and formatting (ruff), type checking (mypy)
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