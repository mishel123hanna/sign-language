# from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
# from fastapi.responses import FileResponse
# from sqlmodel import Session, select, SQLModel, Field
# from sqlmodel.ext.asyncio.session import AsyncSession
# from typing import Optional, List
# from pathlib import Path
# import uuid
# import asyncio
# import os
# from datetime import datetime

# from app.auth.dependencies import AccessTokenBearer
# from app.db.config import get_session
# from app.db.models import TranslationHistory, User, SignGesture, SignTranslation

# text_to_sign_router = APIRouter()


# class TextToSignRequest(SQLModel):
#     """Request model for text to sign translation"""

#     text: str
#     language_code: Optional[str] = Field(default="ar")


# class TextToSignResponse(SQLModel):
#     """Response model for text to sign translation"""

#     video_filename: str
#     video_url: str
#     translation_id: Optional[int] = None
#     message: str


# @text_to_sign_router.post("/generate-video/", response_model=TextToSignResponse)
# async def generate_video_from_text(
#     request: TextToSignRequest,
#     background_tasks: BackgroundTasks,
#     token_data: dict = Depends(AccessTokenBearer()),
#     session: AsyncSession = Depends(get_session),
# ):
#     """
#     Generate sign language video from text input
#     """
#     try:
#         # Validate input
#         if not request.text.strip():
#             raise HTTPException(status_code=400, detail="Text input cannot be empty")

#         if len(request.text) > 1000:  # Reasonable limit
#             raise HTTPException(
#                 status_code=400, detail="Text input too long (max 1000 characters)"
#             )

#         # Generate video
#         video_info = await generate_sign_language_video(
#             text=request.text, language_code=request.language_code
#         )

#         # Log to database in background if user provided
#         if token_data["user"]["user_id"]:
#         # if request.user_id:
#             background_tasks.add_task(
#                 log_translation_history,
#                 user_id=token_data['user']["user_id"],
#                 input_text=request.text,
#                 output_video=video_info["filename"],
#                 language_code=request.language_code,
#             )

#         return TextToSignResponse(
#             video_filename=video_info["filename"],
#             video_url=f"/static/videos/{video_info['filename']}",
#             message="Video generated successfully",
#         )

#     except Exception as e:
#         raise HTTPException(
#             status_code=500, detail=f"Failed to generate video: {str(e)}"
#         )


# @text_to_sign_router.get("/download-video/{filename}")
# async def download_video(filename: str):
#     """
#     Download generated sign language video
#     """
#     try:
#         video_path = Path("static/videos") / filename

#         if not video_path.exists():
#             raise HTTPException(status_code=404, detail="Video file not found")

#         # Security check: ensure filename doesn't contain path traversal
#         if ".." in filename or "/" in filename or "\\" in filename:
#             raise HTTPException(status_code=400, detail="Invalid filename")

#         return FileResponse(
#             path=str(video_path),
#             media_type="video/mp4",
#             filename=f"sign_translation_{filename}",
#         )

#     except Exception as e:
#         raise HTTPException(
#             status_code=500, detail=f"Failed to download video: {str(e)}"
#         )


# @text_to_sign_router.get("/user-history/")
# async def get_user_translation_history(
#     token_data: dict=Depends(AccessTokenBearer()),
#     limit: int = 20,
#     offset: int = 0,
#     session: AsyncSession = Depends(get_session),
# ):
#     """
#     Get user's text-to-sign translation history
#     """
#     user_id = token_data["user"]["user_id"]

#     try:
#         # Verify user exists
#         user = await session.get(User, user_id)
#         if not user:
#             raise HTTPException(status_code=404, detail="User not found")

#         # Get translation history
#         statement = (
#             select(TranslationHistory)
#             .where(
#                 TranslationHistory.user_id == user_id,
#                 # TranslationHistory.input_type == "text_to_sign",
#             )
#             .order_by(TranslationHistory.timestamp.desc())
#             .offset(offset)
#             .limit(limit)
#         )

#         result = await session.exec(statement)
#         history = result.all()

