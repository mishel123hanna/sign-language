from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class TokenTiming(BaseModel):
    """Represents a single token with confidence and timing information."""

    token: str
    confidence: float = Field(ge=0.0, le=1.0)
    start_ms: int
    end_ms: int


class AIError(BaseModel):
    """Standard AI error envelope agreed with the AI team."""

    code: str
    message: str
    details: Dict[str, Any] = Field(default_factory=dict)


class TextToSignRequestPayload(BaseModel):
    """Payload sent to the AI service for text-to-sign translation."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    request_id: str
    text: str
    language_code: str = Field(default="en")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class TextToSignResult(BaseModel):
    """AI response for text-to-sign translation."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    request_id: str
    tokens: List[TokenTiming]
    video_path: Optional[Path]
    latency_ms: int


class SignToTextFramePayload(BaseModel):
    """Metadata accompanying a sign-language frame sent to the AI service."""

    request_id: str
    frame_id: str
    timestamp_ms: int = Field(
        default_factory=lambda: int(datetime.now(timezone.utc).timestamp() * 1000)
    )
    content_type: str = "image/jpeg"
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SignToTextStreamChunk(BaseModel):
    """Streaming chunk returned by the AI service for sign-to-text."""

    request_id: str
    frame_id: str
    token: str
    confidence: float = Field(ge=0.0, le=1.0)
    start_ms: int
    end_ms: int
    transcript: Optional[str] = None
    is_final: bool = False
    timing_info: Dict[str, Any] = Field(default_factory=dict)
