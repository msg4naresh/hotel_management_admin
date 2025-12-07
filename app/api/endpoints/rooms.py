from fastapi import APIRouter, Depends, HTTPException, status
from app.models.rooms import RoomResponse, RoomCreate, RoomDB
from app.models.users import UserDB
from app.api.dependencies.auth_deps import get_current_user
from app.db.base_db import get_session
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/rooms", response_model=list[RoomResponse],
         summary="Get all rooms",
         description="Retrieve a list of all available rooms")
def get_rooms(current_user: UserDB = Depends(get_current_user)):
    try:
        with get_session() as session:
            rooms = RoomDB.get_all_rooms(session)
            return rooms
    except Exception as e:
        logger.exception("Error retrieving rooms")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve rooms"
        )

@router.post("/create-room", 
          response_model=RoomResponse,
          status_code=status.HTTP_201_CREATED,
          summary="Create a new room",
          description="Create a new room with the provided details")
def create_room(
    room: RoomCreate,
    current_user: UserDB = Depends(get_current_user)
):
    try:
        with get_session() as session:
            db_room = RoomDB(**room.model_dump())
            session.add(db_room)
            session.commit()
            session.refresh(db_room)
            return db_room
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create room"
        )
    

