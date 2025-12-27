# Hotel Management System - Admin API

Enterprise-grade FastAPI backend for hotel management with PostgreSQL, AWS S3, and production-ready features.

## Features

- **Authentication**: JWT-based OAuth2 authentication with secure password hashing
- **Room Management**: CRUD operations for hotel rooms with enum-based room types
- **Customer Management**: Customer records with document uploads to S3
- **Booking Management**: Reservations, check-ins, check-outs, payment tracking
- **Document Storage**: AWS S3 integration with file validation and database-first pattern
- **Database**: PostgreSQL 17 with Alembic migrations and row-level locking
- **Monitoring**: Sentry integration for error tracking
- **Health Checks**: Liveness and readiness probes for Kubernetes/Cloud Run
- **Testing**: 190+ comprehensive unit, integration, and e2e tests

## Quick Start - Choose Your Setup

**Three ways to run this project:**

| Setup | What You Need | Time | Best For |
|-------|--------------|------|----------|
| **Hybrid (Recommended)** | Python 3.14, UV, Docker | 10 min | **Active development** - Fast iteration, instant reload |
| **Fully Docker** | Docker Desktop only | 5 min | **Quick start** - No local dependencies needed |
| **Fully Local** | Python 3.14, PostgreSQL 17, UV | 15 min | **Traditional setup** - Full local control |

---

## Configuration

**IMPORTANT**: Create `.env` file in project root (same directory as `README.md` and `docker-compose.yml`).

```bash
# Navigate to project root
cd hotel_management_admin

# Create .env file
touch .env  # or "type nul > .env" on Windows

# Edit with your preferred editor
code .env  # VS Code
# OR: nano .env, vim .env, notepad .env
```

### Environment Variables Template

Copy this template to your `.env` file:

```bash
# API Configuration
PROJECT_NAME="Hotel Management Admin"
API_V1_STR="/api/v1"
ENVIRONMENT="development"

# Database Configuration
# For Docker setup: use PG_HOST=db
# For Local/Hybrid: use PG_HOST=localhost
PG_HOST=localhost
PG_PORT=5432
PG_USERNAME=postgres
PG_PASSWORD=postgres
PG_DB=hotel_management
PG_SCHEMA=public

# Security (CHANGE IN PRODUCTION)
SECRET_KEY=dev-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# AWS S3 - REPLACE WITH YOUR VALUES
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_S3_BUCKET_NAME=your-bucket-name
AWS_S3_REGION=us-east-1

# File Upload
MAX_FILE_SIZE=10485760
ALLOWED_FILE_TYPES=["application/pdf", "image/jpeg", "image/png"]

# Optional - Monitoring
SENTRY_DSN=

# Optional - CORS
BACKEND_CORS_ORIGINS=["http://localhost:3000"]

# Server Port
# For Docker: use PORT=8080
# For Local/Hybrid: use PORT=8000
PORT=8000
```

**Key settings by setup type**:
- **Docker**: Set `PG_HOST=db` and `PORT=8080`
- **Local/Hybrid**: Keep `PG_HOST=localhost` and `PORT=8000`

---

## Option 1: Hybrid Setup (RECOMMENDED)

**Best for active development** - App runs locally for instant reload, database in Docker for isolation.

### Step 1: Install Required Software

```bash
# macOS
brew install python@3.14 docker
curl -LsSf https://astral.sh/uv/install.sh | sh

# Linux
sudo apt install python3.14 python3.14-venv docker.io docker-compose-v2
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows: Download and install
# Python: https://www.python.org/downloads/
# Docker: https://www.docker.com/products/docker-desktop
# UV: powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### Step 2: Clone and Install

```bash
git clone <your-repo-url>
cd hotel_management_admin
uv sync
```

### Step 3: Start Database (Docker only)

```bash
docker compose up -d db
docker compose ps  # Verify 'db' is running
```

### Step 4: Configure Environment

Copy the [environment template](#environment-variables-template) to `.env` with these settings:
- `PG_HOST=localhost` (app connects to Docker DB via localhost)
- `PORT=8000`

### Step 5: Run Migrations & Start App

```bash
uv run alembic upgrade head
uv run python initial_data.py  # Optional: creates admin user
uv run uvicorn app.main:app --reload
```

### Access the App

- Swagger UI: http://localhost:8000/docs
- Health Check: http://localhost:8000/api/v1/health

### Benefits

✅ Instant code reload (no Docker rebuild)
✅ Easy debugging with local Python
✅ Isolated database (no conflicts)
✅ Best developer experience

---

## Option 2: Fully Docker Setup

**Quickest start** - Everything in containers, no local dependencies.

### Step 1: Install Docker

```bash
# macOS
brew install --cask docker

