from datetime import datetime, date, timedelta, timezone
from sqlalchemy import Column, Integer, ForeignKey, Date, DateTime, String, Numeric
from sqlalchemy.orm import relationship
from app.models.base import Base
from pydantic import BaseModel, field_validator
from app.models.enums import BookingStatus, PaymentStatus


def _utcnow():
    return datetime.now(timezone.utc)


class BookingDB(Base):
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(Integer, ForeignKey("rooms.id"))
    customer_id = Column(Integer, ForeignKey("customers.id"))

    # Booking dates
    scheduled_check_in = Column(Date)    # Original planned check-in
    scheduled_check_out = Column(Date)   # Original planned check-out
    actual_check_in = Column(DateTime, nullable=True)    # Actual check-in time
    actual_check_out = Column(DateTime, nullable=True)   # Actual check-out time

    # Status tracking
    booking_status = Column(String, default=BookingStatus.PREBOOKED.value)
    payment_status = Column(String, default=PaymentStatus.PENDING.value)

    # Payment tracking
    total_amount = Column(Numeric(10, 2))
    amount_paid = Column(Numeric(10, 2), default=0)

    # Additional charges (for late check-out etc.)
    additional_charges = Column(Numeric(10, 2), default=0)
    notes = Column(String, nullable=True)

    booking_date = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)
    
    # Relationships
    room = relationship("RoomDB")
    customer = relationship("CustomerDB")

    

    @classmethod
    def is_room_occupied(cls, session, room_id: int, check_in_date: date, check_out_date: date) -> bool:
        """
        Check if room has any current occupants or bookings for a specific date
        Args:
            session: Database session
            room_id: ID of the room to check
            check_date: Optional specific date to check (defaults to today)
        """
        return session.query(cls).filter(
            cls.room_id == room_id,
            cls.booking_status.in_([
                BookingStatus.CHECKED_IN.value, 
                BookingStatus.CONFIRMED.value, 
                BookingStatus.PREBOOKED.value
            ]),
            # Check if there's any overlap with existing bookings
            cls.scheduled_check_in < check_out_date,
            cls.scheduled_check_out > check_in_date
        ).first() is not None

    @classmethod
    def get_all_bookings(cls, session):
        return session.query(cls).all()

class BookingCreate(BaseModel):
    room_id: int
    customer_id: int
    scheduled_check_in: date
    scheduled_check_out: date
    payment_status: PaymentStatus
    booking_status: BookingStatus
    total_amount: float
    amount_paid: float
    additional_charges: float
    notes: str | None

    @field_validator('scheduled_check_in')
    @classmethod
    def check_in_date_validation(cls, v):
        if v < date.today():
            raise ValueError("Check-in date cannot be in the past")
        return v

    @field_validator('scheduled_check_out')
    @classmethod
    def check_out_date_validation(cls, v, info):
        check_in = info.data.get('scheduled_check_in')
        if check_in and v <= check_in:
            raise ValueError("Check-out date must be after check-in date")
        return v

    @field_validator('amount_paid')
    @classmethod
    def amount_paid_validation(cls, v, info):
        if v < 0:
            raise ValueError("Amount paid cannot be negative")
        if 'total_amount' in info.data and v > info.data['total_amount']:
            raise ValueError("Amount paid cannot exceed total amount")
        return v

    @field_validator('total_amount')
    @classmethod
    def total_amount_validation(cls, v):
        if v <= 0:
            raise ValueError("Total amount must be greater than zero")
        return v

class BookingResponse(BaseModel):
    id: int
    room_id: int
    customer_id: int
    scheduled_check_in: date
    scheduled_check_out: date
    actual_check_in: datetime | None
    actual_check_out: datetime | None
    booking_status: str
    payment_status: str
    total_amount: float
    amount_paid: float
    additional_charges: float
    notes: str | None
    booking_date: datetime

    class Config:
        from_attributes = True 