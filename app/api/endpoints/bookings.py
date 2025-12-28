import logging
from datetime import datetime, timezone
from decimal import Decimal

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError

from app.api.dependencies.common import CurrentUserDep, SessionDep
from app.crud import booking as crud_booking
from app.models.bookings import BookingCreate, BookingDB, BookingResponse
from app.models.customer import CustomerDB
from app.models.enums import BookingStatus, PaymentStatus
from app.models.rooms import RoomDB

logger = logging.getLogger(__name__)

router = APIRouter()


class CheckInResponse(BaseModel):
    message: str


class CheckOutResponse(BaseModel):
    message: str
    additional_charges: Decimal


class CancelResponse(BaseModel):
    message: str


@router.get(
    "/bookings",
    response_model=list[BookingResponse],
    summary="Get all bookings",
    description="Retrieve a paginated list of bookings",
)
def get_bookings(
    current_user: CurrentUserDep,
    session: SessionDep,
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
):
    return crud_booking.get_multi(session, skip=skip, limit=limit)


@router.post(
    "/create-booking",
    response_model=BookingResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new booking",
    description="Create a new booking with the provided details",
)
def create_booking(booking: BookingCreate, current_user: CurrentUserDep, session: SessionDep):
    # 1. Lock room row to prevent concurrent bookings
    room = session.query(RoomDB).filter(RoomDB.id == booking.room_id).with_for_update().first()
    if not room:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Room not found")

    # 2. Verify customer exists
    customer = session.query(CustomerDB).filter(CustomerDB.id == booking.customer_id).first()
    if not customer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")

    # 3. Lock ALL overlapping bookings for this room (prevents concurrent double-booking)
    # Locking strategy: Lock all conflicting bookings to prevent race conditions where
    # two concurrent requests both pass the availability check before either creates a booking
    overlapping = (
        session.query(BookingDB)
        .filter(
            BookingDB.room_id == booking.room_id,
            BookingDB.booking_status.in_(
                [BookingStatus.CHECKED_IN.value, BookingStatus.CONFIRMED.value, BookingStatus.PREBOOKED.value]
            ),
            BookingDB.scheduled_check_in < booking.scheduled_check_out,
            BookingDB.scheduled_check_out > booking.scheduled_check_in,
        )
        .with_for_update()
        .all()
    )

    if overlapping:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Room is not available for the selected dates"
        )

    # 4. Create booking within transaction lock
    try:
        db_booking = BookingDB(**booking.model_dump())
        session.add(db_booking)
        session.commit()
        session.refresh(db_booking)
        return db_booking
    except IntegrityError as e:
        session.rollback()
        logger.error(f"Integrity error creating booking: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Database integrity error. Please verify room and customer IDs are valid.",
        ) from e


@router.patch("/bookings/{booking_id}/check-in", response_model=CheckInResponse)
def check_in(booking_id: int, current_user: CurrentUserDep, session: SessionDep):
    # Locking strategy: Lock SINGLE booking to prevent concurrent status changes
    # (different from create_booking which locks ALL overlapping bookings)
    booking = session.query(BookingDB).filter(BookingDB.id == booking_id).with_for_update().first()

    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")

    # Validate status and payment before check-in
    if booking.booking_status not in [BookingStatus.CONFIRMED.value]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot check in booking with status: {booking.booking_status}. Booking must be CONFIRMED (paid).",
        )

    # Verify payment received
    if booking.payment_status not in [PaymentStatus.PAID.value, PaymentStatus.PARTIAL.value]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot check in without payment. Please confirm payment first.",
        )

    booking.actual_check_in = datetime.now(timezone.utc)
    booking.booking_status = BookingStatus.CHECKED_IN.value
    session.commit()
    session.refresh(booking)

    return CheckInResponse(message="Check-in successful")


@router.patch("/bookings/{booking_id}/check-out", response_model=CheckOutResponse)
def check_out(booking_id: int, current_user: CurrentUserDep, session: SessionDep):
    # Locking strategy: Lock SINGLE booking to prevent concurrent status changes
    booking = session.query(BookingDB).filter(BookingDB.id == booking_id).with_for_update().first()

    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")

    # Validate status before check-out
    if booking.booking_status != BookingStatus.CHECKED_IN.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot check out booking with status: {booking.booking_status}",
        )

    booking.actual_check_out = datetime.now(timezone.utc)
    booking.booking_status = BookingStatus.CHECKED_OUT.value
    session.commit()
    session.refresh(booking)

    return CheckOutResponse(message="Check-out successful", additional_charges=booking.additional_charges)


@router.patch("/bookings/{booking_id}/cancel", response_model=CancelResponse)
def cancel_booking(booking_id: int, current_user: CurrentUserDep, session: SessionDep):
    # Locking strategy: Lock SINGLE booking to prevent concurrent status changes
    booking = session.query(BookingDB).filter(BookingDB.id == booking_id).with_for_update().first()

    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")

    if booking.booking_status not in [BookingStatus.PREBOOKED.value, BookingStatus.CONFIRMED.value]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Cannot cancel booking with status: {booking.booking_status}")

    booking.booking_status = BookingStatus.CANCELLED.value
    session.commit()
    session.refresh(booking)

    return CancelResponse(message="Booking cancelled successfully")
