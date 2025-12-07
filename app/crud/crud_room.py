from app.crud.base import CRUDBase
from app.models.rooms import RoomBase, RoomCreate, RoomDB


class CRUDRoom(CRUDBase[RoomDB, RoomCreate, RoomBase]):
    pass


room = CRUDRoom(RoomDB)
