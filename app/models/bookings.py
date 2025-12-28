from datetime import date, datetime, timezone
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import relationship

from app.models.base import Base
from app.models.enums import BookingStatus, PaymentStatus


class BookingDB(Base):
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(Integer, ForeignKey("rooms.id", ondelete="RESTRICT"), nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id", ondelete="RESTRICT"), nullable=False)

    # Booking dates
    scheduled_check_in = Column(Date, nullable=False)  # Original planned check-in
    scheduled_check_out = Column(Date, nullable=False)  # Original planned check-out
    actual_check_in = Column(DateTime, nullable=True)  # Actual check-in time
    actual_check_out = Column(DateTime, nullable=True)  # Actual check-out time

    # Status tracking
    booking_status = Column(String, default=BookingStatus.PREBOOKED.value)
    payment_status = Column(String, default=PaymentStatus.PENDING.value)

    # Payment tracking
    total_amount = Column(Numeric(10, 2), nullable=False)
    amount_paid = Column(Numeric(10, 2), default=0)

    # Additional charges (for late check-out etc.)
    additional_charges = Column(Numeric(10, 2), default=0)
    notes = Column(String, nullable=True)

    booking_date = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False
    )

    # Relationships
    room = relationship("RoomDB")
    customer = relationship("CustomerDB")


class BookingCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    room_id: int
    customer_id: int
    scheduled_check_in: date
    scheduled_check_out: date
    payment_status: PaymentStatus
    booking_status: BookingStatus
    total_amount: Decimal = Field(decimal_places=2, gt=0)
    amount_paid: Decimal = Field(decimal_places=2, ge=0)
    additional_charges: Decimal = Field(decimal_places=2, ge=0, default=Decimal("0.00"))
    notes: str | None = None

    @field_validator("scheduled_check_in")
    @classmethod
    def check_in_date_validation(cls, v):
        if v < date.today():
            raise ValueError("Check-in date cannot be in the past")
        return v

    @field_validator("scheduled_check_out")
    @classmethod
    def check_out_date_validation(cls, v, info):
        check_in = info.data.get("scheduled_check_in")
        if check_in and v <= check_in:
            raise ValueError("Check-out date must be after check-in date")
        return v

    @model_validator(mode="after")
    def validate_payment_amounts(self) -> "BookingCreate":
        """Validate that amount_paid doesn't exceed total_amount."""
        if self.amount_paid > self.total_amount:
            raise ValueError("Amount paid cannot exceed total amount")
        return self


class BookingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    room_id: int
    customer_id: int
    scheduled_check_in: date
    scheduled_check_out: date
    actual_check_in: datetime | None
    actual_check_out: datetime | None
    booking_status: str
    payment_status: str
    total_amount: Decimal
    amount_paid: Decimal
    additional_charges: Decimal
    notes: str | None
    booking_date: datetime
    updated_at: datetime
