import logging
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.api.dependencies.common import CurrentUserDep, SessionDep
from app.models.bookings import BookingCreate, BookingDB, BookingResponse
from app.models.customer import CustomerDB
from app.models.enums import BookingStatus
from app.models.rooms import RoomDB

logger = logging.getLogger(__name__)

router = APIRouter()


class CheckInResponse(BaseModel):
    message: str


class CheckOutResponse(BaseModel):
    message: str
    additional_charges: float


class CancelResponse(BaseModel):
    message: str


@router.get(
    "/bookings",
    response_model=list[BookingResponse],
    summary="Get all bookings",
    description="Retrieve a list of all bookings",
)
def get_bookings(current_user: CurrentUserDep, session: SessionDep):
    bookings = session.query(BookingDB).all()
    return bookings


@router.post(
    "/create-booking",
    response_model=BookingResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new booking",
    description="Create a new booking with the provided details",
)
def create_booking(booking: BookingCreate, current_user: CurrentUserDep, session: SessionDep):
    # Check room availability with proper date parameters
    if BookingDB.is_room_occupied(session, booking.room_id, booking.scheduled_check_in, booking.scheduled_check_out):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Room is not available for the selected dates"
        )

    # Verify room exists
    room = session.query(RoomDB).filter(RoomDB.id == booking.room_id).first()
    if not room:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Room not found")

    # Verify customer exists
    customer = session.query(CustomerDB).filter(CustomerDB.id == booking.customer_id).first()
    if not customer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")

    # Create booking
    db_booking = BookingDB(**booking.model_dump())
    session.add(db_booking)
    session.commit()
    session.refresh(db_booking)
    return db_booking


@router.patch("/bookings/{booking_id}/check-in", response_model=CheckInResponse)
def check_in(booking_id: int, current_user: CurrentUserDep, session: SessionDep):
    booking = session.query(BookingDB).filter(BookingDB.id == booking_id).with_for_update().first()

    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    # Validate status before check-in
    if booking.booking_status not in [BookingStatus.PREBOOKED.value, BookingStatus.CONFIRMED.value]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot check in booking with status: {booking.booking_status}",
        )

    booking.actual_check_in = datetime.now(timezone.utc)
    booking.booking_status = BookingStatus.CHECKED_IN.value
    session.commit()

    return CheckInResponse(message="Check-in successful")


@router.patch("/bookings/{booking_id}/check-out", response_model=CheckOutResponse)
def check_out(booking_id: int, current_user: CurrentUserDep, session: SessionDep):
    booking = session.query(BookingDB).filter(BookingDB.id == booking_id).with_for_update().first()

    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    # Validate status before check-out
    if booking.booking_status != BookingStatus.CHECKED_IN.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot check out booking with status: {booking.booking_status}",
        )

    booking.actual_check_out = datetime.now(timezone.utc)
    booking.booking_status = BookingStatus.CHECKED_OUT.value
    session.commit()

    return CheckOutResponse(message="Check-out successful", additional_charges=float(booking.additional_charges))


@router.patch("/bookings/{booking_id}/cancel", response_model=CancelResponse)
def cancel_booking(booking_id: int, current_user: CurrentUserDep, session: SessionDep):
    booking = session.query(BookingDB).filter(BookingDB.id == booking_id).with_for_update().first()

    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    if booking.booking_status not in [BookingStatus.PENDING.value, BookingStatus.CONFIRMED.value]:
        raise HTTPException(status_code=400, detail="Cannot cancel booking in current status")

    booking.booking_status = BookingStatus.CANCELLED.value
    session.commit()

    return CancelResponse(message="Booking cancelled successfully")
