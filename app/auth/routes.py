# from datetime import timedelta, timezone
# from fastapi import APIRouter, Depends, status, Path, Form
# from .schemas import UserCreateModel, UserModel, UserLoginModel
# from .services import UserService
# from sqlmodel.ext.asyncio.session import AsyncSession
# from app.db.config import get_session
# from fastapi.exceptions import HTTPException
# from .utils import verify_password, create_access_token
# from fastapi.responses import JSONResponse
# from app.core.settings import settings
# from datetime import datetime
# from .dependencies import RefreshTokenBearer, AccessTokenBearer
# from app.db.redis import add_jti_to_blocklist
# from app.db.models import User
# from sqlmodel import select

# auth_router = APIRouter()
# user_service = UserService()


# @auth_router.post(
#     "/signup", response_model=UserModel, status_code=status.HTTP_201_CREATED
# )
# async def create_user_account(
#     username: str = Form(...),
#     email: str = Form(...),
#     password: str = Form(...),
#     session: AsyncSession = Depends(get_session)
# ):
#     try:
#         user_data = UserCreateModel(username=username, email=email, password=password)
#         if await user_service.get_user_by_email(user_data.email, session):
#             raise HTTPException(
#                 status_code=status.HTTP_400_BAD_REQUEST,
#                 detail="A user with this email already exists.",
#             )

#         if await user_service.get_user_by_username(user_data.username, session):
#             raise HTTPException(
#                 status_code=status.HTTP_400_BAD_REQUEST,
#                 detail="A user with this username already exists.",
#             )
#         new_user = await user_service.create_user(user_data, session)
#         return new_user
#     except Exception as e:
#         raise HTTPException(status_code=400, detail=str(e))

# @auth_router.post("/login", status_code=status.HTTP_200_OK)
# async def login(
#     login_data: UserLoginModel, session: AsyncSession = Depends(get_session)
# ):
#     user = await user_service.get_user_by_email(login_data.email, session)
#     if not user or not verify_password(login_data.password, user.hashed_password):
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN, detail="Invalid email or password"
#         )

#     access_token = create_access_token(
#         user_data={"email": user.email, "user_id": user.id}
#     )
#     refresh_token = create_access_token(
#         user_data={"email": user.email, "user_id": user.id},
#         refresh=True,
#         expiry=timedelta(days=settings.REFRESH_TOKEN_EXPIRY),
#     )
#     return JSONResponse(
#         {
#             "message": "login_successfully",
#             "access_token": access_token,
#             "refresh_token": refresh_token,
#             "user": {"email": user.email, "id": user.id},
#         }
#     )


# # # s
# # @auth_router.get("/users/{user_id}", response_model=UserRead)
# # async def get_user_by_id(
# #     user_id: int = Path(..., title="The ID of the user to get"),
# #     current_user: User = Depends(get_current_active_user),
# #     session: AsyncSession = Depends(get_session),
# # ):
# #     """
# #     Get user information by ID
# #     - Only accessible by authenticated users
# #     - Regular users can only see their own profile
# #     - Admin users can see any user profile
# #     """
# #     # Check if the user is requesting their own profile or has admin privileges
# #     if current_user.id != user_id and not getattr(current_user, "is_admin", False):
# #         raise HTTPException(
# #             status_code=status.HTTP_403_FORBIDDEN,
# #             detail="Not authorized to access this user's information",
# #         )

# #     # Get the requested user from the database
# #     user = session.get(User, user_id)

# #     if not user:
# #         raise HTTPException(
# #             status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
# #         )

# #     return UserRead(id=user.id, username=user.username, email=user.email)


# @auth_router.get("/refresh_token", status_code=status.HTTP_200_OK)
# async def get_new_access_token(token_details: dict = Depends(RefreshTokenBearer())):
#     expiry_timestamp = token_details["exp"]

#     if datetime.fromtimestamp(expiry_timestamp, tz=timezone.utc) < datetime.now(
#         timezone.utc
#     ):
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired token"
#         )
#     new_access_token = create_access_token(user_data=token_details["user"])
#     return JSONResponse({"access_token": new_access_token})


# @auth_router.get("/logout", status_code=status.HTTP_200_OK)
# async def revoke_token(token_details: dict = Depends(AccessTokenBearer())):

#     jti = token_details["jti"]

#     await add_jti_to_blocklist(jti)

#     return JSONResponse(content={"detail": "Logged Out Successfully"})


# async def get_current_user(
#     token_data: dict = Depends(AccessTokenBearer()),
#     session: AsyncSession = Depends(get_session),
# ) -> User:
#     user_id = token_data["user"]["user_id"]
#     result = await session.exec(select(User).where(User.id == user_id))
#     user = result.one_or_none()
#     if user is None:
#         raise HTTPException(status_code=404, detail="User not found")
#     return user


# @auth_router.get("/me", response_model=UserModel)
# async def read_current_user(user=Depends(get_current_user)):
#     return user


# optimized with cloud
from datetime import timedelta, timezone, datetime
from fastapi import APIRouter, Depends, status, Path, Form, HTTPException
from .schemas import UserCreateModel, UserModel, UserLoginModel
from .services import UserService
from sqlmodel.ext.asyncio.session import AsyncSession
from app.db.config import get_session
from .utils import verify_password, create_access_token
from fastapi.responses import JSONResponse
from app.core.settings import settings
from .dependencies import RefreshTokenBearer, AccessTokenBearer
from app.db.redis import add_jti_to_blocklist
from app.db.models import User
from sqlmodel import select, or_
from sqlalchemy.exc import IntegrityError
import asyncio
import logging
from typing import Dict, Any, Annotated

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

        # if await user_service.get_user_by_username(user_data.username, session):
        #     raise HTTPException(
        #         status_code=status.HTTP_400_BAD_REQUEST,
        #         detail="A user with this username already exists.",
        #     )
        user_data = UserCreateModel(username=username, email=email, password=user_data.password)

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
    login_data: Annotated[UserLoginModel, Form()], session: AsyncSession = Depends(get_session)
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


# # Additional optimized endpoint for checking username/email availability
# @auth_router.get(
#     "/check-availability",
#     status_code=status.HTTP_200_OK,
#     summary="Check username/email availability",
#     description="Check if username or email is available for registration"
# )
# async def check_availability(
#     username: str = None,
#     email: str = None,
#     session: AsyncSession = Depends(get_session)
# ) -> JSONResponse:
#     """
#     Check availability of username and/or email without creating user.
#     Useful for real-time validation in frontend forms.
#     """
#     if not username and not email:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="At least one parameter (username or email) is required"
#         )

#     try:
#         results = {}

#         if username and email:
#             # Check both in single query
#             username = username.strip().lower()
#             email = email.strip().lower()

#             result = await session.exec(
#                 select(User).where(
#                     or_(User.username == username, User.email == email)
#                 )
#             )
#             existing_user = result.one_or_none()

#             if existing_user:
#                 results['username_available'] = existing_user.username != username
#                 results['email_available'] = existing_user.email != email
#             else:
#                 results['username_available'] = True
#                 results['email_available'] = True

#         elif username:
#             username = username.strip().lower()
#             existing_user = await user_service.get_user_by_username(username, session)
#             results['username_available'] = existing_user is None

#         elif email:
#             email = email.strip().lower()
#             existing_user = await user_service.get_user_by_email(email, session)
#             results['email_available'] = existing_user is None

#         return JSONResponse(content=results)

#     except Exception as e:
#         logger.error(f"Availability check error: {e}", exc_info=True)
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail="Availability check service unavailable"
#         )
