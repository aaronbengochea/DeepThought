"""Pydantic models for user authentication."""

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class User(BaseModel):
    """Full user model as stored in DynamoDB."""

    email: EmailStr = Field(..., description="User email address")
    name: str = Field(..., description="User display name")
    password_hash: str = Field(..., description="Bcrypt password hash")
    created_at: datetime = Field(..., description="Account creation timestamp")


class UserCreate(BaseModel):
    """Request model for user registration."""

    email: EmailStr = Field(..., description="User email address")
    name: str = Field(..., min_length=1, description="User display name")
    password: str = Field(..., min_length=8, description="User password")


class UserSignIn(BaseModel):
    """Request model for user sign-in."""

    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="User password")


class UserResponse(BaseModel):
    """Response model for user data (no sensitive fields)."""

    email: EmailStr = Field(..., description="User email address")
    name: str = Field(..., description="User display name")
    created_at: datetime = Field(..., description="Account creation timestamp")


class AuthResponse(BaseModel):
    """Response model for authentication endpoints."""

    token: str = Field(..., description="JWT access token")
    user: UserResponse = Field(..., description="Authenticated user data")
