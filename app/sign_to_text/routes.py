import asyncio
import logging

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, status
from fastapi.responses import HTMLResponse
from sqlmodel import Session
from sqlmodel.ext.asyncio.session import AsyncSession

from app.ai.schemas import SignToTextStreamChunk
from app.db.config import async_engine, get_session
from app.db.models import TranslationHistory, User
from app.sign_to_text.services import stream_sign_to_text, to_error_payload
from app.sign_to_text.websocket_auth import websocket_token_auth

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

sign_to_text_router = APIRouter()

# Store active WebSocket connections
active_connections: dict[int, WebSocket] = {}


@sign_to_text_router.websocket("/ws/translate/")
async def sign_to_text_websocket(
    websocket: WebSocket,
    session: Session = Depends(get_session),
):
    token_data = await websocket_token_auth(websocket)
    if not token_data:
        return
    try:
        user_id = token_data["user"]["user_id"]
    except Exception:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    active_connections[user_id] = websocket
    print(active_connections)

    try:
        while True:
            frame_data = await websocket.receive_bytes()

            try:
                async for chunk in stream_sign_to_text(frame_data, user_id=user_id):
                    await websocket.send_json(chunk.model_dump())
                    await _persist_history_if_final(
                        chunk=chunk,
                        session=session,
                        user_id=user_id,
                    )
                await asyncio.sleep(0.05)
            except Exception as exc:
                error_payload = to_error_payload(
                    code="SIGN_TO_TEXT_PROCESSING_FAILED",
                    message=str(exc),
                    details={"user_id": user_id},
                )
                await websocket.send_json(error_payload.model_dump())

    except WebSocketDisconnect:
        if user_id in active_connections:
            del active_connections[user_id]
    except Exception as e:
        await websocket.send_json(
            to_error_payload(
                code="WS_CONNECTION_ERROR", message=str(e), details={"user_id": user_id}
            ).model_dump()
        )
        if user_id in active_connections:
            del active_connections[user_id]


@sign_to_text_router.get(
    "/ws-docs", include_in_schema=True, response_class=HTMLResponse
)
async def websocket_docs():
    return """
    <h2>WebSocket Endpoint: /ws/translate</h2>
    <p>Connect to <code>ws://localhost:8000/api/v1/ws/translate</code></p>
    <p>This WebSocket allows real-time sign language detection.</p>
    <p><strong>Client sends:</strong> video frames as bytes</p>
    <p><strong>Server replies:</strong> JSON chunks with tokens, confidence, timing</p>
    <pre>{
      "token": "hello",
      "confidence": 0.92,
      "start_ms": 0,
      "end_ms": 320,
      "is_final": false,
      "transcript": null
    }</pre>
    """


async def _persist_history_if_final(
    chunk: SignToTextStreamChunk, session: Session, user_id: int
):
    """
    Persist only final chunks to keep history concise while still supporting streaming updates.
    """
    if not chunk.is_final or not chunk.transcript:
        return

    async with AsyncSession(async_engine) as fresh_session:
        user = session.get(User, user_id)
        if not user:
            return

        history_entry = TranslationHistory(
            user_id=user_id,
            input_type="sign_to_text",
            input_content="live_video",
            output_content=chunk.transcript,
        )
        fresh_session.add(history_entry)
        await fresh_session.commit()
        await fresh_session.refresh(history_entry)