#         return {
#             "user_id": user_id,
#             "username": user.username,
#             "history": history,
#             "total_count": len(history),
#         }

#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Failed to get history: {str(e)}")


# # @text_to_sign_router.delete("/cleanup-old-videos/")
# # async def cleanup_old_videos(
# #     days_old: int = 7,
# #     background_tasks: BackgroundTasks):
# #     """
# #     Clean up old generated videos (admin endpoint)
# #     """
# #     background_tasks.add_task(cleanup_videos_older_than, days_old)
# #     return {"message": f"Started cleanup of videos older than {days_old} days"}


# async def generate_sign_language_video(text: str, language_code: str = "ar") -> dict:
#     """
#     Generate sign language video from text
#     """
#     try:
#         # Create unique filename
#         output_filename = f"{uuid.uuid4()}.mp4"
#         video_output_path = Path("static/videos") / output_filename

#         # Ensure directory exists
#         video_output_path.parent.mkdir(parents=True, exist_ok=True)

#         # TODO: Replace with actual sign language generation
#         # For now, check if we have specific signs for the input text
#         generated_video = await generate_from_known_signs(text, language_code)

#         if generated_video:
#             # Copy/move the generated video to output path
#             video_output_path.write_bytes(generated_video)
#         else:
#             # Fallback to sample video
#             sample_video = Path("static/videos/test.mp4")
#             if sample_video.exists():
#                 video_output_path.write_bytes(sample_video.read_bytes())
#             else:
#                 raise Exception("No sample video available and no signs found")

#         return {
#             "filename": output_filename,
#             "path": str(video_output_path),
#             "size": video_output_path.stat().st_size,
#         }

#     except Exception as e:
#         raise Exception(f"Video generation failed: {str(e)}")


# async def generate_from_known_signs(text: str, language_code: str) -> Optional[bytes]:
#     """
#     Generate video from known sign gestures in database
#     """
#     try:
#         # This is a placeholder for actual sign language generation
#         # In a real implementation, you would:
#         # 1. Parse the text into words/phrases
#         # 2. Look up corresponding signs in the database
#         # 3. Combine sign videos into a single output video
#         # 4. Handle missing signs appropriately

#         words = text.lower().strip().split()

#         # Simulate async processing
#         await asyncio.sleep(0.1)

#         # TODO: Implement actual video generation logic
#         # For now, return None to use fallback
#         return None

#     except Exception as e:
#         print(f"Error in generate_from_known_signs: {e}")
#         return None


# async def log_translation_history(
#     user_id: int, input_text: str, output_video: str, language_code: str
# ):
#     """
#     Log translation to database history (background task)
#     """
#     try:
#         # Import here to avoid circular imports
#         from app.db.config import async_engine
#         from sqlmodel.ext.asyncio.session import AsyncSession

#         async with AsyncSession(async_engine) as session:
#             # Verify user exists
#             user = await session.get(User, user_id)
#             if not user:
#                 print(f"❌ User {user_id} not found for history logging")
#                 return

#             # Create history entry
#             history_entry = TranslationHistory(
#                 user_id=user_id,
#                 input_type="text_to_sign",
#                 input_content=f"{language_code}:{input_text}",  # Include language code
#                 output_content=output_video,
#                 timestamp=datetime.now(),
#             )

#             session.add(history_entry)
#             await session.commit()
#             await session.refresh(history_entry)

#             print(
#                 f"✅ Text-to-sign history logged: ID {history_entry.id} for user {user_id}"
#             )

#     except Exception as e:
#         print(f"❌ Failed to log translation history: {e}")


# async def cleanup_videos_older_than(days: int):
#     """
#     Clean up old video files (background task)
#     """
#     try:
#         videos_dir = Path("static/videos")
#         if not videos_dir.exists():
#             return

#         cutoff_time = datetime.now().timestamp() - (days * 24 * 60 * 60)
#         cleaned_count = 0

#         for video_file in videos_dir.glob("*.mp4"):
#             # Skip the test video
#             if video_file.name == "test.mp4":
#                 continue

