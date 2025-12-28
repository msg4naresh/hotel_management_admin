from pydantic import BaseModel


class TokenData(BaseModel):
    username: str | None = None


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenResponse(BaseModel):
    """Response model for login endpoint with user info"""

    access_token: str
    token_type: str
    user_id: int
    username: str
