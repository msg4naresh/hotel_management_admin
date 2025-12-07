import re
from datetime import datetime, timezone

from pydantic import BaseModel, field_validator
from sqlalchemy import Column, DateTime, Integer, String

from app.models.base import Base


class CustomerBase(BaseModel):
    name: str
    email: str
    phone: str
    address: str
    proof_of_identity: str
    proof_image_url: str | None = None
    proof_image_filename: str | None = None

    class Config:
        from_attributes = True


class CustomerCreate(CustomerBase):
    @field_validator("email")
    @classmethod
    def email_validator(cls, v):
        # Simple email validation
        if not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", v):
            raise ValueError("Invalid email format")
        return v.lower()  # Normalize to lowercase

    @field_validator("phone")
    @classmethod
    def phone_validator(cls, v):
        # Remove common formatting characters
        cleaned = re.sub(r"[\s\-\(\)\.]", "", v)
        if not cleaned.isdigit() or len(cleaned) < 10:
            raise ValueError("Phone must contain at least 10 digits")
        return cleaned  # Store cleaned version

    @field_validator("name")
    @classmethod
    def name_validator(cls, v):
        if len(v.strip()) < 2:
            raise ValueError("Name must be at least 2 characters")
        return v.strip()


class CustomerResponse(CustomerBase):
    id: int


class CustomerDB(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    email = Column(String(50), unique=True, index=True, nullable=False)
    phone = Column(String(20), nullable=False)
    address = Column(String(200), nullable=False)
    proof_of_identity = Column(String(200), nullable=False)
    proof_image_url = Column(String(500), nullable=True)
    proof_image_filename = Column(String(255), nullable=True)
    uploaded_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
