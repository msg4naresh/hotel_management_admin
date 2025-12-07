"""Tests for database models"""

from datetime import date, datetime, timedelta

from app.models.bookings import BookingDB
from app.models.customer import CustomerDB
from app.models.enums import BookingStatus, PaymentStatus
from app.models.rooms import RoomDB
from app.models.users import UserDB


# Customer model
def test_creates_customer():
    customer = CustomerDB(
        name="John Doe",
        email="john@example.com",
        phone="1234567890",
        address="123 Main St",
        proof_of_identity="Passport",
    )
    assert customer.name == "John Doe"
    assert customer.email == "john@example.com"


def test_customer_with_s3_url():
    customer = CustomerDB(
        name="Jane Smith",
        email="jane@example.com",
        phone="9876543210",
        address="456 Oak Ave",
        proof_of_identity="ID Card",
        proof_image_url="https://bucket.s3.amazonaws.com/proof.pdf",
        proof_image_filename="passport_scan.pdf",
    )
    assert "s3.amazonaws.com" in customer.proof_image_url
    assert customer.proof_image_filename == "passport_scan.pdf"


# User model
def test_creates_user():
    user = UserDB(
        username="testuser",
        hashed_password="hashed_password_here",
    )
    assert user.username == "testuser"
    assert user.hashed_password == "hashed_password_here"


def test_hashes_password():
    password = "SecurePassword123!"
    hashed = UserDB.hash_password(password)
    assert hashed != password
    assert len(hashed) > 20


def test_verifies_password():
    password = "TestPass123"
    hashed = UserDB.hash_password(password)
    user = UserDB(username="test", hashed_password=hashed)

    assert user.verify_password(password) is True
    assert user.verify_password("WrongPassword") is False


# Room model
def test_creates_room():
    room = RoomDB(
        name="Deluxe Suite",
        room_type="Suite",
        floor=5,
        capacity=2,
        price_per_night=250.00,
        amenities=["WiFi", "AC", "TV"],
    )
    assert room.name == "Deluxe Suite"
    assert room.room_type == "Suite"
    assert room.capacity == 2
    assert room.price_per_night == 250.00
    assert len(room.amenities) == 3


def test_room_with_empty_amenities():
    room = RoomDB(
        name="Basic Room",
        room_type="Basic",
        floor=1,
        capacity=1,
        price_per_night=50.00,
        amenities=[],
    )
    assert room.amenities == []


# Booking model
def test_creates_booking():
    check_in = date.today() + timedelta(days=1)
    check_out = check_in + timedelta(days=3)

    booking = BookingDB(
        room_id=1,
        customer_id=1,
        scheduled_check_in=check_in,
        scheduled_check_out=check_out,
        total_amount=300.00,
    )
    assert booking.room_id == 1
    assert booking.customer_id == 1
    assert booking.total_amount == 300.00


def test_booking_with_payment():
    check_in = date.today() + timedelta(days=1)
    check_out = check_in + timedelta(days=2)

    booking = BookingDB(
        room_id=1,
        customer_id=1,
        scheduled_check_in=check_in,
        scheduled_check_out=check_out,
        total_amount=200.00,
        amount_paid=100.00,
        additional_charges=50.00,
        booking_status=BookingStatus.CONFIRMED.value,
        payment_status=PaymentStatus.PARTIAL.value,
    )
    assert booking.amount_paid == 100.00
    assert booking.additional_charges == 50.00
    assert booking.booking_status == BookingStatus.CONFIRMED.value


def test_booking_with_checkin_times():
    check_in_date = date.today()
    check_out_date = check_in_date + timedelta(days=2)
    actual_check_in = datetime.now()
    actual_check_out = datetime.now() + timedelta(hours=48)

    booking = BookingDB(
        room_id=1,
        customer_id=1,
        scheduled_check_in=check_in_date,
        scheduled_check_out=check_out_date,
        actual_check_in=actual_check_in,
        actual_check_out=actual_check_out,
        total_amount=200.00,
        booking_status=BookingStatus.CHECKED_OUT.value,
    )
    assert booking.actual_check_in is not None
    assert booking.actual_check_out is not None


# Enums
def test_booking_status_enum():
    assert BookingStatus.PREBOOKED.value == "prebooked"
    assert BookingStatus.CONFIRMED.value == "confirmed"
    assert BookingStatus.CHECKED_IN.value == "checked_in"
    assert BookingStatus.CHECKED_OUT.value == "checked_out"


def test_payment_status_enum():
    assert PaymentStatus.PENDING.value == "pending"
    assert PaymentStatus.PARTIAL.value == "partial"
    assert PaymentStatus.PAID.value == "paid"
    assert PaymentStatus.REFUNDED.value == "refunded"
