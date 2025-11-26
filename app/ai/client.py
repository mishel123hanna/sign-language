from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from pathlib import Path
from typing import AsyncIterator, Optional
from uuid import uuid4

from app.ai.schemas import (
    AIError,
    SignToTextFramePayload,
    SignToTextStreamChunk,
    TextToSignRequestPayload,
    TextToSignResult,
    TokenTiming,
)


class AIClientError(Exception):
    """Raised when the AI client cannot fulfill a request."""

    def __init__(self, error: AIError):
        self.error = error
        super().__init__(error.message)


class AIClient:
    """Contract for communicating with the external AI service."""

    async def translate_text_to_sign(
        self, payload: TextToSignRequestPayload
    ) -> TextToSignResult:
        raise NotImplementedError

    async def translate_sign_to_text_stream(
        self, payload: SignToTextFramePayload, frame_bytes: bytes
    ) -> AsyncIterator[SignToTextStreamChunk]:
        raise NotImplementedError


class MockAIClient(AIClient):
    """
    Deterministic mock implementation used during backend and frontend development.
    Replace this class with the real wire-up once the AI engineer exposes the models.
    """

    def __init__(
        self,
        sample_video: Path | str = Path("static/videos/test_video.mp4"),
        temp_dir: Path | str = Path("static/temp_ai_videos"),
    ):
        self.sample_video = Path(sample_video)
        self.temp_dir = Path(temp_dir)
        self.temp_dir.mkdir(parents=True, exist_ok=True)

    async def translate_text_to_sign(
        self, payload: TextToSignRequestPayload
    ) -> TextToSignResult:
        if not self.sample_video.exists():
            raise AIClientError(
                AIError(
                    code="SAMPLE_VIDEO_MISSING",
                    message="Sample video not found for mock AI client.",
                    details={"expected_path": str(self.sample_video)},
                )
            )

        start = datetime.now(timezone.utc)
        video_path = await self._copy_sample_video(payload.request_id)
        tokens = self._build_token_timings(payload.text)

        latency_ms = int((datetime.now(timezone.utc) - start).total_seconds() * 1000)

        return TextToSignResult(
            request_id=payload.request_id,
            tokens=tokens,
            video_path=video_path,
            latency_ms=latency_ms,
        )

    async def translate_sign_to_text_stream(
        self, payload: SignToTextFramePayload, frame_bytes: bytes
    ) -> AsyncIterator[SignToTextStreamChunk]:
        """
        Simulate streaming tokens back from the AI service.
        Deterministic output keeps the frontend stable while the model is in flight.
        """

        transcript = self._pick_transcript(payload)
        base_ms = payload.timestamp_ms
        token_windows = self._build_token_timings(transcript, base_ms)

        for index, token_timing in enumerate(token_windows):
            is_final = index == len(token_windows) - 1
            chunk = SignToTextStreamChunk(
                request_id=payload.request_id,
                frame_id=payload.frame_id,
                token=token_timing.token,
                confidence=token_timing.confidence,
                start_ms=token_timing.start_ms,
                end_ms=token_timing.end_ms,
                transcript=transcript if is_final else None,
                is_final=is_final,
                timing_info={"latency_ms": 30},
            )
            yield chunk
            await asyncio.sleep(0.03)  # small gap to mimic streaming cadence

    async def _copy_sample_video(self, request_id: str) -> Path:
        destination = self.temp_dir / f"{request_id}.mp4"
        if destination.exists():
            destination.unlink(missing_ok=True)

        def _copy() -> Path:
            destination.write_bytes(self.sample_video.read_bytes())
            return destination

        return await asyncio.to_thread(_copy)

    def _build_token_timings(
        self, text: str, start_ms: int = 0, token_duration_ms: int = 320
    ) -> list[TokenTiming]:
        tokens: list[str] = text.strip().split() or ["(silence)"]
        timings: list[TokenTiming] = []

        for index, token in enumerate(tokens):
            start = start_ms + index * token_duration_ms
            end = start + token_duration_ms
            timings.append(
                TokenTiming(
                    token=token,
                    confidence=0.92,
                    start_ms=start,
                    end_ms=end,
                )
            )
        return timings

    def _pick_transcript(self, payload: SignToTextFramePayload) -> str:
        """
        Keep outputs deterministic by hashing the frame_id.
        """
        canned = [
            "hello this is a placeholder response",
            "streaming sign language translation in progress",
            "mock response while the real model is being integrated",
        ]
        index = int(payload.frame_id, 16) % len(canned)
        return canned[index]


def build_text_to_sign_request(
    text: str, language_code: str, metadata: Optional[dict] = None
) -> TextToSignRequestPayload:
    """
    Factory for generating consistent request envelopes for the AI client.
    """
    return TextToSignRequestPayload(
        request_id=uuid4().hex,
        text=text,
        language_code=language_code,
        metadata=metadata or {},
    )


def build_sign_to_text_frame(
    metadata: Optional[dict] = None, content_type: str = "image/jpeg"
) -> SignToTextFramePayload:
    """
    Factory for creating frame payloads with the agreed contract.
    """
    now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
    return SignToTextFramePayload(
        request_id=uuid4().hex,
        frame_id=uuid4().hex,
        timestamp_ms=now_ms,
        content_type=content_type,
        metadata=metadata or {},
    )


# Shared mock client instance used across the app
ai_client: AIClient = MockAIClient()
