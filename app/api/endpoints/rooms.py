import logging

from fastapi import APIRouter, status

from app.api.dependencies.common import CurrentUserDep, SessionDep
from app.models.rooms import RoomCreate, RoomDB, RoomResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/rooms",
    response_model=list[RoomResponse],
    summary="Get all rooms",
    description="Retrieve a list of all available rooms",
)
def get_rooms(current_user: CurrentUserDep, session: SessionDep):
    rooms = session.query(RoomDB).all()
    return rooms


@router.post(
    "/create-room",
    response_model=RoomResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new room",
    description="Create a new room with the provided details",
)
def create_room(room: RoomCreate, current_user: CurrentUserDep, session: SessionDep):
    db_room = RoomDB(**room.model_dump())
    session.add(db_room)
    session.commit()
    session.refresh(db_room)
    return db_room
