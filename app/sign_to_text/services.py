from __future__ import annotations

from typing import AsyncIterator, Dict

from app.ai.client import ai_client, build_sign_to_text_frame
from app.ai.schemas import AIError, SignToTextStreamChunk


async def stream_sign_to_text(
    frame_data: bytes, user_id: int
) -> AsyncIterator[SignToTextStreamChunk]:
    """
    Adapter that wraps the AI client stream for the websocket route.
    Attaches stable metadata agreed with the AI team.
    """
    frame_payload = build_sign_to_text_frame(metadata={"user_id": user_id})
    async for chunk in ai_client.translate_sign_to_text_stream(
        frame_payload, frame_data
    ):
        yield chunk


def to_error_payload(code: str, message: str, details: Dict | None = None) -> AIError:
    """Helper to produce standardized AI errors."""
    return AIError(code=code, message=message, details=details or {})
