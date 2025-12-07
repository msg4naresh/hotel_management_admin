from pydantic import BaseModel
from sqlalchemy import JSON, Column, Float, Integer, String

from app.models.base import Base


class RoomBase(BaseModel):
    name: str
    room_type: str
    floor: int
    capacity: int
    price_per_night: float
    amenities: list[str]

    class Config:
        from_attributes = True


class RoomCreate(RoomBase):
    pass


class RoomResponse(RoomBase):
    id: int


class RoomDB(Base):
    __tablename__ = "rooms"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    room_type = Column(String(50), nullable=False)
    floor = Column(Integer, nullable=False)
    capacity = Column(Integer, nullable=False)
    price_per_night = Column(Float, nullable=False)
    amenities = Column(JSON, nullable=False)
