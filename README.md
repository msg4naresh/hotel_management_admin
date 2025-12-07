# Hotel Management System - Admin API

Enterprise-grade FastAPI backend for hotel management with PostgreSQL, AWS S3, and production-ready features.

## ✨ Features

- **🔐 Authentication**: JWT-based OAuth2 authentication with secure password hashing
- **🏨 Room Management**: CRUD operations for hotel rooms
- **👥 Customer Management**: Customer records with document uploads to S3
- **📅 Booking Management**: Reservations, check-ins, check-outs, payment tracking
- **📄 Document Storage**: AWS S3 integration with file validation
- **🗄️ Database**: PostgreSQL with Alembic migrations
- **🔍 Monitoring**: Sentry integration for error tracking
- **🏥 Health Checks**: Liveness and readiness probes
- **🧪 Testing**: Comprehensive unit and integration tests

## 🚀 Quick Start

### Prerequisites

- Python 3.14+
- PostgreSQL 17
- [UV](https://github.com/astral-sh/uv) (recommended) or pip

### Installation

```bash
# Install UV (fast Python package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync

# Create initial admin user (optional)
uv run python initial_data.py

# Run database migrations
uv run alembic upgrade head

# Start development server
uv run uvicorn app.main:app --reload
```

Visit **http://localhost:8000/api/v1/docs** for interactive API documentation.

## 🐳 Docker Deployment

```bash
# Start all services (app + PostgreSQL)
docker compose up -d

# View logs
docker compose logs -f

# Stop services
docker compose down
```

Access at **http://localhost:8050/api/v1/docs**

## 🧪 Testing

```bash
# Run all tests
uv run pytest tests/ -v

# Run with coverage
uv run pytest tests/ --cov=app --cov-report=html

# Run specific test types
uv run pytest tests/unit/ -v           # Unit tests only
uv run pytest tests/integration/ -v    # Integration tests only
```

## 🏗️ Architecture

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

### Project Structure

```
hotel_management_admin/
├── app/
│   ├── main.py                 # FastAPI app + Sentry integration
│   ├── api/
│   │   ├── routes.py           # Central router
│   │   ├── dependencies/       # Dependency injection
│   │   └── endpoints/          # API endpoints by resource
│   ├── core/
│   │   ├── config.py           # Settings (Pydantic)
│   │   ├── security.py         # JWT + password hashing
│   │   └── logging.py          # Structured JSON logging
│   ├── crud/                   # 🆕 Repository pattern
│   │   ├── base.py             # Generic CRUD base class
│   │   ├── crud_user.py        # User operations
│   │   └── crud_room.py        # Room operations
│   ├── models/                 # SQLAlchemy models
│   │   ├── users.py
│   │   ├── rooms.py
│   │   ├── bookings.py
│   │   ├── customer.py
│   │   └── schemas/            # Pydantic schemas
│   ├── services/               # Business logic
│   │   ├── s3_service.py       # S3 operations
│   │   ├── file_validator.py  # File validation
│   │   └── s3_cleanup.py       # Cleanup utilities
│   └── db/                     # Database setup
│       ├── base_db.py          # Engine + session
│       └── postgres_db.py      # Connection URI
├── tests/
│   ├── conftest.py             # Pytest fixtures
│   ├── unit/                   # Unit tests
│   └── integration/            # Integration tests
├── alembic/                    # Database migrations
├── backend_pre_start.py        # 🆕 DB health check script
├── initial_data.py             # 🆕 Seed admin user
├── pyproject.toml              # Dependencies + config
└── docker-compose.yml          # Docker setup
```

## 📡 API Endpoints

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
- `GET /health` - Liveness probe
- `GET /health/ready` - Readiness probe (checks DB)

## ⚙️ Configuration

Create a `.env` file:

```bash
# API
PROJECT_NAME="Hotel Management Admin"
API_V1_STR="/api/v1"
ENVIRONMENT="development"  # development, staging, production

# Database
PG_HOST=localhost
PG_PORT=5432
PG_USERNAME=postgres
PG_PASSWORD=postgres
PG_DB=hotel_management
PG_SCHEMA=public

# Security
SECRET_KEY=your-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# AWS S3
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
AWS_S3_BUCKET_NAME=hotel-management-uploads
AWS_S3_REGION=us-east-1

# File Upload
MAX_FILE_SIZE=10485760  # 10MB
ALLOWED_FILE_TYPES=["application/pdf", "image/jpeg", "image/png"]

# Monitoring (optional)
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project-id

# CORS (optional)
BACKEND_CORS_ORIGINS=["http://localhost:3000"]

# Server
PORT=8000
```

## 🛠️ Development

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
# Create migration
uv run alembic revision --autogenerate -m "description"

# Apply migrations
uv run alembic upgrade head

# Rollback one version
uv run alembic downgrade -1

# Check current version
uv run alembic current
```

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

### Initial Data Seeding

Create default admin user for development:

```bash
uv run python initial_data.py
```

Creates: `username: admin`, `password: admin123` (if no users exist)

## 🔒 Security Features

- **JWT Authentication**: OAuth2-compatible token-based auth
- **Password Hashing**: bcrypt with cost factor 12
- **File Validation**: Magic bytes verification, size limits, path sanitization
- **Path Traversal Prevention**: Filename sanitization
- **Database-first Uploads**: Prevents orphaned S3 files
- **CORS**: Configurable allowed origins
- **Sentry**: Error tracking and performance monitoring

## 🚢 Production Deployment

### Environment Variables

Set these in production:

```bash
ENVIRONMENT=production
SECRET_KEY=<strong-random-key>
SENTRY_DSN=<your-sentry-dsn>
PG_HOST=<production-db-host>
AWS_ACCESS_KEY_ID=<production-key>
AWS_SECRET_ACCESS_KEY=<production-secret>
```

### Docker

The Dockerfile includes:
- Multi-stage build for smaller images
- Pre-start health check
- UV for fast dependency installation
- Non-root user execution

### Health Checks

- **Liveness**: `GET /health` - Always returns 200 if app is running
- **Readiness**: `GET /health/ready` - Returns 200 only if DB is accessible

## 📊 Monitoring

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

All logs are output as JSON for easy parsing:

```json
{
  "timestamp": "2024-12-07 21:00:00,000",
  "level": "INFO",
  "name": "app.main",
  "message": "Application started"
}
```

## 🧩 Design Patterns

### Generic CRUD Repository

The `app/crud/base.py` provides reusable database operations:

```python
from app.crud import room

# Get all rooms
rooms = room.get_multi(db, skip=0, limit=100)

# Get by ID
room_obj = room.get(db, id_=1)

# Create
new_room = room.create(db, obj_in=RoomCreate(...))

# Update
updated = room.update(db, db_obj=room_obj, obj_in={"price": 150.0})

# Delete
room.remove(db, id_=1)
```

Benefits:
- DRY principle
- Consistent error handling
- Easy to test
- Type-safe with generics

## 📝 License

MIT

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `uv run pytest`
5. Run linting: `uv run ruff check --fix app/`
6. Submit a pull request

## 📚 Additional Documentation

- [CLAUDE.md](./CLAUDE.md) - AI development context and architecture details
- [GEMINI.md](./GEMINI.md) - Project overview and conventions