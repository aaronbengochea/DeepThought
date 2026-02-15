"""Authentication endpoints for signup, signin, and user info."""

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from deepthought.api.auth import create_access_token, hash_password, verify_password
from deepthought.api.dependencies import get_users_db_client
from deepthought.db import DynamoDBClient
from deepthought.models.users import AuthResponse, SignInResponse, UserCreate, UserResponse, UserSignIn

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


@router.post(
    "/signin",
    response_model=SignInResponse,
    status_code=status.HTTP_200_OK,
    summary="Sign in to an existing account",
    description="Authenticates a user with email and password. Returns a JWT token and email.",
)
async def signin(
    request: UserSignIn,
    users_db: DynamoDBClient = Depends(get_users_db_client),
) -> SignInResponse:
    """Sign in to an existing user account.

    1. Look up the user by email in DynamoDB
    2. Verify the password against the stored bcrypt hash
    3. Generate a JWT token
    4. Return the token and email
    """
    invalid_credentials = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid email or password",
    )

    user = await users_db.get_item(pk=request.email)
    if user is None:
        raise invalid_credentials

    password_matches = verify_password(request.password, user["password_hash"])
    if not password_matches:
        raise invalid_credentials

    token = create_access_token(data={"sub": request.email})

    return SignInResponse(token=token, email=request.email)
