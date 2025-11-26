# # auth_utils.py
# from jose import JWTError

# async def validate_access_token(token: str) -> dict:
#     """Reusable token validator (for both HTTP and WebSocket)"""
#     if not token:
#         raise HTTPException(status_code=403, detail="Token missing")
    
#     try:
#         token_data = decode_token(token)  # Your existing decode logic
#     except JWTError:
#         raise HTTPException(status_code=403, detail="Invalid token")
    
#     if await token_in_blocklist(token_data["jti"]):
#         raise HTTPException(status_code=403, detail="Token revoked")
    
#     if token_data.get("refresh"):
#         raise HTTPException(status_code=403, detail="Access token required")
    
#     return token_data

from fastapi import WebSocket, status

from app.auth.utils import decode_token


async def websocket_token_auth(websocket: WebSocket) -> dict | None:
    """
    Validate the Authorization header for a websocket connection.
    Avoid raising HTTPException inside a websocket flow (it triggers HTTP responses).
    """
    await websocket.accept()

    auth_header = websocket.headers.get("authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Missing token")
        return None

    token = auth_header.split(" ")[1]
    try:
        return decode_token(token)
    except Exception:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid token")
        return None
