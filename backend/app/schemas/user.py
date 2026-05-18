# backend/app/schemas/user.py
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field, field_validator


class UserCreate(BaseModel):
    email: EmailStr
    username: str = Field(min_length=3, max_length=100)
    password: str = Field(min_length=8, max_length=128)

    @field_validator("username")
    @classmethod
    def username_alphanumeric(cls, v: str) -> str:
        if not v.replace("_", "").replace("-", "").isalnum():
            raise ValueError("Username may only contain letters, digits, underscores and hyphens")
        return v.lower()


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    is_active: bool
    is_admin: bool
    subscription_type: str
    subscription_expires_at: Optional[datetime] = None
    telegram_id: Optional[str] = None
    favorite_leagues: Optional[List] = None
    preferred_markets: Optional[List] = None
    alert_threshold: float
    language: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    username: Optional[str] = Field(default=None, min_length=3, max_length=100)
    telegram_id: Optional[str] = None
    favorite_leagues: Optional[List[int]] = None
    preferred_markets: Optional[List[str]] = None
    alert_threshold: Optional[float] = Field(default=None, ge=0.0, le=100.0)
    language: Optional[str] = Field(default=None, max_length=10)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class TokenData(BaseModel):
    user_id: Optional[int] = None
    email: Optional[str] = None
