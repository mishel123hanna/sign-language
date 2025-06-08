# from fastapi import APIRouter
# from ai_models.text_to_sign.generate_video_from_text import generate_sign_language_video
# from fastapi.responses import FileResponse

# text_to_sign_router = APIRouter()


# @text_to_sign_router.post("/generate-video/")
# async def generate_video_from_text(text: str):
#     video_path = await generate_sign_language_video(text)
#     return FileResponse(
#         video_path, media_type="video/mp4", filename="sign_translation.mp4"
#     )

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.responses import FileResponse
from sqlmodel import Session, select, SQLModel, Field
from sqlmodel.ext.asyncio.session import AsyncSession
from typing import Optional, List
from pathlib import Path
import uuid
import asyncio
import os
from datetime import datetime

from app.auth.dependencies import AccessTokenBearer
from app.db.config import get_session
from app.db.models import TranslationHistory, User, SignGesture, SignTranslation

text_to_sign_router = APIRouter()


class TextToSignRequest(SQLModel):
    """Request model for text to sign translation"""

    text: str
    language_code: Optional[str] = Field(default="ar")


class TextToSignResponse(SQLModel):
    """Response model for text to sign translation"""

    video_filename: str
    video_url: str
    translation_id: Optional[int] = None
    message: str


@text_to_sign_router.post("/generate-video/", response_model=TextToSignResponse)
async def generate_video_from_text(
    request: TextToSignRequest,
    background_tasks: BackgroundTasks,
    token_data: dict = Depends(AccessTokenBearer()),
    session: AsyncSession = Depends(get_session),
):
    """
    Generate sign language video from text input
    """
    try:
        # Validate input
        if not request.text.strip():
            raise HTTPException(status_code=400, detail="Text input cannot be empty")

        if len(request.text) > 1000:  # Reasonable limit
            raise HTTPException(
                status_code=400, detail="Text input too long (max 1000 characters)"
            )

        # Generate video
        video_info = await generate_sign_language_video(
            text=request.text, language_code=request.language_code
        )

        # Log to database in background if user provided
        if token_data["user"]["user_id"]:
        # if request.user_id:
            background_tasks.add_task(
                log_translation_history,
                user_id=token_data['user']["user_id"],
                input_text=request.text,
                output_video=video_info["filename"],
                language_code=request.language_code,
            )

        return TextToSignResponse(
            video_filename=video_info["filename"],
            video_url=f"/static/videos/{video_info['filename']}",
            message="Video generated successfully",
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to generate video: {str(e)}"
        )


@text_to_sign_router.get("/download-video/{filename}")
async def download_video(filename: str):
    """
    Download generated sign language video
    """
    try:
        video_path = Path("static/videos") / filename

        if not video_path.exists():
            raise HTTPException(status_code=404, detail="Video file not found")

        # Security check: ensure filename doesn't contain path traversal
        if ".." in filename or "/" in filename or "\\" in filename:
            raise HTTPException(status_code=400, detail="Invalid filename")

        return FileResponse(
            path=str(video_path),
            media_type="video/mp4",
            filename=f"sign_translation_{filename}",
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to download video: {str(e)}"
        )


