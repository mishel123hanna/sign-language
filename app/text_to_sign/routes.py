import asyncio
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import aiofiles
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse
from pydantic import field_validator
from sqlmodel import Field, SQLModel, select
from sqlmodel.ext.asyncio.session import AsyncSession
from tenacity import retry, stop_after_attempt, wait_exponential

from app.auth.dependencies import AccessTokenBearer
from app.db.config import async_engine, get_session
from app.db.models import TranslationHistory
from app.utils.exceptions import StorageError, VideoGenerationError

# from app.utils.video_service import VideoService
from app.utils.storage_service import StorageService

# Configure logging
logger = logging.getLogger(__name__)


# Constants
class Config:
    MAX_TEXT_LENGTH = 1000
    VIDEO_BUCKET = "signs-generated-by-ai"
    TEMP_VIDEO_DIR = Path("static/temp_videos")
    SUPPORTED_LANGUAGES = {"ar", "en"}
    MAX_CONCURRENT_GENERATIONS = 10
    VIDEO_GENERATION_TIMEOUT = 300  # 5 minutes
    CLEANUP_BATCH_SIZE = 100
    DEFAULT_HISTORY_LIMIT = 20
    MAX_HISTORY_LIMIT = 100
    # Add path to your test video
    TEST_VIDEO_PATH = Path("static/videos/test_video.mp4")  # Update this path


# Initialize services
storage_service = StorageService()

# Semaphore for concurrent video generation
generation_semaphore = asyncio.Semaphore(Config.MAX_CONCURRENT_GENERATIONS)

text_to_sign_router = APIRouter(
    prefix="/text-to-sign",
    responses={
        500: {"description": "Internal server error"},
        422: {"description": "Validation error"},
        429: {"description": "Too many requests"},
    },
)


class TextToSignRequest(SQLModel):
    """Request model for text to sign translation with enhanced validation"""

    text: str = Field(
        ...,
        min_length=1,
        max_length=Config.MAX_TEXT_LENGTH,
        description="Text to convert to sign language",
    )
    language_code: str = Field(default="ar", description="Language code for the text")

    @field_validator("language_code")
    def validate_language_code(cls, v):
        if v not in Config.SUPPORTED_LANGUAGES:
            raise ValueError(
                f"Language code must be one of: {', '.join(Config.SUPPORTED_LANGUAGES)}"
            )
        return v

    @field_validator("text")
    def validate_text(cls, v):
        # Remove excessive whitespace and validate content
        cleaned_text = " ".join(v.strip().split())
        if not cleaned_text:
            raise ValueError("Text cannot be empty or only whitespace")
        return cleaned_text


class TextToSignResponse(SQLModel):
    """Response model for text to sign translation"""

    video_url: str = Field(..., description="URL of the generated sign language video")
    translation_id: Optional[int] = Field(
        None, description="Database ID of the translation"
    )
    message: str = Field(default="Video uploaded successfully")
    generation_time_ms: Optional[int] = Field(
        None, description="Time taken to upload video in milliseconds"
    )


class TranslationHistoryResponse(SQLModel):
    """Response model for translation history"""

    id: int
    input_content: str
    output_content: str
    timestamp: datetime
    language_code: str


