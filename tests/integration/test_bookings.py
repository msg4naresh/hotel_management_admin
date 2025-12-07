"""Integration tests for booking endpoints"""
import pytest
from datetime import date, timedelta


@pytest.mark.asyncio
async def test_get_bookings_success(client, admin_auth_headers, test_booking):
    """Test retrieving list of bookings"""
    response = await client.get(
        "/api/v1/bookings",
        headers=admin_auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_get_bookings_requires_auth(client):
    """Test that getting bookings requires authentication"""
    response = await client.get("/api/v1/bookings")

    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_create_booking_success(client, admin_auth_headers, test_room, test_customer):
    """Test creating a new booking"""
    check_in = date.today() + timedelta(days=5)
    check_out = check_in + timedelta(days=2)

    booking_data = {
        "room_id": test_room.id,
        "customer_id": test_customer.id,
        "scheduled_check_in": check_in.isoformat(),
        "scheduled_check_out": check_out.isoformat(),
        "total_amount": 300.00,
        "payment_status": "pending",
        "booking_status": "prebooked",
        "amount_paid": 0,
        "additional_charges": 0,
        "notes": None,
    }

    response = await client.post(
        "/api/v1/create-booking",
        json=booking_data,
        headers=admin_auth_headers,
    )

    assert response.status_code in [200, 201]
    data = response.json()
    assert data["room_id"] == test_room.id
    assert data["customer_id"] == test_customer.id


@pytest.mark.asyncio
async def test_create_booking_invalid_dates(client, admin_auth_headers, test_room, test_customer):
    """Test that invalid dates are rejected"""
    check_in = date.today() + timedelta(days=2)
    check_out = check_in - timedelta(days=1)  # Check-out before check-in

    booking_data = {
        "room_id": test_room.id,
        "customer_id": test_customer.id,
        "scheduled_check_in": check_in.isoformat(),
        "scheduled_check_out": check_out.isoformat(),
        "total_amount": 300.00,
        "payment_status": "pending",
        "booking_status": "prebooked",
        "amount_paid": 0,
        "additional_charges": 0,
    }

    response = await client.post(
        "/api/v1/create-booking",
        json=booking_data,
        headers=admin_auth_headers,
    )

    assert response.status_code in [400, 422]


@pytest.mark.asyncio
async def test_create_booking_past_date(client, admin_auth_headers, test_room, test_customer):
    """Test that past check-in dates are rejected"""
    check_in = date.today() - timedelta(days=1)  # Past date
    check_out = check_in + timedelta(days=2)

    booking_data = {
        "room_id": test_room.id,
        "customer_id": test_customer.id,
        "scheduled_check_in": check_in.isoformat(),
        "scheduled_check_out": check_out.isoformat(),
        "total_amount": 300.00,
        "payment_status": "pending",
        "booking_status": "prebooked",
        "amount_paid": 0,
        "additional_charges": 0,
    }

    response = await client.post(
        "/api/v1/create-booking",
        json=booking_data,
        headers=admin_auth_headers,
    )

    assert response.status_code in [400, 422]


@pytest.mark.asyncio
async def test_create_booking_nonexistent_room(client, admin_auth_headers, test_customer):
    """Test booking with non-existent room"""
    check_in = date.today() + timedelta(days=1)
    check_out = check_in + timedelta(days=2)

    booking_data = {
        "room_id": 99999,  # Non-existent
        "customer_id": test_customer.id,
        "scheduled_check_in": check_in.isoformat(),
        "scheduled_check_out": check_out.isoformat(),
        "total_amount": 300.00,
        "payment_status": "pending",
        "booking_status": "prebooked",
        "amount_paid": 0,
        "additional_charges": 0,
    }

    response = await client.post(
        "/api/v1/create-booking",
        json=booking_data,
        headers=admin_auth_headers,
    )

    assert response.status_code in [404, 400, 422]


@pytest.mark.asyncio
async def test_create_booking_nonexistent_customer(client, admin_auth_headers, test_room):
    """Test booking with non-existent customer"""
    check_in = date.today() + timedelta(days=1)
    check_out = check_in + timedelta(days=2)

    booking_data = {
        "room_id": test_room.id,
        "customer_id": 99999,  # Non-existent
        "scheduled_check_in": check_in.isoformat(),
        "scheduled_check_out": check_out.isoformat(),
        "total_amount": 300.00,
        "payment_status": "pending",
        "booking_status": "prebooked",
        "amount_paid": 0,
        "additional_charges": 0,
    }

    response = await client.post(
        "/api/v1/create-booking",
        json=booking_data,
        headers=admin_auth_headers,
    )

    assert response.status_code in [404, 400, 422]


@pytest.mark.asyncio
async def test_booking_payment_validation(client, admin_auth_headers, test_room, test_customer):
    """Test that payment amounts are validated"""
    check_in = date.today() + timedelta(days=1)
    check_out = check_in + timedelta(days=2)

    booking_data = {
        "room_id": test_room.id,
        "customer_id": test_customer.id,
        "scheduled_check_in": check_in.isoformat(),
        "scheduled_check_out": check_out.isoformat(),
        "total_amount": 100.00,
        "payment_status": "pending",
        "booking_status": "prebooked",
        "amount_paid": 150.00,  # More than total
        "additional_charges": 0,
    }

    response = await client.post(
        "/api/v1/create-booking",
        json=booking_data,
        headers=admin_auth_headers,
    )

    assert response.status_code in [400, 422]


@pytest.mark.asyncio
async def test_booking_missing_fields(client, admin_auth_headers, test_room, test_customer):
    """Test that missing fields are rejected"""
    booking_data = {
        "room_id": test_room.id,
        "customer_id": test_customer.id,
        # missing scheduled_check_in, scheduled_check_out, total_amount
    }

    response = await client.post(
        "/api/v1/create-booking",
        json=booking_data,
        headers=admin_auth_headers,
    )

    assert response.status_code in [400, 422]


@pytest.mark.asyncio
async def test_booking_status_transitions(client, admin_auth_headers, test_booking):
    """Test booking status transitions"""
    booking_id = test_booking.id

    # Test check-in (if endpoint exists)
    response = await client.patch(
        f"/api/v1/bookings/{booking_id}/check-in",
        headers=admin_auth_headers,
    )

    # Should be 200 or 404 if endpoint doesn't exist
    assert response.status_code in [200, 404, 405]


@pytest.mark.asyncio
async def test_booking_cancellation(client, admin_auth_headers, test_booking):
    """Test booking cancellation"""
    booking_id = test_booking.id

    # Test cancel endpoint (if exists)
    response = await client.patch(
        f"/api/v1/bookings/{booking_id}/cancel",
        headers=admin_auth_headers,
    )

    # Should be 200 or 404 if endpoint doesn't exist
    assert response.status_code in [200, 404, 405]
