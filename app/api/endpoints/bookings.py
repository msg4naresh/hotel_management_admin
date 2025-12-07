from fastapi import APIRouter, Depends, HTTPException, status
from datetime import datetime, timezone
from app.models.bookings import BookingResponse, BookingCreate, BookingDB
from app.models.rooms import RoomDB
from app.models.customer import CustomerDB
from app.models.users import UserDB
from app.models.enums import BookingStatus
from app.api.dependencies.auth_deps import get_current_user
from app.db.base_db import get_session
import logging

logger = logging.getLogger(__name__)

router = APIRouter()



@router.get("/bookings", 
         response_model=list[BookingResponse],
         summary="Get all bookings",
         description="Retrieve a list of all bookings")
def get_bookings(current_user: UserDB = Depends(get_current_user)):
    try:
        with get_session() as session:
            bookings = BookingDB.get_all_bookings(session)
            return bookings
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve bookings"
        )

@router.post("/create-booking", 
          response_model=BookingResponse,
          status_code=status.HTTP_201_CREATED,
          summary="Create a new booking",
          description="Create a new booking with the provided details")
def create_booking(
    booking: BookingCreate,
    current_user: UserDB = Depends(get_current_user)
):
    try:
        with get_session() as session:
            # Check room availability with proper date parameters
            if BookingDB.is_room_occupied(
                session, 
                booking.room_id, 
                booking.scheduled_check_in,
                booking.scheduled_check_out
            ):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Room is not available for the selected dates"
                )
            
            # Verify room exists
            room = session.query(RoomDB).filter(RoomDB.id == booking.room_id).first()
            if not room:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Room not found"
                )
            
            # Verify customer exists
            customer = session.query(CustomerDB).filter(CustomerDB.id == booking.customer_id).first()
            if not customer:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Customer not found"
                )
                
            # Create booking
            db_booking = BookingDB(**booking.model_dump())
            session.add(db_booking)
            session.commit()
            session.refresh(db_booking)
            return db_booking
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create booking: {str(e)}"
        )

@router.patch("/bookings/{booking_id}/check-in")
def check_in(
    booking_id: int,
    current_user: UserDB = Depends(get_current_user)
):
    try:
        with get_session() as session:
            booking = session.query(BookingDB).filter(
                BookingDB.id == booking_id
            ).with_for_update().first()

            if not booking:
                raise HTTPException(status_code=404, detail="Booking not found")

            booking.actual_check_in = datetime.now(timezone.utc)
            booking.booking_status = BookingStatus.CHECKED_IN
            session.commit()

            return {"message": "Check-in successful"}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error checking in booking {booking_id}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check in"
        )

@router.patch("/bookings/{booking_id}/check-out")
def check_out(
    booking_id: int,
    current_user: UserDB = Depends(get_current_user)
):
    try:
        with get_session() as session:
            booking = session.query(BookingDB).filter(
                BookingDB.id == booking_id
            ).with_for_update().first()

            if not booking:
                raise HTTPException(status_code=404, detail="Booking not found")

            booking.actual_check_out = datetime.now(timezone.utc)
            booking.booking_status = BookingStatus.CHECKED_OUT
            session.commit()

            return {
                "message": "Check-out successful",
                "additional_charges": float(booking.additional_charges)
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error checking out booking {booking_id}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check out"
        )

@router.patch("/bookings/{booking_id}/cancel")
def cancel_booking(
    booking_id: int,
    current_user: UserDB = Depends(get_current_user)
):
    try:
        with get_session() as session:
            booking = session.query(BookingDB).filter(
                BookingDB.id == booking_id
            ).with_for_update().first()

            if not booking:
                raise HTTPException(status_code=404, detail="Booking not found")

            if booking.booking_status not in [BookingStatus.PENDING, BookingStatus.CONFIRMED]:
                raise HTTPException(
                    status_code=400,
                    detail="Cannot cancel booking in current status"
                )

            booking.booking_status = BookingStatus.CANCELLED
            session.commit()

            return {"message": "Booking cancelled successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error cancelling booking {booking_id}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cancel booking"
        )