# Linux
sudo apt install docker.io docker-compose-v2
sudo usermod -aG docker $USER && newgrp docker

# Windows: Download from https://www.docker.com/products/docker-desktop
```

### Step 2: Clone and Configure

```bash
git clone <your-repo-url>
cd hotel_management_admin
touch .env
```

Copy the [environment template](#environment-variables-template) to `.env` with these settings:
- `PG_HOST=db` (Docker internal networking)
- `PORT=8080`

### Step 3: Start Everything

```bash
docker compose up -d
docker compose logs -f  # Watch startup logs
```

### Access the App

- Swagger UI: http://localhost:8050/docs
- Health Check: http://localhost:8050/api/v1/health/ready

### Useful Commands

```bash
# View logs
docker compose logs -f app
docker compose logs -f db

# Stop everything
docker compose down

# Fresh start (deletes all data - removes persistent volumes)
docker compose down -v && docker compose up -d

# Rebuild after code changes
docker compose up -d --build

# Database shell
docker compose exec db psql -U postgres -d hotel_management
```

---

## Option 3: Fully Local Setup

**Traditional setup** - Full local control, best if you already have PostgreSQL installed.

### Step 1: Install Software

```bash
# macOS
brew install python@3.14 postgresql@17
curl -LsSf https://astral.sh/uv/install.sh | sh
brew services start postgresql@17

# Linux
sudo apt install python3.14 python3.14-venv postgresql-17
curl -LsSf https://astral.sh/uv/install.sh | sh
sudo systemctl start postgresql && sudo systemctl enable postgresql

# Windows
# Download and install:
# - Python: https://www.python.org/downloads/
# - PostgreSQL: https://www.postgresql.org/download/windows/
# - UV: powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### Step 2: Create Database

```bash
# macOS/Linux
createdb hotel_management

# Windows (psql)
psql -U postgres
CREATE DATABASE hotel_management;
\q
```

### Step 3: Clone, Configure & Run

```bash
git clone <your-repo-url>
cd hotel_management_admin
uv sync
touch .env
```

