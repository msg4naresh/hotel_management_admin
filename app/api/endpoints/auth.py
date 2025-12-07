import logging
from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.api.dependencies.common import CurrentUserDep, SessionDep
from app.core.config import settings
from app.core.security import create_access_token
from app.models.users import UserCreate, UserDB, UserResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/token", summary="User login", description="Login with username and password")
def login(user_credentials: Annotated[OAuth2PasswordRequestForm, Depends()], session: SessionDep):
    user = session.query(UserDB).filter(UserDB.username == user_credentials.username).first()

    if not user or not user.verify_password(user_credentials.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(
        subject=user.username, expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    return {"access_token": access_token, "token_type": "bearer", "user_id": user.id, "username": user.username}


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(user: UserCreate, session: SessionDep):
    if session.query(UserDB).filter(UserDB.username == user.username).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already taken")

    now = datetime.now(timezone.utc)
    db_user = UserDB(
        username=user.username,
        hashed_password=UserDB.hash_password(user.password),
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user


@router.get(
    "/users",
    response_model=list[UserResponse],
    summary="Get all users",
    description="Retrieve a list of all registered users",
)
def get_users(current_user: CurrentUserDep, session: SessionDep):
    users = session.query(UserDB).all()
    return users
