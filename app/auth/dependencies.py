from fastapi import Request, status, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.db.token_blocklist import token_in_blocklist
from .utils import decode_token


class TokenBearer(HTTPBearer):
    def __init__(self, auto_error: bool = True):
        super().__init__(auto_error=auto_error)

    async def __call__(self, request: Request) -> dict | None:
        creds: HTTPAuthorizationCredentials = await super().__call__(request)
        token = creds.credentials if creds else None

        if not token or not self.token_valid(token):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": "This token is invalid or expired",
                    "resolution": "Please get new token",
                },
            )

        token_data = decode_token(token)
        if not token_data:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"error": "Token decoding failed"},
            )

        if await token_in_blocklist(token_data["jti"]):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": "This token is invalid or has been revoked",
                    "resolution": "Please get new token",
                },
            )

        self.verify_token_data(token_data)
        return token_data

    def token_valid(self, token: str) -> bool:
        return decode_token(token) is not None

    def verify_token_data(self, token_data: dict):
        raise NotImplementedError("Override in child classes")


class AccessTokenBearer(TokenBearer):
    def verify_token_data(self, token_data: dict) -> None:
        if token_data and token_data["refresh"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Please provide an access token",
            )


class RefreshTokenBearer(TokenBearer):
    def verify_token_data(self, token_data: dict) -> None:
        if token_data and not token_data["refresh"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Please provide a refresh token",
            )


# JWT Token Bearer classes for WebSocket
class WebSocketTokenBearer(TokenBearer):
    """Token bearer for WebSocket authentication"""
    
    def verify_token_data(self, token_data: dict):
        if token_data and not token_data["refresh"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Please provide a refresh token",
            )

class UserTokenBearer(WebSocketTokenBearer):
    """Token bearer for regular users"""
    
    def verify_token_data(self, token_data: dict):
        # Add user-specific validation
        if not token_data.get("user_id"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"error": "Invalid user token"}
            )
