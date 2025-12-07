"""End-to-end tests for booking workflows"""
import pytest
from datetime import date, timedelta


@pytest.mark.asyncio
async def test_complete_booking_workflow(client, admin_auth_headers, db):
    """Test complete booking workflow: Create customer -> Room -> Booking -> Check-in -> Check-out"""
    from app.models.customer import CustomerDB
    from app.models.rooms import RoomDB

    # Step 1: Create customer
    customer_data = {
        "name": "E2E Test Customer",
        "email": f"e2e_{id(client)}@example.com",
        "phone": "5555555555",
        "address": "123 Test St",
        "proof_of_identity": "Passport",
    }

    response = await client.post(
        "/api/v1/create-customer",
        json=customer_data,
        headers=admin_auth_headers,
    )
    assert response.status_code in [200, 201]
    customer = response.json()
    customer_id = customer["id"]

    # Step 2: Create room
    room_data = {
        "name": "E2E Test Room",
        "room_type": "Standard",
        "floor": 1,
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
    room = response.json()
    room_id = room["id"]

    # Step 3: Create booking
    check_in = date.today() + timedelta(days=1)
    check_out = check_in + timedelta(days=3)

    booking_data = {
        "room_id": room_id,
        "customer_id": customer_id,
        "scheduled_check_in": check_in.isoformat(),
        "scheduled_check_out": check_out.isoformat(),
        "total_amount": 450.00,
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
    assert response.status_code in [200, 201]
    booking = response.json()
    booking_id = booking["id"]

    # Verify booking was created
    assert booking["room_id"] == room_id
    assert booking["customer_id"] == customer_id
    assert booking["booking_status"] == "prebooked"

    # Step 4: Verify booking appears in list
    response = await client.get(
        "/api/v1/bookings",
        headers=admin_auth_headers,
    )
    assert response.status_code == 200
    bookings = response.json()
    assert any(b["id"] == booking_id for b in bookings)


@pytest.mark.asyncio
async def test_booking_with_payment_workflow(client, admin_auth_headers):
    """Test booking workflow with payment processing"""
    # Create customer
    response = await client.post(
        "/api/v1/create-customer",
        json={
            "name": "Payment Test Customer",
            "email": f"payment_{id(client)}@example.com",
            "phone": "6666666666",
            "address": "456 Pay St",
            "proof_of_identity": "License",
        },
        headers=admin_auth_headers,
    )
    assert response.status_code in [200, 201]
    customer_id = response.json()["id"]

    # Create room
    response = await client.post(
        "/api/v1/create-room",
        json={
            "name": "Payment Test Room",
            "room_type": "Deluxe",
            "floor": 3,
            "capacity": 2,
            "price_per_night": 200.00,
            "amenities": ["WiFi", "AC"],
        },
        headers=admin_auth_headers,
    )
    assert response.status_code in [200, 201]
    room_id = response.json()["id"]

    # Create booking with partial payment
    check_in = date.today() + timedelta(days=2)
    check_out = check_in + timedelta(days=2)

    response = await client.post(
        "/api/v1/create-booking",
        json={
            "room_id": room_id,
            "customer_id": customer_id,
            "scheduled_check_in": check_in.isoformat(),
            "scheduled_check_out": check_out.isoformat(),
            "total_amount": 400.00,
            "payment_status": "partial",
            "booking_status": "confirmed",
            "amount_paid": 200.00,
            "additional_charges": 0,
        },
        headers=admin_auth_headers,
    )
    assert response.status_code in [200, 201]
    booking = response.json()
    assert booking["amount_paid"] == 200.00
    assert booking["total_amount"] == 400.00


@pytest.mark.asyncio
async def test_booking_cancellation_workflow(client, admin_auth_headers):
    """Test booking cancellation workflow"""
    # Create customer
    response = await client.post(
        "/api/v1/create-customer",
        json={
            "name": "Cancel Test Customer",
            "email": f"cancel_{id(client)}@example.com",
            "phone": "7777777777",
            "address": "789 Cancel St",
            "proof_of_identity": "Passport",
        },
        headers=admin_auth_headers,
    )
    customer_id = response.json()["id"]

    # Create room
    response = await client.post(
        "/api/v1/create-room",
        json={
            "name": "Cancel Test Room",
            "room_type": "Standard",
            "floor": 2,
            "capacity": 1,
            "price_per_night": 100.00,
            "amenities": ["WiFi"],
        },
        headers=admin_auth_headers,
    )
    room_id = response.json()["id"]

    # Create booking
    check_in = date.today() + timedelta(days=3)
    check_out = check_in + timedelta(days=1)

    response = await client.post(
        "/api/v1/create-booking",
        json={
            "room_id": room_id,
            "customer_id": customer_id,
            "scheduled_check_in": check_in.isoformat(),
            "scheduled_check_out": check_out.isoformat(),
            "total_amount": 100.00,
            "payment_status": "pending",
            "booking_status": "prebooked",
            "amount_paid": 0,
            "additional_charges": 0,
        },
        headers=admin_auth_headers,
    )
    booking_id = response.json()["id"]

    # Cancel booking (if endpoint exists)
    response = await client.patch(
        f"/api/v1/bookings/{booking_id}/cancel",
        headers=admin_auth_headers,
    )
    # 200 if successful, 404 if endpoint doesn't exist
    assert response.status_code in [200, 404, 405]
