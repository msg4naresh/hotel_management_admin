import os
import pytest
import sys
from typing import AsyncGenerator, Generator
from unittest.mock import MagicMock

# Set testing flag to prevent database initialization
os.environ["TESTING"] = "1"

# Mock python-magic for testing
def create_magic_mock():
    def detect_mime(content):
        if content.startswith(b"%PDF"):
            return "application/pdf"
        if content.startswith(b"\xff\xd8\xff"):
            return "image/jpeg"
        if content.startswith(b"\x89PNG"):
            return "image/png"
        return "application/octet-stream"

    mock_instance = MagicMock()
    mock_instance.from_buffer = detect_mime

    magic_module = MagicMock()
    magic_module.Magic.return_value = mock_instance
    return magic_module

sys.modules["magic"] = create_magic_mock()

from httpx import AsyncClient, ASGITransport
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.db.base_db import get_session
from app.models.base import Base

# Test database setup
TEST_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session")
def db_engine():
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db(db_engine) -> Generator:
    connection = db_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
async def client(db) -> AsyncGenerator:
    def override_get_session():
        yield db

    app.dependency_overrides[get_session] = override_get_session

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c

    app.dependency_overrides.clear()


@pytest.fixture
def admin_user(db):
    from app.models.users import UserDB

    user = UserDB(
        username="admin",
        hashed_password=UserDB.hash_password("AdminPass123"),
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def test_customer(db):
    from app.models.customer import CustomerDB

    customer = CustomerDB(
        name="John Doe",
        email="john@example.com",
        phone="1234567890",
        address="123 Main St",
        proof_of_identity="Passport",
    )
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer


@pytest.fixture
def test_room(db):
    from app.models.rooms import RoomDB

    room = RoomDB(
        name="Deluxe Suite",
        room_type="Suite",
        floor=5,
        capacity=2,
        price_per_night=250.00,
        amenities=["WiFi", "AC", "TV"],
    )
    db.add(room)
    db.commit()
    db.refresh(room)
    return room


@pytest.fixture
def test_booking(db, test_room, test_customer):
    from app.models.bookings import BookingDB
    from datetime import date, timedelta

    check_in = date.today() + timedelta(days=1)
    check_out = check_in + timedelta(days=3)

    booking = BookingDB(
        room_id=test_room.id,
        customer_id=test_customer.id,
        scheduled_check_in=check_in,
        scheduled_check_out=check_out,
        total_amount=750.00,
    )
    db.add(booking)
    db.commit()
    db.refresh(booking)
    return booking


@pytest.fixture
def admin_auth_headers(admin_user):
    from app.core.security import create_access_token

    token = create_access_token(subject=str(admin_user.id))
    return {"Authorization": f"Bearer {token}"}
