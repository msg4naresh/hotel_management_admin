# Import all CRUD objects for easy access
from app.crud.crud_room import room
from app.crud.crud_user import user

__all__ = ["room", "user"]
