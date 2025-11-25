import logging
import uuid
from datetime import datetime, timedelta, timezone

import jwt
from fastapi.exceptions import HTTPException
from passlib.context import CryptContext

from app.core.settings import settings

passwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def generate_hash_password(password: str) -> str:
    return passwd_context.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    return passwd_context.verify(password, hashed_password)


...  # the password functions


def create_access_token(
    user_data: dict, expiry: timedelta = timedelta(minutes=60), refresh: bool = False
) -> str:
    payload = {
        "user": user_data,
        "exp": datetime.now(timezone.utc) + expiry,
        "jti": str(uuid.uuid4()),
        "refresh": refresh,
    }

    token = jwt.encode(
        payload=payload, key=settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
    )

    return token


def decode_token(token: str) -> dict:
    try:
        token_data = jwt.decode(
            jwt=token, key=settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
        return token_data

    except jwt.ExpiredSignatureError:
        logging.error("Token has expired")
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidSignatureError:
        logging.error("Invalid token signature")
        raise HTTPException(status_code=401, detail="Invalid token signature")
    except jwt.PyJWTError as jwte:
        logging.exception(f"JWT Error: {jwte}")
        raise HTTPException(status_code=401, detail="Invalid token")
    except Exception as e:
        logging.exception(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Token validation failed")
