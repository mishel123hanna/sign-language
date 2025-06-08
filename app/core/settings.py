from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List
from pathlib import Path


class Settings(BaseSettings):
    # API Settings
    API_VERSION: str = "v1"
    API_PREFIX: str = f"/api/{API_VERSION}"
    # Project Information
    PROJECT_NAME: str = "sign language"
    PROJECT_DESCRIPTION: str = "backend for sign language app"
    CONTACT_NAME: str = "Mishel Hanna"
    CONTACT_URL: str = "https://github.com/mishel123hanna"
    CONTACT_EMAIL: str = "mishelhanna3@gmail.com"
    # TERMS_OF_SERVICE: str = "https://example.com/tos"

    # Database Settings 
    DATABASE_URL: str
    SUPABASE_URL: str
    SUPABASE_USER: str
    SUPABASE_PASSWORD: str
    SUPABASE_HOST: str
    SUPABASE_PORT: int
    SUPABASE_DB_NAME: str
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    DB_ECHO_LOG: bool = False
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 1800  # 30 minutes

    # Security Settings
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRY: int = 2

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]

    # MAIL_USERNAME: str
    # MAIL_PASSWORD: str
    # MAIL_FROM: str
    # MAIL_PORT: int
    # MAIL_SERVER: str
    # MAIL_FROM_NAME: str
    # MAIL_STARTTLS: bool = True
    # MAIL_SSL_TLS: bool = False
    # USE_CREDENTIALS: bool = True
    # VALIDATE_CERTS: bool = True
    # DOMAIN: str
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


# print(Path(__name__).resolve().parent / ".env")
settings = Settings()


broker_url = settings.REDIS_URL
result_backend = settings.REDIS_URL
broker_connection_retry_on_startup = True
