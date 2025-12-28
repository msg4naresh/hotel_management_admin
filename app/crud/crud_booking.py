from app.crud.base import CRUDBase
from app.models.bookings import BookingCreate, BookingDB, BookingResponse


class CRUDBooking(CRUDBase[BookingDB, BookingCreate, BookingCreate]):
    """
    CRUD operations for bookings.

    Handles room availability validation and booking status transitions.
    Endpoints use with_for_update() directly for concurrent booking prevention.
    """

    pass


booking = CRUDBooking(BookingDB)
