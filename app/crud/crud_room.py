from datetime import date, datetime

from sqlalchemy import and_, not_
from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.bookings import BookingDB
from app.models.enums import BookingStatus
from app.models.rooms import RoomBase, RoomCreate, RoomDB


class CRUDRoom(CRUDBase[RoomDB, RoomCreate, RoomBase]):
    """
    CRUD operations for rooms.

    Manages hotel room inventory including room types, amenities, and pricing.
    """

    def get_available(
        self,
        db: Session,
        *,
        check_in: date | datetime,
        check_out: date | datetime,
        ac: bool | None = None,
    ) -> list[RoomDB]:
        """Get rooms that have no overlapping active bookings for the given date/time range."""
        # Active booking statuses that block a room
        active_statuses = [
            BookingStatus.PREBOOKED.value,
            BookingStatus.CONFIRMED.value,
            BookingStatus.CHECKED_IN.value,
        ]

        # Subquery: rooms with overlapping bookings
        overlapping_bookings = (
            db.query(BookingDB.room_id)
            .filter(
                BookingDB.booking_status.in_(active_statuses),
                BookingDB.scheduled_check_in < check_out,
                BookingDB.scheduled_check_out > check_in,
            )
            .subquery()
        )

        query = db.query(RoomDB).filter(
            RoomDB.id.notin_(overlapping_bookings),
            RoomDB.status == "available",
        )

        if ac is not None:
            query = query.filter(RoomDB.ac == ac)

        return query.order_by(RoomDB.building, RoomDB.room_number).all()


room = CRUDRoom(RoomDB)