#             if video_file.stat().st_mtime < cutoff_time:
#                 try:
#                     video_file.unlink()
#                     cleaned_count += 1
#                 except Exception as e:
#                     print(f"Failed to delete {video_file}: {e}")

#         print(f"✅ Cleaned {cleaned_count} old video files")

#     except Exception as e:
#         print(f"❌ Video cleanup failed: {e}")


# # Helper endpoints for development/testing
# @text_to_sign_router.get("/available-signs/")
# async def get_available_signs(
#     language_code: str = "ar", session: AsyncSession = Depends(get_session)
# ):
#     """
#     Get list of available sign gestures
#     """
#     try:
#         statement = (
#             select(SignGesture)
#             .join(SignTranslation)
#             .where(SignTranslation.language_code == language_code)
#         )
#         result = await session.exec(statement)
#         signs = result.all()

#         return {
#             "language_code": language_code,
#             "available_signs": [
#                 {"id": sign.id, "name": sign.name, "description": sign.description}
#                 for sign in signs
#             ],
#         }

#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Failed to get signs: {str(e)}")

"""---------------------------------------------------------"""
# Supabase storage

# import os
# from pathlib import Path
# from typing import Optional
# import uuid
# import asyncio
# from datetime import datetime, timedelta

# from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, status
# from fastapi.responses import JSONResponse
# from sqlmodel import select, SQLModel, Field
# from sqlmodel.ext.asyncio.session import AsyncSession
# from supabase import create_client, Client
# from dotenv import load_dotenv

# from app.auth.dependencies import AccessTokenBearer
# from app.db.config import get_session
# from app.db.models import TranslationHistory, User, SignGesture, SignTranslation

# # Load environment variables
# load_dotenv()

# # Initialize Supabase client
# supabase_url = os.getenv("SUPABASE_PROJECT_URL")
# supabase_key = os.getenv("SUPABASE_API_KEY")
# supabase: Client = create_client(supabase_url, supabase_key)

# # Constants
# MAX_TEXT_LENGTH = 1000
# VIDEO_BUCKET = "signs-generated-by-ai"
# TEMP_VIDEO_DIR = "static/temp_videos"
# SUPPORTED_LANGUAGES = ["ar", "en"]  # Add more as needed

# text_to_sign_router = APIRouter(prefix="/text-to-sign", tags=["Text to Sign"])


# class TextToSignRequest(SQLModel):
#     """Request model for text to sign translation"""
#     text: str = Field(..., min_length=1, max_length=MAX_TEXT_LENGTH)
#     language_code: str = Field(default="ar", regex="|".join(SUPPORTED_LANGUAGES))


# class TextToSignResponse(SQLModel):
#     """Response model for text to sign translation"""
#     video_url: str
#     translation_id: Optional[int] = None
#     message: str = "Video generated successfully"


# async def upload_to_supabase_storage(file_path: Path, destination_path: str) -> str:
#     """Upload file to Supabase Storage and return public URL"""
#     try:
#         # Read file content
#         file_content = file_path.read_bytes()

#         # Correct way to upload to Supabase Storage
#         res = supabase.storage.from_(VIDEO_BUCKET).upload(
#             path=destination_path,
#             file=file_content,
#             file_options={"content-type": "video/mp4"}
#         )

#         # Check if upload was successful
#         if "error" in res:
#             raise Exception(res["error"])

#         # Get public URL
#         return supabase.storage.from_(VIDEO_BUCKET).get_public_url(destination_path)

#     except Exception as e:
#         raise HTTPException(
#             status_code=500,
#             detail=f"Failed to upload video: {str(e)}"
#         )


# async def generate_video_filename(user_id: str) -> str:
#     """Generate a unique video filename with user context"""
#     timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
#     return f"user_{user_id}/{timestamp}_{uuid.uuid4().hex[:8]}.mp4"


