import pytest
from httpx import AsyncClient


@pytest.mark.integration
async def test_create_room(client: AsyncClient, admin_auth_headers: dict):
    response = await client.post(
        "/api/v1/create-room",
        json={
            "name": "Ocean View 101",
            "room_type": "Suite",
            "floor": 1,
            "capacity": 2,
            "price_per_night": 300.0,
            "amenities": ["WiFi", "Jacuzzi"],
        },
        headers=admin_auth_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Ocean View 101"
    assert data["price_per_night"] == 300.0
    assert "Jacuzzi" in data["amenities"]


@pytest.mark.integration
async def test_create_room_invalid_data(client: AsyncClient, admin_auth_headers: dict):
    # Missing required field "name"
    response = await client.post(
        "/api/v1/create-room",
        json={"room_type": "Suite", "floor": 1, "capacity": 2, "price_per_night": 300.0},
        headers=admin_auth_headers,
    )
    assert response.status_code == 422


@pytest.mark.integration
async def test_list_rooms(client: AsyncClient, test_room, admin_auth_headers: dict):
    response = await client.get("/api/v1/rooms", headers=admin_auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    # Check if our test_room is in the list
    room_ids = [room["id"] for room in data]
    assert test_room.id in room_ids
