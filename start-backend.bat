@echo off
REM Hotel Management Admin - Backend Startup Script (Windows)
REM Quick start script for frontend developers

echo.
echo 🏨 Hotel Management Admin - Backend Setup
echo ==========================================
echo.

REM Check if Docker is running
docker info >nul 2>&1
if errorlevel 1 (
    echo ❌ Error: Docker is not running
    echo    Please start Docker Desktop and try again
    exit /b 1
)

REM Check if .env exists
if not exist .env (
    echo 📝 Creating .env file...
    (
        echo # API Configuration
        echo PROJECT_NAME="Hotel Management Admin"
        echo API_V1_STR="/api/v1"
        echo ENVIRONMENT="development"
        echo.
        echo # Database Configuration ^(Docker setup^)
        echo PG_HOST=db
        echo PG_PORT=5432
        echo PG_USERNAME=postgres
        echo PG_PASSWORD=postgres
        echo PG_DB=hotel_management
        echo PG_SCHEMA=public
        echo.
        echo # Security
        echo SECRET_KEY=dev-secret-key-for-frontend-testing
        echo ALGORITHM=HS256
        echo ACCESS_TOKEN_EXPIRE_MINUTES=30
        echo.
        echo # AWS S3 ^(Optional - file uploads won't work without real credentials^)
        echo AWS_ACCESS_KEY_ID=dummy
        echo AWS_SECRET_ACCESS_KEY=dummy
        echo AWS_S3_BUCKET_NAME=dummy-bucket
        echo AWS_S3_REGION=us-east-1
        echo.
        echo # File Upload
        echo MAX_FILE_SIZE=10485760
        echo.
        echo # CORS - Add your frontend URL here
        echo BACKEND_CORS_ORIGINS=["http://localhost:3000","http://localhost:5173","http://localhost:8080"]
        echo.
        echo # Server Port
        echo PORT=8080
    ) > .env
    echo ✅ Created .env file with default settings
) else (
    echo ✅ .env file already exists
)

echo.
echo 🚀 Starting backend services...
docker compose up -d

echo.
echo ⏳ Waiting for services to be ready...
echo    ^(This may take 2-3 minutes on first run^)

REM Wait for health check (simplified for Windows)
timeout /t 30 /nobreak >nul

echo.
echo ✅ Backend should be ready!
echo.
echo 📍 API Documentation: http://localhost:8050/docs
echo 📍 Health Check:      http://localhost:8050/api/v1/health
echo 📍 Database:          localhost:5432 ^(postgres/postgres^)
echo.
echo 📚 Quick Start Guide: See FRONTEND_QUICKSTART.md
echo.
echo 💡 Useful commands:
echo    docker compose logs -f     # View logs
echo    docker compose down        # Stop backend
echo    docker compose restart web # Restart API
echo.

pause