Copy the [environment template](#environment-variables-template) to `.env` with these settings:
- `PG_HOST=localhost` (local PostgreSQL)
- `PORT=8000`

```bash
uv run alembic upgrade head
uv run python initial_data.py  # Optional: creates admin user
uv run uvicorn app.main:app --reload
```

### Access the App

- Swagger UI: http://localhost:8000/docs
- Health Check: http://localhost:8000/api/v1/health

---

## AWS S3 Setup (Required for File Uploads)

All three setup options require AWS S3 credentials for document uploads to work.

### Step 1: Create S3 Bucket

```bash
# Option A: Using AWS Console
# 1. Go to: https://s3.console.aws.amazon.com/
# 2. Click "Create bucket"
# 3. Bucket name: hotel-management-uploads-<your-name>
# 4. Region: us-east-1 (or your preferred region)
# 5. Block all public access: ENABLED (recommended)
# 6. Click "Create bucket"

# Option B: Using AWS CLI
aws s3 mb s3://hotel-management-uploads-yourname --region us-east-1
```

### Step 2: Create IAM User with S3 Access

```bash
# Using AWS Console:
# 1. Go to: https://console.aws.amazon.com/iam/
# 2. Click "Users" → "Add users"
# 3. User name: hotel-management-app
# 4. Access type: Access key - Programmatic access
# 5. Attach policy: AmazonS3FullAccess (dev only)
#    For production: Use custom policy with restricted bucket access
#    See: https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_examples_s3_rw-bucket.html
# 6. Save the Access Key ID and Secret Access Key
```

### Step 3: Update .env File

```bash
AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
AWS_S3_BUCKET_NAME=hotel-management-uploads-yourname
AWS_S3_REGION=us-east-1
```

### Step 4: Test S3 Upload (Optional)

```bash
# After starting the app, test file upload:
# 1. Login and get token from http://localhost:8000/docs
# 2. Create a customer
# 3. Upload a document to that customer
# 4. Check AWS S3 console - file should appear in bucket
```

---

## Testing

The project includes **190+ tests** covering unit, integration, and end-to-end scenarios with **75%+ code coverage**.

### Running Tests

```bash
# Run all tests
uv run pytest tests/ -v

# Run by test type
uv run pytest tests/unit/ -v           # ~150 unit tests
uv run pytest tests/integration/ -v    # ~34 integration tests
uv run pytest tests/e2e/ -v            # ~9 e2e tests

# Run with coverage report
uv run pytest tests/ --cov=app --cov-report=html --cov-report=term

# Open HTML coverage report
open htmlcov/index.html

# Run specific test file
uv run pytest tests/unit/test_file_validator.py -v

# Run specific test function
uv run pytest tests/unit/test_file_validator.py::test_validate_file_success -v

# Faster execution (parallel mode)
uv run pytest tests/ -n auto
```

### Test Structure

- **unit/**: Services, validators, utilities (mocked dependencies)
- **integration/**: API endpoints with real database (mocked S3 via moto)
- **e2e/**: Complete workflows (login → upload → verify)

---

## Architecture

See [CLAUDE.md](./CLAUDE.md) for complete architecture details and patterns.

### Tech Stack

| Component | Technology | Version |
|-----------|-----------|---------|
| **Framework** | FastAPI | 0.115+ |
| **Language** | Python | 3.14 |
| **Database** | PostgreSQL | 17 |
| **ORM** | SQLAlchemy | 2.0+ |
| **Migrations** | Alembic | 1.14+ |
| **Storage** | AWS S3 | boto3 1.35+ |
| **Auth** | JWT | python-jose 3.3+ |
| **Testing** | pytest | 8.0+ |
| **Linting** | Ruff | 0.8+ |
| **Type Checking** | MyPy | 1.12+ |
| **Monitoring** | Sentry | 1.40+ |

### Key Directories

```
app/
├── main.py                 # FastAPI app + Sentry integration
├── api/
│   ├── routes.py           # Central router
│   ├── dependencies/       # Dependency injection (SessionDep, CurrentUserDep)
│   └── endpoints/          # API endpoints by resource
├── core/
│   ├── config.py           # Pydantic Settings
│   ├── security.py         # JWT + password hashing
│   └── logging.py          # Structured JSON logging
├── crud/                   # Repository pattern (generic CRUD operations)
├── models/                 # SQLAlchemy models + Pydantic schemas
├── services/               # Business logic (S3, file validation)
└── db/                     # Database setup (get_db dependency)

tests/
├── conftest.py             # Pytest fixtures
├── unit/                   # Unit tests
├── integration/            # Integration tests
└── e2e/                    # End-to-end tests

alembic/                    # Database migrations
```

---

## API Endpoints

All endpoints prefixed with `/api/v1`:

### Authentication
- `POST /auth/token` - Login (OAuth2 compatible)
- `POST /auth/register` - Register new user
- `GET /auth/users` - List all users (protected)

### Rooms
- `GET /rooms` - List all rooms
- `POST /create-room` - Create new room

### Customers
- `GET /customers` - List customers
- `POST /create-customer` - Create customer

### Bookings
- `GET /bookings` - List bookings
- `POST /create-booking` - Create booking
- `PATCH /bookings/{id}/check-in` - Check-in guest
- `PATCH /bookings/{id}/check-out` - Check-out guest
- `PATCH /bookings/{id}/cancel` - Cancel booking

### Documents
- `POST /upload-document/{customer_id}` - Upload to S3
- `DELETE /documents/{customer_id}` - Delete from S3

### Health
- `GET /health` - Liveness probe (always returns 200 if app is running)
- `GET /health/ready` - Readiness probe (checks database connectivity)

---

## Development

**Note**: `uv run <command>` executes commands in the project's virtual environment.

### Code Quality

```bash
# Format code
uv run ruff format app/ tests/

# Lint and auto-fix
uv run ruff check --fix app/ tests/

# Type check (pragmatic config for SQLAlchemy)
uv run python -m mypy app/
```

### Database Migrations

```bash
# Create migration after modifying models
uv run alembic revision --autogenerate -m "description"

# Apply migrations
uv run alembic upgrade head

# Rollback one version
uv run alembic downgrade -1

# Check current version
uv run alembic current

# View migration history
uv run alembic history
```

### Initial Data Seeding

Create default admin user for development:

```bash
uv run python initial_data.py
```

Creates: `username: admin`, `password: admin123` (if no users exist)

### Pre-start Health Check

The `backend_pre_start.py` script runs before the app starts (in Docker) to verify database connectivity:

```bash
# Run manually
uv run python backend_pre_start.py
```

Features:
- Retries DB connection up to 300 times (5 minutes)
- Logs all retry attempts
- Exits with error code if DB is unreachable

### Common Development Tasks

```bash
# Add a new Python package
uv add package-name              # Runtime dependency
uv add --dev package-name        # Development dependency

# Update all dependencies
uv lock --upgrade

# Sync environment with lockfile (after pulling changes)
uv sync

# View database schema
uv run python -c "from app.models import *; from app.db.base_db import Base; print(Base.metadata.tables)"

# Connect to database with psql
psql -h localhost -U postgres -d hotel_management
# Inside psql:
# \dt        - List tables
# \d users   - Describe users table
# \q         - Quit
```

### Troubleshooting

**Database connection fails**:
```bash
# Check if PostgreSQL is running
docker ps  # or: brew services list

# Test database connection manually
psql -h localhost -U postgres -d hotel_management

# Reset database (WARNING: DELETES ALL DATA - removes persistent volumes)
docker compose down -v          # -v flag removes volumes
docker compose up -d db         # Start fresh database
uv run alembic upgrade head     # Recreate schema from migrations
```

**Import errors or module not found**:
```bash
# Ensure virtual environment is in sync with lockfile
uv sync

# Verify Python version
python --version  # Should be 3.14+
```

**Alembic migration conflicts**:
```bash
# Check current database migration version
uv run alembic current

# View migration history to identify conflicts
uv run alembic history

# Downgrade to specific version (if needed)
uv run alembic downgrade <revision_id>

# Then reapply migrations
uv run alembic upgrade head
```

**S3 upload fails**:
- Verify AWS credentials are set correctly in `.env`
- Check S3 bucket exists: `aws s3 ls s3://your-bucket-name`
- Verify region is correct: `AWS_S3_REGION=us-east-1`
- Ensure IAM user has `s3:PutObject` and `s3:DeleteObject` permissions

---

## Design Patterns

This project follows FastAPI best practices and modern Python patterns:

1. **Dependency injection** with type aliases (`SessionDep`, `CurrentUserDep`, `S3ServiceDep`)
2. **Database-first uploads** to prevent orphaned S3 files (validate DB → upload S3 → update DB in single transaction)
3. **Generic CRUD repository** for DRY database operations (`app/crud/base.py`)
4. **OAuth2 JWT authentication** (FastAPI official pattern with `OAuth2PasswordBearer`)
5. **Minimalist exception handling** (let FastAPI handle exceptions; only catch specific ones like `ClientError`, `IntegrityError`)
6. **Modern type hints** (Python 3.10+ syntax: `list[T]`, `dict[K, V]`, `X | None`)

See [CLAUDE.md](./CLAUDE.md) for detailed examples, rationale, and implementation guidelines.

---

## Security Features

- **JWT Authentication**: OAuth2-compatible token-based auth
- **Password Hashing**: bcrypt with cost factor 12
- **File Validation**: Magic bytes verification, size limits, path sanitization
- **Path Traversal Prevention**: Filename sanitization
- **Database-first Uploads**: Prevents orphaned S3 files through transactional consistency
- **CORS**: Configurable allowed origins
- **Sentry**: Error tracking and performance monitoring

---

## Production Deployment

### Environment Variables

Set these in production (in addition to the base configuration):

```bash
ENVIRONMENT=production
SECRET_KEY=<strong-random-key>  # Generate with: openssl rand -hex 32
SENTRY_DSN=<your-sentry-dsn>
PG_HOST=<production-db-host>
PG_PASSWORD=<strong-db-password>
AWS_ACCESS_KEY_ID=<production-key>
AWS_SECRET_ACCESS_KEY=<production-secret>
```

### Docker

The Dockerfile includes:
- Multi-stage build for smaller images
- Pre-start health check (`backend_pre_start.py`)
- UV for fast dependency installation
- Non-root user execution
- Optimized for Cloud Run deployment

### Health Checks

Configure your orchestrator to use:
- **Liveness**: `GET /health` - Returns 200 if app is running
- **Readiness**: `GET /health/ready` - Returns 200 only if database is accessible

**Example Kubernetes config**:
```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 8080
  initialDelaySeconds: 30
  periodSeconds: 10

readinessProbe:
  httpGet:
    path: /health/ready
    port: 8080
  initialDelaySeconds: 10
  periodSeconds: 5
```

---

## Monitoring

### Sentry Integration

Automatically enabled if `SENTRY_DSN` is set:

```bash
export SENTRY_DSN="https://your-dsn@sentry.io/project-id"
export ENVIRONMENT="production"
```

Features:
- Error tracking with full stack traces
- Performance monitoring (10% sample rate in production)
- SQLAlchemy query tracking
- FastAPI request tracing

### Structured Logging

All logs are output as JSON for easy parsing by log aggregators:

```json
{
  "timestamp": "2024-12-07 21:00:00,000",
  "level": "INFO",
  "name": "app.main",
  "message": "Application started"
}
```

---

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `uv run pytest`
5. Run linting: `uv run ruff check --fix app/`
6. Submit a pull request

---

## Additional Documentation

- **[CLAUDE.md](./CLAUDE.md)** - Architecture principles, patterns, development guidelines, and AI agent context
- **[GEMINI.md](./GEMINI.md)** - Alternative AI agent instructions and project conventions

---

## License

MIT
