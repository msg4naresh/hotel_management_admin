from app.crud.base import CRUDBase
from app.models.rooms import RoomBase, RoomCreate, RoomDB


class CRUDRoom(CRUDBase[RoomDB, RoomCreate, RoomBase]):
    """
    CRUD operations for rooms.

    Manages hotel room inventory including room types, amenities, and pricing.
    """

    pass


room = CRUDRoom(RoomDB)
