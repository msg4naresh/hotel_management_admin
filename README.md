# Hotel Management System - Admin API

FastAPI-based backend API for managing hotel rooms, customers, bookings, and document uploads with PostgreSQL and AWS S3.

## Quick Start

```bash
# Install UV (fast Python package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync

# Run database migrations
uv run alembic upgrade head

# Start development server
uv run uvicorn app.main:app --reload
```

Visit http://localhost:8000/docs for interactive API documentation.

## Docker Deployment

```bash
docker compose up -d
```

Access at http://localhost:8050

## Testing

```bash
# Run all tests
uv run pytest tests/ -v

# Run with coverage
uv run pytest tests/ --cov=app --cov-report=html

# Run specific test types
uv run pytest tests/unit/ -v           # Unit tests
uv run pytest tests/integration/ -v    # Integration tests
uv run pytest tests/e2e/ -v            # End-to-end tests
```

## Core Features

- **Authentication**: JWT-based admin authentication
- **Room Management**: Create and list hotel rooms
- **Customer Management**: Manage customer records with document uploads
- **Booking Management**: Handle reservations, check-ins, check-outs
- **Document Storage**: AWS S3 integration for customer proof documents
- **Database**: PostgreSQL with Alembic migrations

## Tech Stack

- **FastAPI** 0.120+ - Modern async web framework
- **PostgreSQL** 17 - Database
- **Python** 3.14 - With free-threaded mode + JIT
- **SQLAlchemy** 2.0+ - ORM
- **Alembic** - Database migrations
- **AWS S3** - Document storage (via boto3)
- **UV** - Fast Python package manager
- **pytest** 8.0+ - Testing framework

## API Endpoints

All endpoints prefixed with `/api/v1`:

### Authentication
- `POST /auth/login` - Login and get JWT token

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

### Documents
- `POST /upload-document/{customer_id}` - Upload customer document to S3
- `DELETE /documents/{customer_id}` - Delete customer document

### Health
- `GET /health` - Liveness probe
- `GET /health/ready` - Readiness probe (checks database)

## Development

### Code Quality

```bash
# Format code
uv run black app/ tests/
uv run isort app/ tests/

# Lint
uv run ruff check --fix app/ tests/

# Type check
uv run mypy app/
```

### Database Migrations

```bash
# Create migration
uv run alembic revision --autogenerate -m "description"

# Apply migrations
uv run alembic upgrade head

# Check status
uv run alembic current
```

### Package Management

```bash
# Add dependency
uv add package-name

# Add dev dependency
uv add --dev package-name

# Sync dependencies
uv sync
```

## Project Structure

```
hotel_management_admin/
├── app/
│   ├── main.py              # FastAPI application entry
│   ├── api/
│   │   ├── routes.py        # Central router
│   │   └── endpoints/       # API endpoints
│   ├── services/            # Business logic
│   │   ├── s3_service.py
│   │   ├── file_validator.py
│   │   └── s3_cleanup.py
│   ├── models/              # SQLAlchemy models
│   ├── db/                  # Database config
│   └── core/                # Config & utilities
├── tests/                   # Test suite
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── alembic/                 # Database migrations
├── pyproject.toml           # Project config & dependencies
├── uv.lock                  # Locked dependencies
└── docker-compose.yml       # Docker setup
```

## Environment Variables

Create a `.env` file:

```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/hotel_db

# AWS S3
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
AWS_S3_BUCKET_NAME=your_bucket
AWS_S3_REGION=us-east-1

# Security
SECRET_KEY=your_secret_key_here
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Server
PORT=8000
```

## Security Features

- JWT token-based authentication
- Password hashing with bcrypt
- File validation (magic bytes, size limits, sanitization)
- Path traversal prevention
- Database-first upload pattern (prevents orphaned S3 files)

## CI/CD

GitHub Actions workflow runs on every push:
- Tests (unit, integration, e2e)
- Code quality checks (ruff, black, mypy)
- Migration validation

See `.github/workflows/tests.yml` for details.

## Deployment

The application uses the `PORT` environment variable for Cloud Run compatibility.

For architecture details and AI development context, see [CLAUDE.md](./CLAUDE.md).

## License

MIT