# @text_to_sign_router.post("/generate", response_model=TextToSignResponse)
# async def generate_video_from_text(
#     request: TextToSignRequest,
#     background_tasks: BackgroundTasks,
#     token_data: dict = Depends(AccessTokenBearer()),
#     session: AsyncSession = Depends(get_session),
# ):
#     """
#     Generate sign language video from text input and store in Supabase Storage
#     """
#     user_id = token_data["user"]["user_id"]

#     try:
#         # Generate video (this would be your AI model)
#         video_path = await generate_sign_language_video(
#             text=request.text,
#             language_code=request.language_code,
#             user_id=user_id
#         )

#         # Generate destination path in Supabase Storage
#         destination_path = await generate_video_filename(user_id)

#         # Upload to Supabase Storage
#         video_url = await upload_to_supabase_storage(video_path, destination_path)

#         # Clean up local file
#         if video_path.exists():
#             video_path.unlink()

#         # Log to database in background
#         background_tasks.add_task(
#             log_translation_history,
#             user_id=user_id,
#             input_text=request.text,
#             video_url=video_url,
#             language_code=request.language_code,
#         )

#         return TextToSignResponse(video_url=video_url)

#     except HTTPException:
#         raise
#     except Exception as e:
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Failed to generate video: {str(e)}"
#         )


# async def generate_sign_language_video(
#     text: str,
#     language_code: str,
#     user_id: str
# ) -> Path:
#     """
#     Generate sign language video from text and return local file path
#     """
#     try:
#         # Create temp directory if not exists
#         temp_dir = Path(TEMP_VIDEO_DIR)
#         temp_dir.mkdir(parents=True, exist_ok=True)

#         # Create unique filename
#         output_filename = f"temp_{uuid.uuid4()}.mp4"
#         video_output_path = temp_dir / output_filename

#         # TODO: Replace with actual sign language generation
#         # For now, we'll use a placeholder implementation
#         generated_video = await generate_from_known_signs(text, language_code)

#         if generated_video:
#             video_output_path.write_bytes(generated_video)
#         else:
#             # Fallback to sample video if no signs found
#             sample_video = Path("static/videos/test.mp4")
#             if sample_video.exists():
#                 video_output_path.write_bytes(sample_video.read_bytes())
#             else:
#                 raise Exception("No sample video available and no signs found")

#         return video_output_path

#     except Exception as e:
#         # Clean up if something went wrong
#         if video_output_path.exists():
#             video_output_path.unlink()
#         raise Exception(f"Video generation failed: {str(e)}")


# async def log_translation_history(
#     user_id: str,
#     input_text: str,
#     video_url: str,
#     language_code: str
# ):
#     """
#     Log translation to database history (background task)
#     """
#     try:
#         from app.db.config import async_engine

#         async with AsyncSession(async_engine) as session:
#             # Create history entry
#             history_entry = TranslationHistory(
#                 user_id=user_id,
#                 input_type="text_to_sign",
#                 input_content=f"{language_code}:{input_text}",
#                 output_content=video_url,  # Now storing Supabase URL
#                 timestamp=datetime.now(),
#             )

#             session.add(history_entry)
#             await session.commit()

#     except Exception as e:
#         # In production, you might want to log this to a monitoring system
#         print(f"Failed to log translation history: {e}")


# @text_to_sign_router.get("/history", response_model=list[TranslationHistory])
# async def get_user_translation_history(
#     token_data: dict = Depends(AccessTokenBearer()),
#     limit: int = 20,
#     offset: int = 0,
#     session: AsyncSession = Depends(get_session),
# ):
#     """
#     Get user's text-to-sign translation history with Supabase URLs
#     """
#     user_id = token_data["user"]["user_id"]

#     try:
#         statement = (
#             select(TranslationHistory)
#             .where(TranslationHistory.user_id == user_id)
#             .order_by(TranslationHistory.timestamp.desc())
#             .offset(offset)
#             .limit(limit)
#         )

#         result = await session.exec(statement)
#         history = result.all()

#         return history

#     except Exception as e:
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Failed to get history: {str(e)}"
#         )


