import asyncio
from datetime import datetime, timedelta, timezone

# JTI: JWT ID
JTI_EXPIRY = 3600  # seconds

# In-memory blocklist store with expiry tracking
_token_blocklist: dict[str, datetime] = {}
_lock = asyncio.Lock()


def _purge_expired(now: datetime) -> None:
    expired = [jti for jti, expires_at in _token_blocklist.items() if expires_at <= now]
    for jti in expired:
        _token_blocklist.pop(jti, None)


async def add_jti_to_blocklist(jti: str) -> None:
    expires_at = datetime.now(timezone.utc) + timedelta(seconds=JTI_EXPIRY)
    async with _lock:
        _purge_expired(datetime.now(timezone.utc))
        _token_blocklist[jti] = expires_at


async def token_in_blocklist(jti: str) -> bool:
    now = datetime.now(timezone.utc)
    async with _lock:
        _purge_expired(now)
        expires_at = _token_blocklist.get(jti)

    return bool(expires_at and expires_at > now)
