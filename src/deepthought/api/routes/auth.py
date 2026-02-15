"""Authentication endpoints for signup, signin, and user info."""

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from deepthought.api.auth import create_access_token, hash_password
from deepthought.api.dependencies import get_users_db_client
from deepthought.db import DynamoDBClient
from deepthought.models.users import AuthResponse, UserCreate, UserResponse

router = APIRouter()


@router.post(
    "/signup",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Creates a new user account with email, first name, last name, and password. Returns a JWT token.",
)
async def signup(
    request: UserCreate,
    users_db: DynamoDBClient = Depends(get_users_db_client),
) -> AuthResponse:
    """Register a new user account.

    1. Check if a user with this email already exists
    2. Hash the password with bcrypt
    3. Store the user record in DynamoDB (pk=email, no sort key)
    4. Generate a JWT token
    5. Return the token and user info
    """
    existing_user = await users_db.get_item(pk=request.email)
    if existing_user is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists",
        )

    password_hash = hash_password(request.password)
    now = datetime.now(timezone.utc)

    user_item: dict[str, Any] = {
        "pk": request.email,
        "first_name": request.first_name,
        "last_name": request.last_name,
        "password_hash": password_hash,
        "created_at": now.isoformat(),
    }
    await users_db.put_item(user_item)

    token = create_access_token(data={"sub": request.email})

    user_response = UserResponse(
        email=request.email,
        first_name=request.first_name,
        last_name=request.last_name,
        created_at=now,
    )

    return AuthResponse(token=token, user=user_response)