# @text_to_sign_router.delete("/cleanup", status_code=status.HTTP_204_NO_CONTENT)
# async def cleanup_user_videos(
#     background_tasks: BackgroundTasks,
#     token_data: dict = Depends(AccessTokenBearer()),
#     days_old: int = 30
# ):
#     """
#     Clean up user's old videos from Supabase Storage
#     """
#     user_id = token_data["user"]["user_id"]

#     try:
#         # This would be more efficient with a proper job queue in production
#         background_tasks.add_task(
#             cleanup_supabase_videos,
#             user_id=user_id,
#             days_old=days_old
#         )

#     except Exception as e:
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Failed to initiate cleanup: {str(e)}"
#         )


# async def cleanup_supabase_videos(user_id: str, days_old: int):
#     """
#     Background task to clean up old videos from Supabase Storage
#     """
#     try:
#         # List all files for this user
#         files = supabase.storage().from_(VIDEO_BUCKET).list(f"user_{user_id}")

#         cutoff = datetime.now() - timedelta(days=days_old)

#         for file in files:
#             file_date = datetime.strptime(file['name'].split('_')[1], "%Y%m%d")
#             if file_date < cutoff:
#                 supabase.storage().from_(VIDEO_BUCKET).remove([file['name']])

#     except Exception as e:
#         # Log the error properly in production
#         print(f"Failed to cleanup videos for user {user_id}: {e}")


# async def generate_from_known_signs(text: str, language_code: str) -> Optional[bytes]:
#     """
#     Generate video from known sign gestures in database
#     """
#     try:
#         # This is a placeholder for actual sign language generation
#         # In a real implementation, you would:
#         # 1. Parse the text into words/phrases
#         # 2. Look up corresponding signs in the database
#         # 3. Combine sign videos into a single output video
#         # 4. Handle missing signs appropriately

#         words = text.lower().strip().split()

#         # Simulate async processing
#         await asyncio.sleep(0.1)

#         # TODO: Implement actual video generation logic
#         # For now, return None to use fallback
#         return None

#     except Exception as e:
#         print(f"Error in generate_from_known_signs: {e}")
#         return None

# """----------------------------------------------------------"""
# with cloud ai

# import os
# import asyncio
# import logging
# from pathlib import Path
# from typing import Optional, List
# from datetime import datetime, timedelta
# from contextlib import asynccontextmanager
# import uuid
# from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, status
# from fastapi.responses import JSONResponse
# from sqlmodel import select, SQLModel, Field
# from sqlmodel.ext.asyncio.session import AsyncSession
# from supabase import create_client, Client
# from pydantic import field_validator, Field as PydanticField
# import aiofiles
# from tenacity import retry, stop_after_attempt, wait_exponential
# from fastapi import Query
# from app.auth.dependencies import AccessTokenBearer
# from app.db.config import get_session
# from app.db.models import TranslationHistory, User, SignGesture, SignTranslation
# from app.core.settings import settings
# from app.utils.exceptions import VideoGenerationError, StorageError
# from app.utils.video_service import VideoService
# from app.utils.storage_service import StorageService

# # Configure logging
# logger = logging.getLogger(__name__)

# # Constants
# class Config:
#     MAX_TEXT_LENGTH = 1000
#     VIDEO_BUCKET = "signs-generated-by-ai"
#     TEMP_VIDEO_DIR = Path("static/temp_videos")
#     SUPPORTED_LANGUAGES = {"ar", "en"}
#     MAX_CONCURRENT_GENERATIONS = 10
#     VIDEO_GENERATION_TIMEOUT = 300  # 5 minutes
#     CLEANUP_BATCH_SIZE = 100
#     DEFAULT_HISTORY_LIMIT = 20
#     MAX_HISTORY_LIMIT = 100

# # Initialize services
# storage_service = StorageService()
# video_service = VideoService()

# # Semaphore for concurrent video generation
# generation_semaphore = asyncio.Semaphore(Config.MAX_CONCURRENT_GENERATIONS)

