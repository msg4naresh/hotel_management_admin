import logging
from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import OAuth2PasswordRequestForm
from jose import JWTError, jwt
from pydantic import BaseModel

from app.api.dependencies.common import CurrentUserDep, SessionDep
from app.core.config import settings
from app.core.security import create_access_token, create_refresh_token
from app.crud import crud_refresh_token
from app.crud import user as crud_user
from app.models.schemas.auth import RefreshTokenRequest, RefreshTokenResponse, TokenResponse
from app.models.users import UserCreate, UserDB, UserResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/token", response_model=TokenResponse, summary="User login", description="Login with username and password")
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

    # Revoke all existing refresh tokens for this user
    crud_refresh_token.revoke_all_for_user(session, user_id=user.id)

    access_token = create_access_token(
        subject=user.username, expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    refresh_token, refresh_expires = create_refresh_token(subject=user.username)

    # Store refresh token in database
    crud_refresh_token.create_refresh_token(
        session, user_id=user.id, token=refresh_token, expires_at=refresh_expires
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user_id": user.id,
        "username": user.username,
    }


@router.post(
    "/refresh",
    response_model=RefreshTokenResponse,
    summary="Refresh access token",
    description="Exchange a valid refresh token for a new access token and refresh token. The old refresh token is invalidated.",
)
def refresh_token(body: RefreshTokenRequest, session: SessionDep):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid refresh token",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # Decode the refresh token JWT
    try:
        payload = jwt.decode(body.refresh_token, settings.VALIDATED_SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        token_type: str = payload.get("type")

        if not username or token_type != "refresh_token":
            raise credentials_exception
    except JWTError:
        raise credentials_exception from None

    # Validate the refresh token exists in database and is not revoked
    stored_token = crud_refresh_token.get_by_token(session, token=body.refresh_token)
    if not stored_token or not crud_refresh_token.is_valid(stored_token):
        raise credentials_exception

    # Get user from database
    user = crud_user.get_by_username(session, username=username)
    if not user or not user.is_active:
        raise credentials_exception

    # Revoke the old refresh token (rotation)
    crud_refresh_token.revoke_token(session, db_obj=stored_token)

    # Issue new tokens
    new_access_token = create_access_token(
        subject=user.username, expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    new_refresh_token, refresh_expires = create_refresh_token(subject=user.username)

    # Store new refresh token
    crud_refresh_token.create_refresh_token(
        session, user_id=user.id, token=new_refresh_token, expires_at=refresh_expires
    )

    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
    }


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(user: UserCreate, session: SessionDep):
    try:
        return crud_user.create(session, obj_in=user)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/users",
    response_model=list[UserResponse],
    summary="Get all users",
    description="Retrieve a paginated list of registered users",
)
def get_users(
    current_user: CurrentUserDep,
    session: SessionDep,
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
):
    return crud_user.get_multi(session, skip=skip, limit=limit)


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


@router.post(
    "/change-password",
    summary="Change password",
    description="Change the authenticated user's password",
)
def change_password(
    body: ChangePasswordRequest,
    current_user: CurrentUserDep,
    session: SessionDep,
):
    if not current_user.verify_password(body.current_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )

    if len(body.new_password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be at least 6 characters",
        )

    current_user.hashed_password = UserDB.hash_password(body.new_password)
    session.commit()

    return {"message": "Password changed successfully"}
