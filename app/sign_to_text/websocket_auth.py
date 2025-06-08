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
from fastapi.exceptions import HTTPException
from app.auth.utils import decode_token

async def websocket_token_auth(websocket: WebSocket) -> dict:
    await websocket.accept()
    
    auth_header = websocket.headers.get("authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        await websocket.close(code=1008, reason="Missing token")
        return
    token = auth_header.split(" ")[1]
    print(token)    
    try:
        return decode_token(token)
    except HTTPException as e:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        raise  # Prevents further execution
