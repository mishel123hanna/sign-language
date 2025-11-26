import re
from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator


class UserCreateModel(BaseModel):
    """Schema for user registration with enhanced validation."""

    username: str = Field(
        min_length=3,
        max_length=12,
        description="Username (3-12 characters, alphanumeric and underscore only)",
    )
    email: EmailStr = Field(max_length=25, description="Valid email address")
    password: str = Field(
        min_length=6, max_length=128, description="Password (6-128 characters)"
    )

    @field_validator("username")
    def validate_username(cls, v):
        """Validate username format and characters."""
        if not v:
            raise ValueError("Username cannot be empty")

        # Remove whitespace and convert to lowercase
        v = v.strip().lower()

        # Check for valid characters (alphanumeric and underscore only)
        if not re.match(r"^[a-z0-9_]+$", v):
            raise ValueError(
                "Username can only contain letters, numbers, and underscores"
            )

        # Check if username starts with underscore
        if v.startswith("_"):
            raise ValueError("Username cannot start with underscore")

        # Check for reserved usernames
        reserved_usernames = {"admin", "root", "api", "www", "mail", "test", "user"}
        if v in reserved_usernames:
            raise ValueError("This username is reserved and cannot be used")

        return v

    @field_validator("email")
    def validate_email(cls, v):
        """Additional email validation."""
        if not v:
            raise ValueError("Email cannot be empty")

        # Convert to lowercase for consistency
        v = str(v).strip().lower()

        # Basic length check after normalization
        if len(v) > 25:
            raise ValueError("Email address is too long")

        return v

    @field_validator("password")
    def validate_password(cls, v):
        """Enhanced password validation."""
        if not v:
            raise ValueError("Password cannot be empty")

        # Check for minimum complexity
        if len(v) < 6:
            raise ValueError("Password must be at least 6 characters long")

        return v

    class Config:
        """Pydantic configuration."""

        str_strip_whitespace = True  # Automatically strip whitespace
        validate_assignment = True  # Validate on assignment
        schema_extra = {
            "example": {
                "username": "johndoe",
                "email": "john@example.com",
                "password": "securepass123",
            }
        }


class UserModel(BaseModel):
    """Schema for user response with additional fields."""

    id: int = Field(description="Unique user identifier")
    username: str = Field(description="Username")
    email: str = Field(description="Email address")
    created_at: datetime = Field(description="Account creation timestamp")
    is_active: Optional[bool] = Field(default=True, description="Account status")

    class Config:
        """Pydantic configuration."""

        from_attributes = True  # For SQLModel compatibility
        json_encoders = {
            datetime: lambda v: v.isoformat()  # Ensure consistent datetime format
        }
        schema_extra = {
            "example": {
                "id": 1,
                "username": "johndoe",
                "email": "john@example.com",
                "created_at": "2023-01-01T12:00:00Z",
                "is_active": True,
            }
        }


class UserLoginModel(BaseModel):
    """Schema for user login with validation."""

    email: EmailStr = Field(max_length=25, description="Email address")
    password: str = Field(min_length=6, description="Password")

    @field_validator("email")
    def validate_email(cls, v):
        """Normalize email for login."""
        return str(v).strip().lower()

    class Config:
        """Pydantic configuration."""

        str_strip_whitespace = True
        schema_extra = {
            "example": {"email": "john@example.com", "password": "securepass123"}
        }


class TokenResponse(BaseModel):
    """Schema for token responses."""

    access_token: str = Field(description="JWT access token")
    refresh_token: Optional[str] = Field(None, description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: Optional[int] = Field(None, description="Token expiration in seconds")


class LoginResponse(BaseModel):
    """Schema for login response."""

    message: str = Field(description="Response message")
    access_token: str = Field(description="JWT access token")
    refresh_token: str = Field(description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    user: UserModel = Field(description="User information")


class UserUpdateModel(BaseModel):
    """Schema for user profile updates."""

    username: Optional[str] = Field(
        None, min_length=3, max_length=12, description="New username (optional)"
    )
    email: Optional[EmailStr] = Field(
        None, max_length=25, description="New email address (optional)"
    )

    @field_validator("username")
    def validate_username(cls, v):
        """Validate username if provided."""
        if v is None:
            return v

        v = v.strip().lower()

        if not re.match(r"^[a-z0-9_]+$", v):
            raise ValueError(
                "Username can only contain letters, numbers, and underscores"
            )

        if v.startswith("_"):
            raise ValueError("Username cannot start with underscore")

        reserved_usernames = {"admin", "root", "api", "www", "mail", "test", "user"}
        if v in reserved_usernames:
            raise ValueError("This username is reserved and cannot be used")

        return v

    @field_validator("email")
    def validate_email(cls, v):
        """Validate email if provided."""
        if v is None:
            return v
        return str(v).strip().lower()

    class Config:
        """Pydantic configuration."""

        str_strip_whitespace = True


class PasswordChangeModel(BaseModel):
    """Schema for password change requests."""

    current_password: str = Field(description="Current password")
    new_password: str = Field(
        min_length=6, max_length=128, description="New password (6-128 characters)"
    )
    confirm_password: str = Field(description="Confirm new password")

    @field_validator("confirm_password")
    def passwords_match(cls, v, values):
        """Ensure passwords match."""
        if "new_password" in values and v != values["new_password"]:
            raise ValueError("Passwords do not match")
        return v

    @field_validator("new_password")
    def validate_new_password(cls, v, values):
        """Validate new password."""
        if "current_password" in values and v == values["current_password"]:
            raise ValueError("New password must be different from current password")
        return v


class AvailabilityResponse(BaseModel):
    """Schema for availability check responses."""

    username_available: Optional[bool] = Field(
        None, description="Username availability"
    )
    email_available: Optional[bool] = Field(None, description="Email availability")


class ErrorResponse(BaseModel):
    """Schema for error responses."""

    detail: str = Field(description="Error message")
    error_code: Optional[str] = Field(None, description="Specific error code")
    timestamp: Optional[datetime] = Field(default_factory=datetime.now(timezone.utc))

    class Config:
        """Pydantic configuration."""

        json_encoders = {datetime: lambda v: v.isoformat()}