# text_to_sign_router = APIRouter(
#     prefix="/text-to-sign",
#     tags=["Text to Sign"],
#     responses={
#         500: {"description": "Internal server error"},
#         422: {"description": "Validation error"},
#         429: {"description": "Too many requests"}
#     }
# )


# class TextToSignRequest(SQLModel):
#     """Request model for text to sign translation with enhanced validation"""
#     text: str = Field(
#         ...,
#         min_length=1,
#         max_length=Config.MAX_TEXT_LENGTH,
#         description="Text to convert to sign language"
#     )
#     language_code: str = Field(
#         default="ar",
#         description="Language code for the text"
#     )

#     @field_validator('language_code')
#     def validate_language_code(cls, v):
#         if v not in Config.SUPPORTED_LANGUAGES:
#             raise ValueError(f"Language code must be one of: {', '.join(Config.SUPPORTED_LANGUAGES)}")
#         return v

#     @field_validator('text')
#     def validate_text(cls, v):
#         # Remove excessive whitespace and validate content
#         cleaned_text = ' '.join(v.strip().split())
#         if not cleaned_text:
#             raise ValueError("Text cannot be empty or only whitespace")
#         return cleaned_text


# class TextToSignResponse(SQLModel):
#     """Response model for text to sign translation"""
#     video_url: str = Field(..., description="URL of the generated sign language video")
#     translation_id: Optional[int] = Field(None, description="Database ID of the translation")
#     message: str = Field(default="Video generated successfully")
#     generation_time_ms: Optional[int] = Field(None, description="Time taken to generate video in milliseconds")


# class TranslationHistoryResponse(SQLModel):
#     """Response model for translation history"""
#     id: int
#     input_content: str
#     output_content: str
#     timestamp: datetime
#     language_code: str


# class VideoGenerationService:
#     """Service class for video generation operations"""

#     def __init__(self):
#         self.temp_dir = Config.TEMP_VIDEO_DIR
#         self.temp_dir.mkdir(parents=True, exist_ok=True)

#     async def generate_video_filename(self, user_id: str) -> str:
#         """Generate a unique video filename with user context"""
#         timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
#         import uuid
#         return f"user_{user_id}/{timestamp}_{uuid.uuid4().hex[:8]}.mp4"

#     @retry(
#         stop=stop_after_attempt(3),
#         wait=wait_exponential(multiplier=1, min=4, max=10)
#     )
#     async def upload_to_storage(self, file_path: Path, destination_path: str) -> str:
#         """Upload file to Supabase Storage with retry logic"""
#         try:
#             return await storage_service.upload_video(file_path, destination_path)
#         except Exception as e:
#             logger.error(f"Failed to upload video {destination_path}: {str(e)}")
#             raise StorageError(f"Failed to upload video: {str(e)}")

#     async def generate_sign_language_video(
#         self,
#         text: str,
#         language_code: str,
#         user_id: str
#     ) -> Path:
#         """Generate sign language video from text with improved error handling"""
#         output_path = None
#         try:
#             # Generate unique filename
#             import uuid
#             output_filename = f"temp_{uuid.uuid4()}.mp4"
#             output_path = self.temp_dir / output_filename

#             # Use video service for generation
#             video_content = await video_service.generate_from_text(
#                 text=text,
#                 language_code=language_code,
#                 user_id=user_id
#             )

#             if video_content:
#                 async with aiofiles.open(output_path, 'wb') as f:
#                     await f.write(video_content)
#             else:
#                 # Use fallback video
#                 await self._use_fallback_video(output_path)

#             return output_path

#         except Exception as e:
#             # Clean up on error
#             if output_path and output_path.exists():
#                 output_path.unlink(missing_ok=True)
#             raise VideoGenerationError(f"Video generation failed: {str(e)}")


#     async def _use_fallback_video(self, output_path: Path):
#         """Use fallback video when generation fails"""
#         fallback_path = Path("static/videos/fallback.mp4")
#         if fallback_path.exists():
#             async with aiofiles.open(fallback_path, 'rb') as src:
#                 content = await src.read()
#             async with aiofiles.open(output_path, 'wb') as dst:
#                 await dst.write(content)
#         else:
#             raise VideoGenerationError("No fallback video available")