class VideoGenerationService:
    """Service class for video operations - modified for testing with existing videos"""

    def __init__(self):
        self.temp_dir = Config.TEMP_VIDEO_DIR
        self.temp_dir.mkdir(parents=True, exist_ok=True)

    async def generate_video_filename(self, user_id: str) -> str:
        """Generate a unique video filename with user context"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"user_{user_id}/{timestamp}_{uuid.uuid4().hex[:8]}.mp4"

    @retry(
        stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def upload_to_storage(self, file_path: Path, destination_path: str) -> str:
        """Upload file to Supabase Storage with retry logic"""
        try:
            return await storage_service.upload_video(file_path, destination_path)
        except Exception as e:
            logger.error(f"Failed to upload video {destination_path}: {str(e)}")
            raise StorageError(f"Failed to upload video: {str(e)}")

    async def prepare_test_video(
        self, text: str, language_code: str, user_id: str
    ) -> Path:
        """
        For testing: Copy existing video to temp location with unique name
        In production, this would be replaced with actual video generation
        """
        try:
            # Check if test video exists
            if not Config.TEST_VIDEO_PATH.exists():
                raise VideoGenerationError(
                    f"Test video not found at {Config.TEST_VIDEO_PATH}"
                )

            # Generate unique filename for the copy
            output_filename = f"temp_{uuid.uuid4().hex[:8]}.mp4"
            output_path = self.temp_dir / output_filename

            # Copy the test video to temp location
            logger.info(f"Copying test video for text: '{text}' (user: {user_id})")
            async with aiofiles.open(Config.TEST_VIDEO_PATH, "rb") as src:
                content = await src.read()

            async with aiofiles.open(output_path, "wb") as dst:
                await dst.write(content)

            logger.info(f"Test video prepared at: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Failed to prepare test video: {str(e)}")
            raise VideoGenerationError(f"Test video preparation failed: {str(e)}")

    async def _use_fallback_video(self, output_path: Path):
        """Use fallback video when test video is not available"""
        fallback_path = Path("static/videos/fallback.mp4")
        if fallback_path.exists():
            async with aiofiles.open(fallback_path, "rb") as src:
                content = await src.read()
            async with aiofiles.open(output_path, "wb") as dst:
                await dst.write(content)
            logger.info("Using fallback video")
        else:
            raise VideoGenerationError("No test video or fallback video available")


# Initialize service
video_gen_service = VideoGenerationService()


@text_to_sign_router.post(
    "/generate",
    response_model=TextToSignResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload test video for text input (Testing Mode)",
    description="For testing: Upload existing video file to cloud storage without actual generation",
)
async def generate_video_from_text(
    request: TextToSignRequest,
    background_tasks: BackgroundTasks,
    token_data: dict = Depends(AccessTokenBearer()),
    session: AsyncSession = Depends(get_session),
):
    """
    Testing endpoint: Upload existing video instead of generating new one
    """
    user_id = token_data["user"]["user_id"]
    start_time = datetime.now()

    logger.info(
        f"Processing test upload for user {user_id}, text: '{request.text[:50]}...'"
    )

    # Rate limiting with semaphore
    async with generation_semaphore:
        try:
            # Prepare test video with timeout
            video_path = await asyncio.wait_for(
                video_gen_service.prepare_test_video(
                    text=request.text,
                    language_code=request.language_code,
                    user_id=user_id,
                ),
                timeout=Config.VIDEO_GENERATION_TIMEOUT,
            )

            # Generate destination path
            destination_path = await video_gen_service.generate_video_filename(user_id)

            # Upload to storage
            video_url = await video_gen_service.upload_to_storage(
                video_path, destination_path
            )

            # Clean up local temp file
            if video_path.exists():
                video_path.unlink(missing_ok=True)
                logger.info(f"Cleaned up temp file: {video_path}")

            # Calculate upload time
            upload_time = int((datetime.now() - start_time).total_seconds() * 1000)

            # Log to database in background
            background_tasks.add_task(
                log_translation_history,
                user_id=user_id,
                input_text=request.text,
                video_url=video_url,
                language_code=request.language_code,
                # session_factory=lambda: AsyncSession(session.bind)
                # session_factory=lambda: AsyncSession(async_engine)
            )

            logger.info(
                f"Test video uploaded successfully for user {user_id}, URL: {video_url}"
            )

            return TextToSignResponse(
                video_url=video_url,
                message="Test video uploaded successfully",
                generation_time_ms=upload_time,
            )

        except asyncio.TimeoutError:
            raise HTTPException(
                status_code=status.HTTP_408_REQUEST_TIMEOUT,
                detail="Video upload timed out. Please try again.",
            )
        except (VideoGenerationError, StorageError) as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
            )
        except Exception as e:
            logger.error(
                f"Unexpected error in video upload for user {user_id}: {str(e)}"
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An unexpected error occurred during video upload",
            )


async def log_translation_history(
    user_id: str,
    input_text: str,
    video_url: str,
    language_code: str,
    # session_factory
):
    """Log translation to database history with improved error handling"""
    try:
        async with AsyncSession(async_engine) as session:
            history_entry = TranslationHistory(
                user_id=user_id,
                input_type="text_to_sign",
                input_content=f"{language_code}:{input_text}",
                output_content=video_url,
                timestamp=datetime.now(),
            )

            session.add(history_entry)
            await session.commit()
            logger.info(f"Translation history logged for user {user_id}")

    except Exception as e:
        logger.error(f"Failed to log translation history for user {user_id}: {str(e)}")


@text_to_sign_router.get(
    "/history",
    response_model=List[TranslationHistoryResponse],
    summary="Get user translation history",
    description="Retrieve user's text-to-sign translation history with pagination",
)
async def get_user_translation_history(
    token_data: dict = Depends(AccessTokenBearer()),
    limit: int = Query(
        default=Config.DEFAULT_HISTORY_LIMIT,
        ge=1,
        le=Config.MAX_HISTORY_LIMIT,
        description="Number of records to return",
    ),
    offset: int = Query(default=0, ge=0, description="Number of records to skip"),
    session: AsyncSession = Depends(get_session),
):
    """Get user's text-to-sign translation history with enhanced querying"""
    user_id = token_data["user"]["user_id"]

    try:
        # Optimized query with proper indexing assumptions
        statement = (
            select(TranslationHistory)
            .where(
                TranslationHistory.user_id == user_id,
                TranslationHistory.input_type == "text_to_sign",
            )
            .order_by(TranslationHistory.timestamp.desc())
            .offset(offset)
            .limit(limit)
        )

        result = await session.exec(statement)
        history = result.all()

        # Transform to response model
        response_history = []
        for record in history:
            # Extract language code from input_content
            parts = record.input_content.split(":", 1)
            language_code = parts[0] if len(parts) > 1 else "unknown"

            response_history.append(
                TranslationHistoryResponse(
                    id=record.id,
                    input_content=parts[1] if len(parts) > 1 else record.input_content,
                    output_content=record.output_content,
                    timestamp=record.timestamp,
                    language_code=language_code,
                )
            )

        return response_history

    except Exception as e:
        logger.error(f"Failed to get history for user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve translation history",
        )


