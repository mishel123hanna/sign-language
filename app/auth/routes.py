import logging
from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, Form, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.settings import settings
from app.db.config import get_session
from app.db.models import User
from app.db.token_blocklist import add_jti_to_blocklist

from .dependencies import AccessTokenBearer, RefreshTokenBearer
from .schemas import UserCreateModel, UserLoginModel, UserModel
from .services import UserService
from .utils import create_access_token, verify_password

logger = logging.getLogger(__name__)

auth_router = APIRouter()
user_service = UserService()


@auth_router.post(
    "/signup",
    response_model=UserModel,
    status_code=status.HTTP_201_CREATED,
    summary="Create new user account",
    description="Register a new user with username, email, and password",
)
async def create_user_account(
    user_data: Annotated[UserCreateModel, Form()],
    session: AsyncSession = Depends(get_session),
) -> UserModel:
    # Input sanitization
    username = user_data.username.strip().lower()
    email = user_data.email.strip().lower()

    try:
        # Validate input data

        if await user_service.get_user_by_email(user_data.email, session):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A user with this email already exists.",
            )

        user_data = UserCreateModel(
            username=username, email=email, password=user_data.password
        )

        # Create new user
        new_user = await user_service.create_user(user_data, session)
        logger.info(f"User created successfully: {new_user.id}")

        return new_user

    except HTTPException:
        raise
    except IntegrityError as e:
        # Handle race conditions and database constraints
        await session.rollback()
        error_msg = str(e.orig).lower()

        if "email" in error_msg or "unique.*email" in error_msg:
            detail = "A user with this email already exists."
        elif "username" in error_msg or "unique.*username" in error_msg:
            detail = "A user with this username already exists."
        else:
            detail = "User data conflicts with existing records."

        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=detail)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Validation error: {str(e)}",
        )
    except Exception as e:
        logger.error(f"Unexpected error in signup: {e}", exc_info=True)
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during registration.",
        )


@auth_router.post(
    "/login",
    status_code=status.HTTP_200_OK,
    summary="User login",
    description="Authenticate user and return access/refresh tokens",
)
async def login(
    login_data: Annotated[UserLoginModel, Form()],
    session: AsyncSession = Depends(get_session),
) -> JSONResponse:
    """
    Authenticate user and return JWT tokens with improved error handling.
    """
    try:
        # Sanitize email input
        email = login_data.email.strip().lower()

        # Get user by email
        user = await user_service.get_user_by_email(email, session)

        # Verify user exists and password is correct
        if not user or not verify_password(login_data.password, user.hashed_password):
            # Use generic message to prevent username enumeration
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Check if user account is active (if you have this field)
        if hasattr(user, "is_active") and not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Account is deactivated"
            )

        # Create tokens
        user_data = {"email": user.email, "user_id": user.id}

        access_token = create_access_token(user_data=user_data)
        refresh_token = create_access_token(
            user_data=user_data,
            refresh=True,
            expiry=timedelta(days=settings.REFRESH_TOKEN_EXPIRY),
        )

        # Log successful login (without sensitive data)
        logger.info(f"User logged in successfully: {user.id}")

        return JSONResponse(
            content={
                "message": "Login successful",
                "access_token": access_token,
                "refresh_token": refresh_token,
                "user": {"id": user.id, "email": user.email, "username": user.username},
                "token_type": "bearer",
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication service unavailable",
        )


@auth_router.get(
    "/refresh_token",
    status_code=status.HTTP_200_OK,
    summary="Refresh access token",
    description="Generate new access token using refresh token",
)
async def get_new_access_token(
    token_details: dict = Depends(RefreshTokenBearer()),
) -> JSONResponse:
    """
    Generate new access token using valid refresh token.
    """
    try:
        expiry_timestamp = token_details["exp"]
        current_time = datetime.now(timezone.utc)
        token_expiry = datetime.fromtimestamp(expiry_timestamp, tz=timezone.utc)

        if token_expiry < current_time:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Create new access token
        new_access_token = create_access_token(user_data=token_details["user"])

        return JSONResponse({"access_token": new_access_token, "token_type": "bearer"})

    except HTTPException:
        raise
    except KeyError as e:
        logger.error(f"Invalid token structure: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token format"
        )
    except Exception as e:
        logger.error(f"Token refresh error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh service unavailable",
        )


@auth_router.post(  # Changed to POST for better security practices
    "/logout",
    status_code=status.HTTP_200_OK,
    summary="User logout",
    description="Revoke access token and logout user",
)
async def logout(token_details: dict = Depends(AccessTokenBearer())) -> JSONResponse:
    """
    Logout user by adding token to blocklist.
    """
    try:
        jti = token_details["jti"]
        await add_jti_to_blocklist(jti)

        logger.info(
            f"User logged out: {token_details.get('user', {}).get('user_id', 'unknown')}"
        )

        return JSONResponse(
            content={
                "message": "Logged out successfully",
                "detail": "Token has been revoked",
            }
        )

    except KeyError as e:
        logger.error(f"Invalid token structure for logout: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token format"
        )
    except Exception as e:
        logger.error(f"Logout error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout service unavailable",
        )


async def get_current_user(
    token_data: dict = Depends(AccessTokenBearer()),
    session: AsyncSession = Depends(get_session),
) -> User:
    """
    Get current authenticated user with optimized query and error handling.
    """
    try:
        user_id = token_data["user"]["user_id"]

        # Optimized query with explicit select
        result = await session.exec(select(User).where(User.id == user_id))
        user = result.one_or_none()

        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        # Check if user is active (if you have this field)
        if hasattr(user, "is_active") and not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is deactivated",
            )

        return user

    except HTTPException:
        raise
    except KeyError as e:
        logger.error(f"Invalid token structure: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token format"
        )
    except Exception as e:
        logger.error(f"Get current user error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="User service unavailable",
        )


@auth_router.get(
    "/me",
    response_model=UserModel,
    summary="Get current user",
    description="Get current authenticated user's profile information",
)
async def get_current_user_profile(user: User = Depends(get_current_user)) -> UserModel:
    """
    Get current user's profile information.
    """
    return user
