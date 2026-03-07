import logging
import math
from datetime import date, datetime, timezone
from decimal import Decimal

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import extract, func
from sqlalchemy.exc import IntegrityError

from app.api.dependencies.common import CurrentUserDep, SessionDep
from app.crud import booking as crud_booking
from app.models.bookings import BookingCreate, BookingDB, BookingResponse, PaginatedBookingResponse
from app.models.customer import CustomerDB
from app.models.enums import BookingStatus, PaymentStatus
from app.models.rooms import RoomDB

logger = logging.getLogger(__name__)

router = APIRouter()


class PaidAmountRequest(BaseModel):
    paid_amount: Decimal = Field(ge=0, decimal_places=2)


class CheckInResponse(BaseModel):
    message: str


class CheckOutResponse(BaseModel):
    message: str
    additional_charges: Decimal


class CancelResponse(BaseModel):
    message: str


@router.get(
    "/bookings",
    response_model=PaginatedBookingResponse,
    summary="Get bookings by month and year",
    description="Retrieve bookings filtered by month/year with pagination metadata",
)
def get_bookings(
    current_user: CurrentUserDep,
    session: SessionDep,
    month: int = Query(..., ge=1, le=12, description="Month (1-12)"),
    year: int = Query(..., ge=2000, le=2100, description="Year (2000-2100)"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Records per page"),
):
    # Build filtered query — filter by scheduled_check_in month/year
    query = session.query(BookingDB).filter(
        extract("month", BookingDB.scheduled_check_in) == month,
        extract("year", BookingDB.scheduled_check_in) == year,
    )

    total_records = query.count()
    total_pages = math.ceil(total_records / per_page) if total_records > 0 else 0

    bookings = query.order_by(BookingDB.scheduled_check_in).offset((page - 1) * per_page).limit(per_page).all()

    return PaginatedBookingResponse(
        data=bookings,
        page=page,
        per_page=per_page,
        total_records=total_records,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_previous=page > 1,
    )


class TodayBookingSummary(BaseModel):
    """Summary counts of today's booking activity."""

    check_ins: int
    check_outs: int
    prebooked: int
    confirmed: int
    stays: int
    cancelled: int


@router.get(
    "/bookings/today",
    response_model=TodayBookingSummary,
    summary="Get today's booking summary",
    description="Get counts of today's check-ins, check-outs, prebooked, confirmed, and ongoing stays",
)
def get_today_bookings(
    current_user: CurrentUserDep,
    session: SessionDep,
):
    today = date.today()

    # Check-ins today (actual_check_in is today)
    check_ins = session.query(func.count(BookingDB.id)).filter(
        BookingDB.actual_check_in == today,
        BookingDB.booking_status == BookingStatus.CHECKED_IN.value,
    ).scalar()

    # Check-outs today (actual_check_out is today)
    check_outs = session.query(func.count(BookingDB.id)).filter(
        BookingDB.actual_check_out == today,
        BookingDB.booking_status == BookingStatus.CHECKED_OUT.value,
    ).scalar()

    # Prebooked for today
    prebooked = session.query(func.count(BookingDB.id)).filter(
        BookingDB.scheduled_check_in <= today,
        BookingDB.scheduled_check_out >= today,
        BookingDB.booking_status == BookingStatus.PREBOOKED.value,
    ).scalar()

    # Confirmed for today
    confirmed = session.query(func.count(BookingDB.id)).filter(
        BookingDB.scheduled_check_in <= today,
        BookingDB.scheduled_check_out >= today,
        BookingDB.booking_status == BookingStatus.CONFIRMED.value,
    ).scalar()

    # Stays: checked in before today and still not checked out
    stays = session.query(func.count(BookingDB.id)).filter(
        BookingDB.actual_check_in < today,
        BookingDB.booking_status == BookingStatus.CHECKED_IN.value,
    ).scalar()

    # Cancelled today (updated_at is today and status is cancelled)
    cancelled = session.query(func.count(BookingDB.id)).filter(
        func.date(BookingDB.updated_at) == today,
        BookingDB.booking_status == BookingStatus.CANCELLED.value,
    ).scalar()

    return TodayBookingSummary(
        check_ins=check_ins,
        check_outs=check_outs,
        prebooked=prebooked,
        confirmed=confirmed,
        stays=stays,
        cancelled=cancelled,
    )


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

        # If status is CHECKED_IN, auto-set actual check-in fields (direct walk-in)
        if booking.booking_status == BookingStatus.CHECKED_IN:
            now = datetime.now(timezone.utc)
            db_booking.actual_check_in = now.date()
            db_booking.actual_check_in_time = now.strftime("%I:%M %p").lstrip("0")

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
def check_in(booking_id: int, body: PaidAmountRequest, current_user: CurrentUserDep, session: SessionDep):
    # Locking strategy: Lock SINGLE booking to prevent concurrent status changes
    # (different from create_booking which locks ALL overlapping bookings)
    booking = session.query(BookingDB).filter(BookingDB.id == booking_id).with_for_update().first()

    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")

    # Validate status before check-in
    if booking.booking_status not in [BookingStatus.CONFIRMED.value, BookingStatus.PREBOOKED.value]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot check in booking with status: {booking.booking_status}. Booking must be CONFIRMED or PREBOOKED.",
        )

    now = datetime.now(timezone.utc)
    booking.actual_check_in = now.date()
    booking.actual_check_in_time = now.strftime("%I:%M %p").lstrip("0")  # e.g. "1:00 PM", "12:00 AM"
    booking.amount_paid = body.paid_amount
    booking.booking_status = BookingStatus.CHECKED_IN.value
    session.commit()
    session.refresh(booking)

    return CheckInResponse(message="Check-in successful")


@router.patch("/bookings/{booking_id}/check-out", response_model=CheckOutResponse)
def check_out(booking_id: int, body: PaidAmountRequest, current_user: CurrentUserDep, session: SessionDep):
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

    now = datetime.now(timezone.utc)
    booking.actual_check_out = now.date()
    booking.actual_check_out_time = now.strftime("%I:%M %p").lstrip("0")  # e.g. "2:00 PM", "11:00 AM"
    booking.amount_paid = body.paid_amount
    booking.booking_status = BookingStatus.CHECKED_OUT.value
    session.commit()
    session.refresh(booking)

    return CheckOutResponse(message="Check-out successful", additional_charges=booking.additional_charges)


@router.patch("/bookings/{booking_id}/cancel", response_model=CancelResponse)
def cancel_booking(booking_id: int, body: PaidAmountRequest, current_user: CurrentUserDep, session: SessionDep):
    # Locking strategy: Lock SINGLE booking to prevent concurrent status changes
    booking = session.query(BookingDB).filter(BookingDB.id == booking_id).with_for_update().first()

    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")

    if booking.booking_status not in [BookingStatus.PREBOOKED.value, BookingStatus.CONFIRMED.value]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Cannot cancel booking with status: {booking.booking_status}")

    booking.amount_paid = body.paid_amount
    booking.booking_status = BookingStatus.CANCELLED.value
    session.commit()
    session.refresh(booking)

    return CancelResponse(message="Booking cancelled successfully")
