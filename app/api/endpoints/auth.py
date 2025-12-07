import logging
from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.api.dependencies.common import CurrentUserDep, SessionDep
from app.core.config import settings
from app.core.security import create_access_token
from app.crud import user as crud_user
from app.models.users import UserCreate, UserResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/token", summary="User login", description="Login with username and password")
def login(user_credentials: Annotated[OAuth2PasswordRequestForm, Depends()], session: SessionDep):
    user = crud_user.authenticate(session, username=user_credentials.username, password=user_credentials.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not crud_user.is_active(user):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Inactive user")

    access_token = create_access_token(
        subject=user.username, expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    return {"access_token": access_token, "token_type": "bearer", "user_id": user.id, "username": user.username}


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(user: UserCreate, session: SessionDep):
    if crud_user.get_by_username(session, username=user.username):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already taken")

    return crud_user.create(session, obj_in=user)


@router.get(
    "/users",
    response_model=list[UserResponse],
    summary="Get all users",
    description="Retrieve a list of all registered users",
)
def get_users(current_user: CurrentUserDep, session: SessionDep):
    return crud_user.get_multi(session)
