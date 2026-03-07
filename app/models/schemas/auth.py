from pydantic import BaseModel


class TokenData(BaseModel):
    username: str | None = None


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenResponse(BaseModel):
    """Response model for login endpoint with user info"""

    access_token: str
    refresh_token: str
    token_type: str
    user_id: int
    username: str


class RefreshTokenRequest(BaseModel):
    """Request model for token refresh endpoint"""

    refresh_token: str


class RefreshTokenResponse(BaseModel):
    """Response model for token refresh endpoint"""

    access_token: str
    refresh_token: str
    token_type: str
