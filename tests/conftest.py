import os
import sys
from typing import AsyncGenerator
from unittest.mock import MagicMock

import boto3
import pytest
from httpx import AsyncClient
from moto import mock_aws

# Set testing environment BEFORE importing app modules
# This ensures settings are loaded with TESTING=True and init_db() is skipped
os.environ["TESTING"] = "1"
os.environ["AWS_ACCESS_KEY_ID"] = "testing"
os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
os.environ["AWS_SECURITY_TOKEN"] = "testing"
os.environ["AWS_SESSION_TOKEN"] = "testing"
os.environ["AWS_S3_REGION"] = "us-east-1"
os.environ["AWS_S3_BUCKET_NAME"] = "test-bucket"

# Now import app modules
from httpx import ASGITransport
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.api.dependencies.s3_deps import get_s3_service
from app.db.base_db import get_db
from app.main import app
from app.models.base import Base
from app.services.s3_service import S3Service


@pytest.fixture(scope="function")
def s3_client():
    """Mocked S3 client."""
    with mock_aws():
        s3 = boto3.client("s3", region_name="us-east-1")
        s3.create_bucket(Bucket="test-bucket")
        yield s3


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

# Test database setup
TEST_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session")
def db_engine():
    # Create tables once
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session_factory(db_engine):
    """
    Creates a new database connection for a test, binds SessionLocal to it,
    and starts a transaction. rolls back at end.
    """
    connection = db_engine.connect()
    transaction = connection.begin()

    # Bind the global SessionLocal to this connection
    from app.db import base_db

    # Save original bind
    original_bind = base_db.SessionLocal.kw.get("bind")

    # Configure to use the connection
    base_db.SessionLocal.configure(bind=connection)

    # Create a session for the test fixture usage
    session = base_db.SessionLocal()

    yield session

    session.close()
    transaction.rollback()
    connection.close()

    # Restore original bind (to engine)
    if original_bind:
        base_db.SessionLocal.configure(bind=original_bind)
    else:
        # Fallback if original bind was None or not set in kw
        base_db.SessionLocal.configure(bind=db_engine)


@pytest.fixture(scope="function")
def db(db_session_factory):
    """
    Yields the shared session.
    """
    yield db_session_factory


@pytest.fixture(scope="function")
async def client(db, s3_client) -> AsyncGenerator[AsyncClient, None]:
    def override_get_db():
        yield db

    def override_s3_service():
        return S3Service()

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_s3_service] = override_s3_service

    # Note: Because we rebound SessionLocal, calls to get_db()
    # (used in auth_deps) will ALSO use the same connection.
    # S3Service will use mocked AWS via moto context

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
    from datetime import date, timedelta

    from app.models.bookings import BookingDB

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

    token = create_access_token(subject=admin_user.username)
    return {"Authorization": f"Bearer {token}"}
