import logging
from datetime import date, datetime, time

from fastapi import APIRouter, HTTPException, Query, status

from app.api.dependencies.common import CurrentUserDep, SessionDep
from app.crud import room as crud_room
from app.models.bookings import BookingDB
from app.models.enums import BookingStatus, RoomStatus
from app.models.rooms import RoomAvailabilityResponse, RoomCreate, RoomDB, RoomResponse, RoomStatusUpdate, UnavailableRoomResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/rooms",
    response_model=list[RoomResponse],
    summary="Get all rooms",
    description="Retrieve a paginated list of available rooms",
)
def get_rooms(
    current_user: CurrentUserDep,
    session: SessionDep,
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
):
    return crud_room.get_multi(session, skip=skip, limit=limit)


@router.get(
    "/available-rooms",
    response_model=RoomAvailabilityResponse,
    summary="Get room availability",
    description="Get all rooms categorized as available, not available (with blocking booking details), and not cleaned",
)
def get_available_rooms(
    check_in: date = Query(..., description="Check-in date (YYYY-MM-DD)"),
    check_out: date = Query(..., description="Check-out date (YYYY-MM-DD)"),
    check_in_time: time | None = Query(None, description="Check-in time (HH:MM)"),
    check_out_time: time | None = Query(None, description="Check-out time (HH:MM)"),
    ac: bool | None = Query(None, description="Filter by A/C (true/false). Omit for all."),
    current_user: CurrentUserDep = None,
    session: SessionDep = None,
):
    check_in_dt = datetime.combine(check_in, check_in_time or time.min)
    check_out_dt = datetime.combine(check_out, check_out_time or time.max)

    if check_out_dt <= check_in_dt:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Check-out date/time must be after check-in date/time",
        )

    # Get all rooms (optionally filtered by AC)
    query = session.query(RoomDB)
    if ac is not None:
        query = query.filter(RoomDB.ac == ac)
    all_rooms = query.order_by(RoomDB.building, RoomDB.room_number).all()

    # Get overlapping bookings keyed by room_id
    active_statuses = [
        BookingStatus.PREBOOKED.value,
        BookingStatus.CONFIRMED.value,
        BookingStatus.CHECKED_IN.value,
    ]
    overlapping_bookings = (
        session.query(BookingDB)
        .filter(
            BookingDB.booking_status.in_(active_statuses),
            BookingDB.scheduled_check_in < check_out,
            BookingDB.scheduled_check_out > check_in,
        )
        .all()
    )
    booking_by_room: dict[int, BookingDB] = {}
    for b in overlapping_bookings:
        booking_by_room[b.room_id] = b  # latest overlapping booking per room

    available: list[RoomDB] = []
    not_available: list[UnavailableRoomResponse] = []
    not_cleaned: list[RoomDB] = []

    for room in all_rooms:
        if room.status == RoomStatus.NOT_CLEANED.value:
            not_cleaned.append(room)
        elif room.id in booking_by_room or room.status == RoomStatus.NOT_AVAILABLE.value:
            entry = UnavailableRoomResponse.model_validate(room)
            booking = booking_by_room.get(room.id)
            if booking:
                entry.booking = booking
            not_available.append(entry)
        else:
            available.append(room)

    return RoomAvailabilityResponse(
        available=available,
        not_available=not_available,
        not_cleaned=not_cleaned,
    )


@router.post(
    "/create-room",
    response_model=RoomResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new room",
    description="Create a new room with the provided details",
)
def create_room(room: RoomCreate, current_user: CurrentUserDep, session: SessionDep):
    # Check for duplicate room_number in the same building
    existing = session.query(RoomDB).filter(
        RoomDB.building == room.building.value,
        RoomDB.room_number == room.room_number,
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Room {room.room_number} already exists in {room.building.value}",
        )
    return crud_room.create(session, obj_in=room)


@router.patch(
    "/rooms/{room_id}/status",
    response_model=RoomResponse,
    summary="Update room status",
    description="Update the status of a room (available, not_available, not_cleaned)",
)
def update_room_status(
    room_id: int,
    status_update: RoomStatusUpdate,
    current_user: CurrentUserDep,
    session: SessionDep,
):
    room = crud_room.get(session, id_=room_id)
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Room with id {room_id} not found",
        )
    return crud_room.update(session, db_obj=room, obj_in={"status": status_update.status.value})


@router.delete(
    "/rooms/{room_id}",
    response_model=RoomResponse,
    summary="Delete a room",
    description="Delete a room by its ID",
)
def delete_room(
    room_id: int,
    current_user: CurrentUserDep,
    session: SessionDep,
):
    try:
        return crud_room.remove(session, id_=room_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Room with id {room_id} not found",
        )
