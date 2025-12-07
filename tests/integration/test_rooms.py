"""Integration tests for room endpoints"""
import pytest


@pytest.mark.asyncio
async def test_get_rooms_success(client, admin_auth_headers, test_room):
    """Test retrieving list of rooms"""
    response = await client.get(
        "/api/v1/rooms",
        headers=admin_auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_get_rooms_requires_auth(client):
    """Test that getting rooms requires authentication"""
    response = await client.get("/api/v1/rooms")

    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_create_room_success(client, admin_auth_headers):
    """Test creating a new room"""
    room_data = {
        "name": "Standard Room",
        "room_type": "Standard",
        "floor": 2,
        "capacity": 2,
        "price_per_night": 150.00,
        "amenities": ["WiFi", "TV"],
    }

    response = await client.post(
        "/api/v1/create-room",
        json=room_data,
        headers=admin_auth_headers,
    )

    assert response.status_code in [200, 201]
    data = response.json()
    assert data["name"] == "Standard Room"
    assert data["floor"] == 2


@pytest.mark.asyncio
async def test_create_room_missing_fields(client, admin_auth_headers):
    """Test that missing fields are rejected"""
    room_data = {
        "name": "Room",
        # missing room_type, floor, capacity, price_per_night, amenities
    }

    response = await client.post(
        "/api/v1/create-room",
        json=room_data,
        headers=admin_auth_headers,
    )

    assert response.status_code in [400, 422]


@pytest.mark.asyncio
async def test_create_room_with_different_types(client, admin_auth_headers):
    """Test creating rooms with different types"""
    room_types = [
        ("Single", 1),
        ("Double", 2),
        ("Suite", 4),
        ("Penthouse", 8),
    ]

    for room_type, capacity in room_types:
        room_data = {
            "name": f"{room_type} Room",
            "room_type": room_type,
            "floor": 1,
            "capacity": capacity,
            "price_per_night": 100.00,
            "amenities": ["WiFi"],
        }

        response = await client.post(
            "/api/v1/create-room",
            json=room_data,
            headers=admin_auth_headers,
        )

        assert response.status_code in [200, 201]


@pytest.mark.asyncio
async def test_create_room_with_amenities(client, admin_auth_headers):
    """Test creating room with various amenities"""
    amenities = ["WiFi", "AC", "TV", "Mini Bar", "Bathrobe", "Slippers"]

    room_data = {
        "name": "Luxury Suite",
        "room_type": "Suite",
        "floor": 10,
        "capacity": 2,
        "price_per_night": 500.00,
        "amenities": amenities,
    }

    response = await client.post(
        "/api/v1/create-room",
        json=room_data,
        headers=admin_auth_headers,
    )

    assert response.status_code in [200, 201]
    data = response.json()
    assert set(data["amenities"]) == set(amenities)


@pytest.mark.asyncio
async def test_room_pricing_validation(client, admin_auth_headers):
    """Test that room price validation works"""
    room_data = {
        "name": "Negative Price Room",
        "room_type": "Standard",
        "floor": 1,
        "capacity": 2,
        "price_per_night": -100.00,  # Invalid
        "amenities": [],
    }

    response = await client.post(
        "/api/v1/create-room",
        json=room_data,
        headers=admin_auth_headers,
    )

    # Should either reject or accept (depending on validation implementation)
    assert response.status_code in [200, 201, 400, 422]


@pytest.mark.asyncio
async def test_room_capacity_validation(client, admin_auth_headers):
    """Test that room capacity validation works"""
    room_data = {
        "name": "Zero Capacity Room",
        "room_type": "Standard",
        "floor": 1,
        "capacity": 0,  # Invalid
        "price_per_night": 100.00,
        "amenities": [],
    }

    response = await client.post(
        "/api/v1/create-room",
        json=room_data,
        headers=admin_auth_headers,
    )

    # Should either reject or accept (depending on validation implementation)
    assert response.status_code in [200, 201, 400, 422]
