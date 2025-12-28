import logging

from fastapi import APIRouter, Query, status

from app.api.dependencies.common import CurrentUserDep, SessionDep
from app.crud import room as crud_room
from app.models.rooms import RoomCreate, RoomResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/rooms",
    response_model=list[RoomResponse],
    summary="Get all rooms",
    description="Retrieve a paginated list of available rooms",
)
def get_rooms(
    current_user: CurrentUserDep,
    session: SessionDep,
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
):
    return crud_room.get_multi(session, skip=skip, limit=limit)


@router.post(
    "/create-room",
    response_model=RoomResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new room",
    description="Create a new room with the provided details",
)
def create_room(room: RoomCreate, current_user: CurrentUserDep, session: SessionDep):
    return crud_room.create(session, obj_in=room)
