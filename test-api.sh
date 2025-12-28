#!/bin/bash

# Hotel Management Admin - API Test Script
# Quick test to verify the backend is working correctly

set -e

API_BASE="http://localhost:8050/api/v1"
TEST_USER="testuser_$(date +%s)"
TEST_PASS="testpass123"

echo "🧪 Testing Hotel Management Admin API"
echo "====================================="
echo ""

# Test 1: Health Check
echo "1️⃣  Testing health endpoint..."
if curl -sf "${API_BASE}/health" > /dev/null; then
    echo "   ✅ Health check passed"
else
    echo "   ❌ Health check failed - is the backend running?"
    echo "   Run: docker compose up -d"
    exit 1
fi

# Test 2: Database Readiness
echo ""
echo "2️⃣  Testing database connectivity..."
if curl -sf "${API_BASE}/health/ready" > /dev/null; then
    echo "   ✅ Database is ready"
else
    echo "   ❌ Database not ready - check logs: docker compose logs db"
    exit 1
fi

# Test 3: User Registration
echo ""
echo "3️⃣  Testing user registration..."
REGISTER_RESPONSE=$(curl -sf -X POST "${API_BASE}/auth/register" \
    -H "Content-Type: application/json" \
    -d "{\"username\":\"${TEST_USER}\",\"email\":\"${TEST_USER}@example.com\",\"password\":\"${TEST_PASS}\"}")

if [ -n "$REGISTER_RESPONSE" ]; then
    echo "   ✅ User registration successful"
    echo "   Created user: ${TEST_USER}"
else
    echo "   ❌ User registration failed"
    exit 1
fi

# Test 4: Login & Token Generation
echo ""
echo "4️⃣  Testing authentication..."
TOKEN_RESPONSE=$(curl -sf -X POST "${API_BASE}/auth/token" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "username=${TEST_USER}&password=${TEST_PASS}")

if [ -z "$TOKEN_RESPONSE" ]; then
    echo "   ❌ Login failed"
    exit 1
fi

ACCESS_TOKEN=$(echo "$TOKEN_RESPONSE" | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)

if [ -n "$ACCESS_TOKEN" ]; then
    echo "   ✅ Authentication successful"
    echo "   Token: ${ACCESS_TOKEN:0:20}..."
else
    echo "   ❌ Could not extract access token"
    exit 1
fi

# Test 5: Protected Endpoint Access
echo ""
echo "5️⃣  Testing protected endpoint (rooms)..."
ROOMS_RESPONSE=$(curl -sf -X GET "${API_BASE}/rooms" \
    -H "Authorization: Bearer ${ACCESS_TOKEN}")

if [ -n "$ROOMS_RESPONSE" ]; then
    echo "   ✅ Protected endpoint access successful"
else
    echo "   ❌ Could not access protected endpoint"
    exit 1
fi

# Test 6: Create Room
echo ""
echo "6️⃣  Testing room creation..."
ROOM_DATA='{
    "room_number": "TEST-'$(date +%s)'",
    "room_type": "SINGLE",
    "price_per_night": 99.99,
    "is_available": true
}'

CREATE_ROOM_RESPONSE=$(curl -sf -X POST "${API_BASE}/create-room" \
    -H "Authorization: Bearer ${ACCESS_TOKEN}" \
    -H "Content-Type: application/json" \
    -d "$ROOM_DATA")

if [ -n "$CREATE_ROOM_RESPONSE" ]; then
    echo "   ✅ Room creation successful"
    ROOM_ID=$(echo "$CREATE_ROOM_RESPONSE" | grep -o '"id":[0-9]*' | cut -d':' -f2)
    echo "   Created room ID: ${ROOM_ID}"
else
    echo "   ❌ Room creation failed"
    exit 1
fi

# All tests passed
echo ""
echo "========================================="
echo "✅ All API tests passed!"
echo ""
echo "🎉 Backend is working correctly"
echo ""
echo "📍 API Documentation: http://localhost:8050/docs"
echo "📍 Test credentials:"
echo "   Username: ${TEST_USER}"
echo "   Password: ${TEST_PASS}"
echo "   Token: ${ACCESS_TOKEN:0:30}..."
echo ""