# # Initialize service
# video_gen_service = VideoGenerationService()


# @text_to_sign_router.post(
#     "/generate",
#     response_model=TextToSignResponse,
#     status_code=status.HTTP_201_CREATED,
#     summary="Generate sign language video from text",
#     description="Convert text input to sign language video and store in cloud storage"
# )
# async def generate_video_from_text(
#     request: TextToSignRequest,
#     background_tasks: BackgroundTasks,
#     token_data: dict = Depends(AccessTokenBearer()),
#     session: AsyncSession = Depends(get_session),
# ):
#     """Generate sign language video from text input with enhanced performance and error handling"""
#     user_id = token_data["user"]["user_id"]
#     start_time = datetime.now()

#     # Rate limiting with semaphore
#     async with generation_semaphore:
#         try:
#             # Generate video with timeout
#             video_path = await asyncio.wait_for(
#                 video_gen_service.generate_sign_language_video(
#                     text=request.text,
#                     language_code=request.language_code,
#                     user_id=user_id
#                 ),
#                 timeout=Config.VIDEO_GENERATION_TIMEOUT
#             )

#             # Generate destination path
#             destination_path = await video_gen_service.generate_video_filename(user_id)

#             # Upload to storage
#             video_url = await video_gen_service.upload_to_storage(video_path, destination_path)

#             # Clean up local file
#             if video_path.exists():
#                 video_path.unlink(missing_ok=True)

#             # Calculate generation time
#             generation_time = int((datetime.now() - start_time).total_seconds() * 1000)

#             # Log to database in background
#             background_tasks.add_task(
#                 log_translation_history,
#                 user_id=user_id,
#                 input_text=request.text,
#                 video_url=video_url,
#                 language_code=request.language_code,
#                 session_factory=lambda: AsyncSession(session.bind)
#             )

#             return TextToSignResponse(
#                 video_url=video_url,
#                 generation_time_ms=generation_time
#             )

#         except asyncio.TimeoutError:
#             raise HTTPException(
#                 status_code=status.HTTP_408_REQUEST_TIMEOUT,
#                 detail="Video generation timed out. Please try again with shorter text."
#             )
#         except (VideoGenerationError, StorageError) as e:
#             raise HTTPException(
#                 status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#                 detail=str(e)
#             )
#         except Exception as e:
#             logger.error(f"Unexpected error in video generation for user {user_id}: {str(e)}")
#             raise HTTPException(
#                 status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#                 detail="An unexpected error occurred during video generation"
#             )


# async def log_translation_history(
#     user_id: str,
#     input_text: str,
#     video_url: str,
#     language_code: str,
#     session_factory
# ):
#     """Log translation to database history with improved error handling"""
#     try:
#         async with session_factory() as session:
#             history_entry = TranslationHistory(
#                 user_id=user_id,
#                 input_type="text_to_sign",
#                 input_content=f"{language_code}:{input_text}",
#                 output_content=video_url,
#                 timestamp=datetime.now(),
#             )

#             session.add(history_entry)
#             await session.commit()
#             logger.info(f"Translation history logged for user {user_id}")

#     except Exception as e:
#         logger.error(f"Failed to log translation history for user {user_id}: {str(e)}")
#         # In production, you might want to send this to a dead letter queue
#         # or retry mechanism


# @text_to_sign_router.get(
#     "/history",
#     response_model=List[TranslationHistoryResponse],
#     summary="Get user translation history",
#     description="Retrieve user's text-to-sign translation history with pagination"
# )
# async def get_user_translation_history(
#     token_data: dict = Depends(AccessTokenBearer()),
#     limit: int = Query(
#         default=Config.DEFAULT_HISTORY_LIMIT,
#         ge=1,
#         le=Config.MAX_HISTORY_LIMIT,
#         description="Number of records to return"
#     ),
#     offset: int = Query(
#         default=0,
#         ge=0,
#         description="Number of records to skip"
#     ),
#     session: AsyncSession = Depends(get_session),
# ):
#     """Get user's text-to-sign translation history with enhanced querying"""
#     user_id = token_data["user"]["user_id"]