@text_to_sign_router.delete(
    "/cleanup",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Clean up old videos",
    description="Remove user's old videos from storage to free up space",
)
async def cleanup_user_videos(
    background_tasks: BackgroundTasks,
    token_data: dict = Depends(AccessTokenBearer()),
    days_old: int = Query(
        default=30, ge=1, le=365, description="Delete videos older than this many days"
    ),
):
    """Clean up user's old videos from storage with improved batch processing"""
    user_id = token_data["user"]["user_id"]

    try:
        background_tasks.add_task(
            cleanup_storage_videos, user_id=user_id, days_old=days_old
        )

        logger.info(f"Cleanup task scheduled for user {user_id}, days_old={days_old}")

    except Exception as e:
        logger.error(f"Failed to schedule cleanup for user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to schedule cleanup task",
        )


async def cleanup_storage_videos(user_id: str, days_old: int):
    """Background task to clean up old videos with batch processing"""
    try:
        await storage_service.cleanup_old_videos(
            user_prefix=f"user_{user_id}",
            days_old=days_old,
            batch_size=Config.CLEANUP_BATCH_SIZE,
        )
        logger.info(f"Cleanup completed for user {user_id}")

    except Exception as e:
        logger.error(f"Failed to cleanup videos for user {user_id}: {str(e)}")


@text_to_sign_router.get(
    "/health",
    summary="Health check endpoint",
    description="Check the health of the text-to-sign service",
)
async def health_check():
    """Health check endpoint for monitoring"""
    try:
        # Basic health checks
        health_status = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0-testing",
            "mode": "testing_with_existing_video",
            "services": {
                "storage": await storage_service.health_check(),
                "temp_directory": Config.TEMP_VIDEO_DIR.exists(),
                "test_video_available": Config.TEST_VIDEO_PATH.exists(),
            },
        }

        # Check if any service is unhealthy
        if not all(health_status["services"].values()):
            health_status["status"] = "degraded"
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE, content=health_status
            )

        return health_status

    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            },
        )


# Additional endpoint for testing purposes
@text_to_sign_router.get(
    "/test-config",
    summary="Get testing configuration",
    description="Get current testing configuration and video availability",
)
async def get_test_config():
    """Get testing configuration information"""
    return {
        "test_video_path": str(Config.TEST_VIDEO_PATH),
        "test_video_exists": Config.TEST_VIDEO_PATH.exists(),
        "temp_directory": str(Config.TEMP_VIDEO_DIR),
        "temp_directory_exists": Config.TEMP_VIDEO_DIR.exists(),
        "supported_languages": list(Config.SUPPORTED_LANGUAGES),
        "max_text_length": Config.MAX_TEXT_LENGTH,
        "mode": "testing_mode",
    }