@text_to_sign_router.get("/user-history/")
async def get_user_translation_history(
    token_data: dict=Depends(AccessTokenBearer()),
    limit: int = 20,
    offset: int = 0,
    session: AsyncSession = Depends(get_session),
):
    """
    Get user's text-to-sign translation history
    """
    user_id = token_data["user"]["user_id"]

    try:
        # Verify user exists
        user = await session.get(User, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Get translation history
        statement = (
            select(TranslationHistory)
            .where(
                TranslationHistory.user_id == user_id,
                # TranslationHistory.input_type == "text_to_sign",
            )
            .order_by(TranslationHistory.timestamp.desc())
            .offset(offset)
            .limit(limit)
        )

        result = await session.exec(statement)
        history = result.all()

        return {
            "user_id": user_id,
            "username": user.username,
            "history": history,
            "total_count": len(history),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get history: {str(e)}")


# @text_to_sign_router.delete("/cleanup-old-videos/")
# async def cleanup_old_videos(
#     days_old: int = 7,
#     background_tasks: BackgroundTasks):
#     """
#     Clean up old generated videos (admin endpoint)
#     """
#     background_tasks.add_task(cleanup_videos_older_than, days_old)
#     return {"message": f"Started cleanup of videos older than {days_old} days"}


async def generate_sign_language_video(text: str, language_code: str = "ar") -> dict:
    """
    Generate sign language video from text
    """
    try:
        # Create unique filename
        output_filename = f"{uuid.uuid4()}.mp4"
        video_output_path = Path("static/videos") / output_filename

        # Ensure directory exists
        video_output_path.parent.mkdir(parents=True, exist_ok=True)

        # TODO: Replace with actual sign language generation
        # For now, check if we have specific signs for the input text
        generated_video = await generate_from_known_signs(text, language_code)

        if generated_video:
            # Copy/move the generated video to output path
            video_output_path.write_bytes(generated_video)
        else:
            # Fallback to sample video
            sample_video = Path("static/videos/test.mp4")
            if sample_video.exists():
                video_output_path.write_bytes(sample_video.read_bytes())
            else:
                raise Exception("No sample video available and no signs found")

        return {
            "filename": output_filename,
            "path": str(video_output_path),
            "size": video_output_path.stat().st_size,
        }

    except Exception as e:
        raise Exception(f"Video generation failed: {str(e)}")


async def generate_from_known_signs(text: str, language_code: str) -> Optional[bytes]:
    """
    Generate video from known sign gestures in database
    """
    try:
        # This is a placeholder for actual sign language generation
        # In a real implementation, you would:
        # 1. Parse the text into words/phrases
        # 2. Look up corresponding signs in the database
        # 3. Combine sign videos into a single output video
        # 4. Handle missing signs appropriately

        words = text.lower().strip().split()

        # Simulate async processing
        await asyncio.sleep(0.1)

        # TODO: Implement actual video generation logic
        # For now, return None to use fallback
        return None

    except Exception as e:
        print(f"Error in generate_from_known_signs: {e}")
        return None


async def log_translation_history(
    user_id: int, input_text: str, output_video: str, language_code: str
):
    """
    Log translation to database history (background task)
    """
    try:
        # Import here to avoid circular imports
        from app.db.config import async_engine
        from sqlmodel.ext.asyncio.session import AsyncSession

        async with AsyncSession(async_engine) as session:
            # Verify user exists
            user = await session.get(User, user_id)
            if not user:
                print(f"❌ User {user_id} not found for history logging")
                return

            # Create history entry
            history_entry = TranslationHistory(
                user_id=user_id,
                input_type="text_to_sign",
                input_content=f"{language_code}:{input_text}",  # Include language code
                output_content=output_video,
                timestamp=datetime.now(),
            )

            session.add(history_entry)
            await session.commit()
            await session.refresh(history_entry)

            print(
                f"✅ Text-to-sign history logged: ID {history_entry.id} for user {user_id}"
            )

    except Exception as e:
        print(f"❌ Failed to log translation history: {e}")


async def cleanup_videos_older_than(days: int):
    """
    Clean up old video files (background task)
    """
    try:
        videos_dir = Path("static/videos")
        if not videos_dir.exists():
            return

        cutoff_time = datetime.now().timestamp() - (days * 24 * 60 * 60)
        cleaned_count = 0

        for video_file in videos_dir.glob("*.mp4"):
            # Skip the test video
            if video_file.name == "test.mp4":
                continue

            if video_file.stat().st_mtime < cutoff_time:
                try:
                    video_file.unlink()
                    cleaned_count += 1
                except Exception as e:
                    print(f"Failed to delete {video_file}: {e}")

        print(f"✅ Cleaned {cleaned_count} old video files")

    except Exception as e:
        print(f"❌ Video cleanup failed: {e}")


# Helper endpoints for development/testing
@text_to_sign_router.get("/available-signs/")
async def get_available_signs(
    language_code: str = "ar", session: AsyncSession = Depends(get_session)
):
    """
    Get list of available sign gestures
    """
    try:
        statement = (
            select(SignGesture)
            .join(SignTranslation)
            .where(SignTranslation.language_code == language_code)
        )
        result = await session.exec(statement)
        signs = result.all()

        return {
            "language_code": language_code,
            "available_signs": [
                {"id": sign.id, "name": sign.name, "description": sign.description}
                for sign in signs
            ],
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get signs: {str(e)}")
