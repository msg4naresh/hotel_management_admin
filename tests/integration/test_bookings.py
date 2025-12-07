from datetime import date, timedelta

import pytest
from httpx import AsyncClient


@pytest.mark.integration
async def test_create_booking(client: AsyncClient, test_room, test_customer, admin_auth_headers: dict):
    # Book for next week to avoid conflicts with fixture
    check_in = date.today() + timedelta(days=7)
    check_out = check_in + timedelta(days=3)

    response = await client.post(
        "/api/v1/create-booking",
        json={
            "room_id": test_room.id,
            "customer_id": test_customer.id,
            "scheduled_check_in": check_in.isoformat(),
            "scheduled_check_out": check_out.isoformat(),
            "total_amount": 900.00,
            "payment_status": "pending",
            "booking_status": "confirmed",
            "amount_paid": 0.0,
            "additional_charges": 0.0,
            "notes": "Test booking",
        },
        headers=admin_auth_headers,
    )

    assert response.status_code == 201
    data = response.json()
    assert data["room_id"] == test_room.id
    assert data["booking_status"] == "confirmed"


@pytest.mark.integration
async def test_create_booking_conflict(client: AsyncClient, test_booking, admin_auth_headers: dict):
    # Try to book the same room for the same dates as the fixture
    # The fixture books from tomorrow for 3 days

    response = await client.post(
        "/api/v1/create-booking",
        json={
            "room_id": test_booking.room_id,
            "customer_id": test_booking.customer_id,
            "scheduled_check_in": test_booking.scheduled_check_in.isoformat(),
            "scheduled_check_out": test_booking.scheduled_check_out.isoformat(),
            "total_amount": 900.00,
            "payment_status": "pending",
            "booking_status": "confirmed",
            "amount_paid": 0.0,
            "additional_charges": 0.0,
            "notes": "Conflict booking",
        },
        headers=admin_auth_headers,
    )

    # Use 422 if conflict check is a validator, or 400/409 depending on app logic
    # Assuming validation failure or conflict
    assert response.status_code in [400, 409, 422]
    # Assuming the app handles this logically


@pytest.mark.integration
async def test_list_bookings(client: AsyncClient, test_booking, admin_auth_headers: dict):
    response = await client.get("/api/v1/bookings", headers=admin_auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    booking_ids = [b["id"] for b in data]
    assert test_booking.id in booking_ids
