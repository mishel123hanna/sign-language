from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, status
from ai_models.sign_to_text.tranlate_sign_language import process_frame_with_ai
from fastapi.responses import HTMLResponse
from app.core.websocket import manager
import asyncio
import logging
import json
from typing import Dict
from sqlmodel import Session
from app.db.config import get_session, async_engine
from app.db.models import User, TranslationHistory
from sqlmodel.ext.asyncio.session import AsyncSession
from app.auth.dependencies import AccessTokenBearer
from .websocket_auth import websocket_token_auth

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

sign_to_text_router = APIRouter()


# @sign_to_text_router.websocket(
#     "/ws/translate/{user_id}",
# )
# async def websocket_endpoint(websocket: WebSocket, user_id: int):
#     await websocket.accept()

#     try:
#         while True:
#             # Receive data (could be binary frame or text message)
#             try:
#                 # Try to receive as bytes first (video frames)
#                 data = await websocket.receive_bytes()

#                 # Get connection info for additional context
#                 # conn_info = manager.get_connection_info(user_id)
#                 # user_id = conn_info.get("user_id")

#                 # Process frame with AI model (include user context if needed)
#                 detected_text = await process_frame_with_ai(data, user_id=user_id)

#                 # Send result back to client
#                 response = {
#                     "type": "detection_result",
#                     "text": detected_text,
#                     "user_id": user_id,
#                     "timestamp": asyncio.get_event_loop().time(),
#                 }

#                 await manager.send_message(response, websocket)

#             except Exception as recv_error:
#                 # If not bytes, might be a text message (control message)
#                 try:
#                     text_data = await websocket.receive_text()
#                     control_message = json.loads(text_data)

#                     # Handle control messages (ping, settings, etc.)
#                     if control_message.get("type") == "ping":
#                         await manager.send_message({"type": "pong"}, user_id)

#                 except:
#                     logger.error(
#                         f"Error processing message from {user_id}: {recv_error}"
#                     )
#                     break

#     except WebSocketDisconnect:
#         manager.disconnect(user_id)
#     except Exception as e:
#         logger.error(f"WebSocket error for client {user_id}: {e}")
#         manager.disconnect(user_id)


# Cloud

# Store active WebSocket connections
# active_connections:list[WebSocket] = []
active_connections: Dict[int, WebSocket] = {}


@sign_to_text_router.websocket("/ws/translate/")
async def sign_to_text_websocket(
    websocket: WebSocket,
    # token_data: dict= Depends(AccessTokenBearer()),
    session: Session = Depends(get_session),
):
    # await websocket.accept()
    token_data = await websocket_token_auth(websocket)
    try:
        user_id = token_data["user"]["user_id"]
    except Exception as e:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    active_connections[user_id] = websocket
    # active_connections.append(websocket)
    print(active_connections)

    try:
        # Initialize variables for processing
        buffer = []
        last_prediction = ""
        prediction_count = 0

        while True:
            # Receive binary frame data
            frame_data = await websocket.receive_bytes()

            try:
                # # Convert binary data directly to numpy array
                # nparr = np.frombuffer(frame_data, np.uint8)
                # frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

                # if frame is None:
                #     await websocket.send_text("Error: Invalid image data received")
                #     continue

                # # Process the frame and detect signs
                prediction = await process_frame_with_ai(frame_data)
                # Simple filtering to avoid flickering predictions
                # if prediction == last_prediction:
                #     prediction_count += 1
                # else:
                #     prediction_count = 1
                #     last_prediction = prediction

                print("prediction:  ", prediction)
                # Only send stable predictions (same prediction for multiple frames)
                # if prediction_count >= 5 and prediction:
                # if prediction:
                # Send the detected text back to the client
                await websocket.send_text(prediction)

                async with AsyncSession(async_engine) as fresh_session:
                    # Log the translation to history (if user is authenticated)
                    user = session.get(User, user_id)
                    print("USER: ", user)
                    if user:
                        history_entry = TranslationHistory(
                            user_id=user_id,
                            input_type="sign_to_text",
                            input_content="live_video",
                            output_content=prediction,
                        )
                        fresh_session.add(history_entry)
                        await fresh_session.commit()  # await the commit
                        await fresh_session.refresh(history_entry)  # await refresh
                        print(
                            f"✅ Saved and committed: {prediction} for user {user_id}, ID: {history_entry.id}"
                        )

                    # Brief pause to control processing rate
                    await asyncio.sleep(0.1)

            except Exception as e:
                await websocket.send_text(f"Error processing frame: {str(e)}")

    except WebSocketDisconnect:
        if user_id in active_connections:
            del active_connections[user_id]
    except Exception as e:
        # Handle any other unexpected errors
        await websocket.send_text(f"Connection error: {str(e)}")
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
    <p><strong>Server replies:</strong> detected sign language text as string</p>
    """
