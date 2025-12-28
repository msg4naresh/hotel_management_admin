#!/bin/bash

# Hotel Management Admin - Backend Startup Script
# Quick start script for frontend developers

set -e

echo "🏨 Hotel Management Admin - Backend Setup"
echo "=========================================="
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Error: Docker is not running"
    echo "   Please start Docker Desktop and try again"
    exit 1
fi

# Check if .env exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    cat > .env << 'EOF'
# API Configuration
PROJECT_NAME="Hotel Management Admin"
API_V1_STR="/api/v1"
ENVIRONMENT="development"

# Database Configuration (Docker setup)
PG_HOST=db
PG_PORT=5432
PG_USERNAME=postgres
PG_PASSWORD=postgres
PG_DB=hotel_management
PG_SCHEMA=public

# Security
SECRET_KEY=dev-secret-key-for-frontend-testing
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# AWS S3 (Optional - file uploads won't work without real credentials)
AWS_ACCESS_KEY_ID=dummy
AWS_SECRET_ACCESS_KEY=dummy
AWS_S3_BUCKET_NAME=dummy-bucket
AWS_S3_REGION=us-east-1

# File Upload
MAX_FILE_SIZE=10485760

# CORS - Add your frontend URL here
BACKEND_CORS_ORIGINS=["http://localhost:3000","http://localhost:5173","http://localhost:8080"]

# Server Port
PORT=8080
EOF
    echo "✅ Created .env file with default settings"
else
    echo "✅ .env file already exists"
fi

echo ""
echo "🚀 Starting backend services..."
docker compose up -d

echo ""
echo "⏳ Waiting for services to be ready..."
echo "   (This may take 2-3 minutes on first run)"

# Wait for health check
max_attempts=60
attempt=0
while [ $attempt -lt $max_attempts ]; do
    if docker compose ps | grep -q "healthy"; then
        echo ""
        echo "✅ Backend is ready!"
        echo ""
        echo "📍 API Documentation: http://localhost:8050/docs"
        echo "📍 Health Check:      http://localhost:8050/api/v1/health"
        echo "📍 Database:          localhost:5432 (postgres/postgres)"
        echo ""
        echo "📚 Quick Start Guide: See FRONTEND_QUICKSTART.md"
        echo ""
        echo "💡 Useful commands:"
        echo "   docker compose logs -f     # View logs"
        echo "   docker compose down        # Stop backend"
        echo "   docker compose restart web # Restart API"
        echo ""
        exit 0
    fi
    attempt=$((attempt + 1))
    sleep 2
    echo -n "."
done

echo ""
echo "⚠️  Services started but health check timeout"
echo "   Check logs: docker compose logs -f"
exit 1
