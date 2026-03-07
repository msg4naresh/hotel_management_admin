from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import Boolean, Column, Integer, String, UniqueConstraint

from app.models.base import Base
from app.models.enums import Building, RoomStatus, RoomType


class RoomBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    room_number: str
    building: Building
    capacity: Literal[1, 2, 3, 4, 5, 6, 7, 8]
    room_type: RoomType
    ac: bool = False
    status: RoomStatus = RoomStatus.AVAILABLE


class RoomCreate(RoomBase):
    pass


class RoomStatusUpdate(BaseModel):
    status: RoomStatus


class RoomResponse(RoomBase):
    id: int


class UnavailableRoomResponse(BaseModel):
    """Room that is unavailable due to an existing booking."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    room_number: str
    building: str
    capacity: int
    room_type: str
    ac: bool
    status: str
    booking: "BookingBriefResponse | None" = None


class BookingBriefResponse(BaseModel):
    """Brief booking info explaining why a room is unavailable."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    customer_id: int
    scheduled_check_in: "date"
    scheduled_check_out: "date"
    scheduled_check_in_time: str | None
    scheduled_check_out_time: str | None
    booking_status: str
    payment_status: str
    total_amount: "Decimal"
    amount_paid: "Decimal"


class RoomAvailabilityResponse(BaseModel):
    """Categorized room availability response."""

    available: list[RoomResponse]
    not_available: list[UnavailableRoomResponse]
    not_cleaned: list[RoomResponse]


class RoomDB(Base):
    __tablename__ = "rooms"
    __table_args__ = (
        UniqueConstraint("building", "room_number", name="uq_building_room_number"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    room_number = Column(String(20), nullable=False)
    building = Column(String(20), nullable=False)
    capacity = Column(Integer, nullable=False)
    room_type = Column(String(20), nullable=False)
    ac = Column(Boolean, nullable=False, default=False)
    status = Column(String(20), nullable=False, default="available")
