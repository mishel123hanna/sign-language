from fastapi.websockets import WebSocket
from typing import Dict
import logging
import json
import asyncio

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WebSocketManager:
    """Manages WebSocket connections with authentication"""

    # def __init__(self):
    #     self.active_connections: Dict[str, Dict] = {}

    # async def connect(self, websocket: WebSocket, user_id: str):
    #     await websocket.accept()
    #     self.active_connections[user_id] = {
    #         "websocket": websocket,
    #         "user_id": user_id,
    #         "connected_at": asyncio.get_event_loop().time(),
    #     }
    #     logger.info(f"Client {user_id} (User: {user_id}) connected")

    # def disconnect(self, user_id: str):
    #     if user_id in self.active_connections:
    #         user_id = self.active_connections[user_id].get("user_id")
    #         del self.active_connections[user_id]
    #         logger.info(f"Client {user_id} (User: {user_id}) disconnected")

    # async def send_message(self, message: dict,websocket:WebSocket):
    #     if message["user_id"] in self.active_connections:
    #         await websocket.send(json.dumps(message))

    # def get_connection_info(self, user_id: str) -> dict:
    #     return self.active_connections.get(user_id, {})
    
    # -------------------


    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_message(self, message: str, websocket: WebSocket):
        await websocket.send_json(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)


manager = WebSocketManager()