#     try:
#         # Optimized query with proper indexing assumptions
#         statement = (
#             select(TranslationHistory)
#             .where(
#                 TranslationHistory.user_id == user_id,
#                 TranslationHistory.input_type == "text_to_sign"
#             )
#             .order_by(TranslationHistory.timestamp.desc())
#             .offset(offset)
#             .limit(limit)
#         )

#         result = await session.exec(statement)
#         history = result.all()

#         # Transform to response model
#         response_history = []
#         for record in history:
#             # Extract language code from input_content
#             parts = record.input_content.split(':', 1)
#             language_code = parts[0] if len(parts) > 1 else "unknown"

#             response_history.append(TranslationHistoryResponse(
#                 id=record.id,
#                 input_content=parts[1] if len(parts) > 1 else record.input_content,
#                 output_content=record.output_content,
#                 timestamp=record.timestamp,
#                 language_code=language_code
#             ))

#         return response_history

#     except Exception as e:
#         logger.error(f"Failed to get history for user {user_id}: {str(e)}")
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail="Failed to retrieve translation history"
#         )


# @text_to_sign_router.delete(
#     "/cleanup",
#     status_code=status.HTTP_204_NO_CONTENT,
#     summary="Clean up old videos",
#     description="Remove user's old videos from storage to free up space"
# )
# async def cleanup_user_videos(
#     background_tasks: BackgroundTasks,
#     token_data: dict = Depends(AccessTokenBearer()),
#     days_old: int = Query(
#         default=30,
#         ge=1,
#         le=365,
#         description="Delete videos older than this many days"
#     )
# ):
#     """Clean up user's old videos from storage with improved batch processing"""
#     user_id = token_data["user"]["user_id"]

#     try:
#         background_tasks.add_task(
#             cleanup_storage_videos,
#             user_id=user_id,
#             days_old=days_old
#         )

#         logger.info(f"Cleanup task scheduled for user {user_id}, days_old={days_old}")

#     except Exception as e:
#         logger.error(f"Failed to schedule cleanup for user {user_id}: {str(e)}")
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail="Failed to schedule cleanup task"
#         )


# async def cleanup_storage_videos(user_id: str, days_old: int):
#     """Background task to clean up old videos with batch processing"""
#     try:
#         await storage_service.cleanup_old_videos(
#             user_prefix=f"user_{user_id}",
#             days_old=days_old,
#             batch_size=Config.CLEANUP_BATCH_SIZE
#         )
#         logger.info(f"Cleanup completed for user {user_id}")

#     except Exception as e:
#         logger.error(f"Failed to cleanup videos for user {user_id}: {str(e)}")
#         # In production, you might want to retry or alert monitoring systems


# @text_to_sign_router.get(
#     "/health",
#     summary="Health check endpoint",
#     description="Check the health of the text-to-sign service"
# )
# async def health_check():
#     """Health check endpoint for monitoring"""
#     try:
#         # Basic health checks
#         health_status = {
#             "status": "healthy",
#             "timestamp": datetime.now().isoformat(),
#             "version": "1.0.0",
#             "services": {
#                 "storage": await storage_service.health_check(),
#                 # "video_generation": await video_service.health_check(),
#                 "temp_directory": Config.TEMP_VIDEO_DIR.exists()
#             }
#         }

#         # Check if any service is unhealthy
#         if not all(health_status["services"].values()):
#             health_status["status"] = "degraded"
#             return JSONResponse(
#                 status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
#                 content=health_status
#             )

#         return health_status

#     except Exception as e:
#         logger.error(f"Health check failed: {str(e)}")
#         return JSONResponse(
#             status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
#             content={
#                 "status": "unhealthy",
#                 "error": str(e),
#                 "timestamp": datetime.now().isoformat()
#             }
#         )

# """-----------------------"""
# testing (upload an exist video)
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
