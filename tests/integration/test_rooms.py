import pytest
from httpx import AsyncClient


@pytest.mark.integration
async def test_create_room(client: AsyncClient, admin_auth_headers: dict):
    response = await client.post(
        "/api/v1/create-room",
        json={
            "room_number": "102",
            "building": "building_1",
            "capacity": 2,
            "room_type": "delux",
            "ac": True,
        },
        headers=admin_auth_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["room_number"] == "102"
    assert data["building"] == "building_1"
    assert data["ac"] is True


@pytest.mark.integration
async def test_create_room_invalid_data(client: AsyncClient, admin_auth_headers: dict):
    # Missing required field "room_number"
    response = await client.post(
        "/api/v1/create-room",
        json={"building": "building_1", "capacity": 2, "room_type": "delux"},
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
