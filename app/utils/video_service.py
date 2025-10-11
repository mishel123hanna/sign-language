# import os
# import asyncio
# import logging
# import hashlib
# import json
# from pathlib import Path
# from typing import Optional, List, Dict, Any, Tuple
# from datetime import datetime, timedelta
# from dataclasses import dataclass, asdict
# from enum import Enum
# import tempfile
# import subprocess

# import aiofiles
# import aiohttp
# from sqlmodel import select, SQLModel
# from sqlmodel.ext.asyncio.session import AsyncSession
# from tenacity import (
#     retry, 
#     stop_after_attempt, 
#     wait_exponential, 
#     retry_if_exception_type,
#     before_sleep_log
# )
# # import cv2
# # import numpy as np
# from moviepy.editor import VideoFileClip, concatenate_videoclips, ImageClip

# from app.core.settings import settings
# from app.utils.exceptions import VideoGenerationError, AIModelError, CacheError
# from app.db.config import get_session
# from app.db.models import SignGesture, SignTranslation

# logger = logging.getLogger(__name__)


# class VideoQuality(str, Enum):
#     """Video quality options"""
#     LOW = "480p"
#     MEDIUM = "720p"
#     HIGH = "1080p"


# class GenerationStatus(str, Enum):
#     """Video generation status"""
#     PENDING = "pending"
#     PROCESSING = "processing"
#     COMPLETED = "completed"
#     FAILED = "failed"
#     CACHED = "cached"


# @dataclass
# class VideoGenerationRequest:
#     """Video generation request parameters"""
#     text: str
#     language_code: str
#     user_id: str
#     quality: VideoQuality = VideoQuality.MEDIUM
#     include_subtitles: bool = True
#     background_color: str = "#FFFFFF"
#     speed_multiplier: float = 1.0


# @dataclass
# class VideoGenerationResult:
#     """Result of video generation"""
#     success: bool
#     video_content: Optional[bytes] = None
#     video_path: Optional[Path] = None
#     generation_time_ms: int = 0
#     status: GenerationStatus = GenerationStatus.PENDING
#     error_message: Optional[str] = None
#     cache_hit: bool = False
#     metadata: Optional[Dict[str, Any]] = None


# @dataclass
# class SignVideoSegment:
#     """Individual sign video segment"""
#     word: str
#     video_path: Optional[Path]
#     duration_ms: int
#     confidence_score: float = 1.0
#     is_generated: bool = True
#     fallback_used: bool = False


# class AIModelClient:
#     """Client for AI sign language generation models"""
    
#     def __init__(self):
#         self.api_endpoint = settings.AI_MODEL_ENDPOINT
#         self.api_key = settings.AI_MODEL_API_KEY
#         self.model_version = settings.AI_MODEL_VERSION or "v1.0"
#         self.timeout = settings.AI_MODEL_TIMEOUT or 60
        
#         # Model-specific configurations
#         self.supported_languages = {"ar", "en", "fr", "es"}
#         self.max_text_length = 500
#         self.generation_params = {
#             "quality": "high",
#             "fps": 30,
#             "resolution": "1280x720",
#             "format": "mp4"
#         }
    
#     async def generate_sign_video(
#         self, 
#         text: str, 
#         language_code: str,
#         quality: VideoQuality = VideoQuality.MEDIUM
#     ) -> Optional[bytes]:
#         """
#         Generate sign language video using AI model
        
#         Args:
#             text: Text to convert to sign language
#             language_code: Language code for the text
#             quality: Video quality setting
            
#         Returns:
#             Generated video content as bytes
#         """
#         try:
#             if language_code not in self.supported_languages:
#                 raise AIModelError(f"Language {language_code} not supported by AI model")
            
#             if len(text) > self.max_text_length:
#                 raise AIModelError(f"Text length {len(text)} exceeds maximum {self.max_text_length}")
            
#             # Prepare request payload
#             payload = {
#                 "text": text,
#                 "language": language_code,
#                 "quality": quality.value,
#                 "model_version": self.model_version,
#                 **self.generation_params
#             }
            
#             headers = {
#                 "Authorization": f"Bearer {self.api_key}",
#                 "Content-Type": "application/json",
#                 "User-Agent": f"SignLanguageApp/{self.model_version}"
#             }
            
#             # Make API request
#             async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
#                 async with session.post(
#                     self.api_endpoint,
#                     json=payload,
#                     headers=headers
#                 ) as response:
                    
#                     if response.status == 200:
#                         content = await response.read()
#                         logger.info(f"AI model generated video for text: '{text[:50]}...'")
#                         return content
#                     elif response.status == 429:
#                         raise AIModelError("AI model rate limit exceeded")
#                     elif response.status >= 500:
#                         raise AIModelError(f"AI model server error: {response.status}")
#                     else:
#                         error_text = await response.text()
#                         raise AIModelError(f"AI model request failed: {response.status} - {error_text}")
                        
#         except aiohttp.ClientError as e:
#             logger.error(f"AI model client error: {str(e)}")
#             raise AIModelError(f"Failed to connect to AI model: {str(e)}")
#         except Exception as e:
#             logger.error(f"Unexpected error in AI model generation: {str(e)}")
#             raise AIModelError(f"AI model generation failed: {str(e)}")
    
#     async def health_check(self) -> bool:
#         """Check if AI model service is available"""
#         try:
#             health_endpoint = f"{self.api_endpoint.rstrip('/')}/health"
            
#             async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
#                 async with session.get(health_endpoint) as response:
#                     return response.status == 200
                    
#         except Exception as e:
#             logger.error(f"AI model health check failed: {str(e)}")
#             return False


# class VideoCacheManager:
#     """Cache manager for generated videos"""
    
#     def __init__(self):
#         self.cache_dir = Path(settings.VIDEO_CACHE_DIR or "cache/videos")
#         self.cache_dir.mkdir(parents=True, exist_ok=True)
        
#         self.max_cache_size_gb = settings.MAX_CACHE_SIZE_GB or 10
#         self.cache_ttl_hours = settings.CACHE_TTL_HOURS or 24
#         self.cleanup_interval_hours = 6
        
#         # In-memory cache for metadata
#         self._cache_metadata: Dict[str, Dict[str, Any]] = {}
        
#         # Start cleanup task
#         asyncio.create_task(self._periodic_cleanup())
    
#     def _generate_cache_key(self, text: str, language_code: str, quality: VideoQuality) -> str:
#         """Generate cache key for video"""
#         content = f"{text}:{language_code}:{quality.value}"
#         return hashlib.sha256(content.encode()).hexdigest()
    
#     async def get_cached_video(
#         self, 
#         text: str, 
#         language_code: str, 
#         quality: VideoQuality
#     ) -> Optional[bytes]:
#         """Retrieve cached video if available and valid"""
#         try:
#             cache_key = self._generate_cache_key(text, language_code, quality)
#             cache_file = self.cache_dir / f"{cache_key}.mp4"
#             metadata_file = self.cache_dir / f"{cache_key}.json"
            
#             if not cache_file.exists() or not metadata_file.exists():
#                 return None
            
#             # Check if cache is still valid
#             async with aiofiles.open(metadata_file, 'r') as f:
#                 metadata = json.loads(await f.read())
            
#             created_at = datetime.fromisoformat(metadata["created_at"])
#             if datetime.now() - created_at > timedelta(hours=self.cache_ttl_hours):
#                 # Cache expired, clean it up
#                 await self._remove_cache_entry(cache_key)
#                 return None
            
#             # Load cached video
#             async with aiofiles.open(cache_file, 'rb') as f:
#                 video_content = await f.read()
            
#             # Update access time
#             metadata["last_accessed"] = datetime.now().isoformat()
#             metadata["access_count"] = metadata.get("access_count", 0) + 1
            
#             async with aiofiles.open(metadata_file, 'w') as f:
#                 await f.write(json.dumps(metadata, indent=2))
            
#             logger.info(f"Cache hit for key: {cache_key}")
#             return video_content
            
#         except Exception as e:
#             logger.error(f"Error retrieving cached video: {str(e)}")
#             return None
    
#     async def cache_video(
#         self, 
#         text: str, 
#         language_code: str, 
#         quality: VideoQuality,
#         video_content: bytes,
#         generation_metadata: Optional[Dict[str, Any]] = None
#     ) -> bool:
#         """Cache generated video"""
#         try:
#             cache_key = self._generate_cache_key(text, language_code, quality)
#             cache_file = self.cache_dir / f"{cache_key}.mp4"
#             metadata_file = self.cache_dir / f"{cache_key}.json"
            
#             # Check available space
#             if not await self._ensure_cache_space(len(video_content)):
#                 logger.warning("Insufficient cache space, skipping cache")
#                 return False
            
#             # Save video file
#             async with aiofiles.open(cache_file, 'wb') as f:
#                 await f.write(video_content)
            
#             # Save metadata
#             metadata = {
#                 "cache_key": cache_key,
#                 "text": text,
#                 "language_code": language_code,
#                 "quality": quality.value,
#                 "file_size_bytes": len(video_content),
#                 "created_at": datetime.now().isoformat(),
#                 "last_accessed": datetime.now().isoformat(),
#                 "access_count": 1,
#                 "generation_metadata": generation_metadata or {}
#             }
            
#             async with aiofiles.open(metadata_file, 'w') as f:
#                 await f.write(json.dumps(metadata, indent=2))
            
#             logger.info(f"Video cached with key: {cache_key}")
#             return True
            
#         except Exception as e:
#             logger.error(f"Error caching video: {str(e)}")
#             return False
    
#     async def _ensure_cache_space(self, required_bytes: int) -> bool:
#         """Ensure sufficient cache space by cleaning old entries"""
#         try:
#             current_size = await self._get_cache_size()
#             max_size_bytes = self.max_cache_size_gb * 1024 * 1024 * 1024
            
#             if current_size + required_bytes <= max_size_bytes:
#                 return True
            
#             # Clean up old entries to make space
#             await self._cleanup_old_entries(required_bytes)
            
#             # Check again
#             current_size = await self._get_cache_size()
#             return current_size + required_bytes <= max_size_bytes
            
#         except Exception as e:
#             logger.error(f"Error ensuring cache space: {str(e)}")
#             return False
    
#     async def _get_cache_size(self) -> int:
#         """Get current cache size in bytes"""
#         total_size = 0
#         for file_path in self.cache_dir.glob("*.mp4"):
#             if file_path.is_file():
#                 total_size += file_path.stat().st_size
#         return total_size
    
#     async def _cleanup_old_entries(self, space_needed: int = 0):
#         """Clean up old cache entries"""
#         try:
#             # Get all cache entries with metadata
#             entries = []
#             for metadata_file in self.cache_dir.glob("*.json"):
#                 try:
#                     async with aiofiles.open(metadata_file, 'r') as f:
#                         metadata = json.loads(await f.read())
                    
#                     video_file = self.cache_dir / f"{metadata['cache_key']}.mp4"
#                     if video_file.exists():
#                         entries.append({
#                             "cache_key": metadata["cache_key"],
#                             "last_accessed": datetime.fromisoformat(metadata["last_accessed"]),
#                             "file_size": metadata["file_size_bytes"],
#                             "access_count": metadata.get("access_count", 1)
#                         })
#                 except Exception as e:
#                     logger.warning(f"Error reading cache metadata {metadata_file}: {str(e)}")
            
#             # Sort by last accessed time (oldest first)
#             entries.sort(key=lambda x: x["last_accessed"])
            
#             # Remove old entries
#             freed_space = 0
#             for entry in entries:
#                 if space_needed > 0 and freed_space >= space_needed:
#                     break
                
#                 await self._remove_cache_entry(entry["cache_key"])
#                 freed_space += entry["file_size"]
#                 logger.info(f"Removed cache entry: {entry['cache_key']}")
            
#         except Exception as e:
#             logger.error(f"Error during cache cleanup: {str(e)}")
    
#     async def _remove_cache_entry(self, cache_key: str):
#         """Remove a specific cache entry"""
#         try:
#             cache_file = self.cache_dir / f"{cache_key}.mp4"
#             metadata_file = self.cache_dir / f"{cache_key}.json"
            
#             if cache_file.exists():
#                 cache_file.unlink()
#             if metadata_file.exists():
#                 metadata_file.unlink()
                
#         except Exception as e:
#             logger.error(f"Error removing cache entry {cache_key}: {str(e)}")
    
#     async def _periodic_cleanup(self):
#         """Periodic cache cleanup task"""
#         while True:
#             try:
#                 await asyncio.sleep(self.cleanup_interval_hours * 3600)
#                 await self._cleanup_old_entries()
#                 logger.info("Periodic cache cleanup completed")
#             except Exception as e:
#                 logger.error(f"Error in periodic cache cleanup: {str(e)}")


# class VideoService:
#     """
#     Comprehensive video generation service for sign language content
#     """
    
#     def __init__(self):
#         self.ai_client = AIModelClient()
#         self.cache_manager = VideoCacheManager()
        
#         # Configuration
#         self.temp_dir = Path(settings.TEMP_VIDEO_DIR or "temp/videos")
#         self.temp_dir.mkdir(parents=True, exist_ok=True)
        
#         self.fallback_video_dir = Path(settings.FALLBACK_VIDEO_DIR or "static/fallback_videos")
#         self.sign_database_enabled = settings.ENABLE_SIGN_DATABASE or True
        
#         # Video processing settings
#         self.default_fps = 30
#         self.default_resolution = (1280, 720)
#         self.max_video_length_seconds = 300  # 5 minutes
        
#         # Statistics
#         self._generation_stats = {
#             "total_generations": 0,
#             "ai_generations": 0,
#             "database_generations": 0,
#             "fallback_generations": 0,
#             "cache_hits": 0,
#             "average_generation_time_ms": 0
#         }
    
#     async def health_check(self) -> bool:
#         """Check if video service is healthy"""
#         try:
#             # Check AI model availability
#             ai_healthy = await self.ai_client.health_check()
            
#             # Check temp directory
#             temp_dir_accessible = self.temp_dir.exists() and os.access(self.temp_dir, os.W_OK)
            
#             # Check fallback videos
#             fallback_available = self.fallback_video_dir.exists()
            
#             return ai_healthy or fallback_available and temp_dir_accessible
            
#         except Exception as e:
#             logger.error(f"Video service health check failed: {str(e)}")
#             return False
    
#     async def generate_from_text(
#         self, 
#         text: str, 
#         language_code: str,
#         user_id: str,
#         quality: VideoQuality = VideoQuality.MEDIUM,
#         **kwargs
#     ) -> Optional[bytes]:
#         """
#         Main entry point for video generation from text
        
#         Args:
#             text: Text to convert to sign language
#             language_code: Language code for the text
#             user_id: User ID for logging and personalization
#             quality: Video quality setting
#             **kwargs: Additional generation parameters
            
#         Returns:
#             Generated video content as bytes
#         """
#         start_time = datetime.now()
        
#         try:
#             # Create generation request
#             request = VideoGenerationRequest(
#                 text=text,
#                 language_code=language_code,
#                 user_id=user_id,
#                 quality=quality,
#                 **kwargs
#             )
            
#             # Try cache first
#             cached_video = await self.cache_manager.get_cached_video(
#                 text, language_code, quality
#             )
            
#             if cached_video:
#                 self._generation_stats["cache_hits"] += 1
#                 logger.info(f"Returning cached video for user {user_id}")
#                 return cached_video
            
#             # Generate new video
#             result = await self._generate_video(request)
            
#             if result.success and result.video_content:
#                 # Cache the result
#                 await self.cache_manager.cache_video(
#                     text, language_code, quality,
#                     result.video_content,
#                     result.metadata
#                 )
                
#                 # Update statistics
#                 generation_time = (datetime.now() - start_time).total_seconds() * 1000
#                 await self._update_generation_stats(generation_time, result.status)
                
#                 logger.info(f"Video generated for user {user_id} in {generation_time:.2f}ms")
#                 return result.video_content
#             else:
#                 raise VideoGenerationError(result.error_message or "Video generation failed")
                
#         except Exception as e:
#             logger.error(f"Video generation failed for user {user_id}: {str(e)}")
#             raise VideoGenerationError(f"Failed to generate video: {str(e)}")
    
#     async def _generate_video(self, request: VideoGenerationRequest) -> VideoGenerationResult:
#         """Internal video generation logic with multiple fallback strategies"""
#         try:
#             # Strategy 1: Try AI model generation
#             try:
#                 video_content = await self.ai_client.generate_sign_video(
#                     request.text,
#                     request.language_code,
#                     request.quality
#                 )
                
#                 if video_content:
#                     self._generation_stats["ai_generations"] += 1
#                     return VideoGenerationResult(
#                         success=True,
#                         video_content=video_content,
#                         status=GenerationStatus.COMPLETED,
#                         metadata={"generation_method": "ai_model", "quality": request.quality.value}
#                     )
                    
#             except AIModelError as e:
#                 logger.warning(f"AI model generation failed: {str(e)}")
            
#             # Strategy 2: Try database-based generation
#             if self.sign_database_enabled:
#                 try:
#                     video_content = await self._generate_from_database(request)
#                     if video_content:
#                         self._generation_stats["database_generations"] += 1
#                         return VideoGenerationResult(
#                             success=True,
#                             video_content=video_content,
#                             status=GenerationStatus.COMPLETED,
#                             metadata={"generation_method": "database", "quality": request.quality.value}
#                         )
                        
#                 except Exception as e:
#                     logger.warning(f"Database generation failed: {str(e)}")
            
#             # Strategy 3: Use fallback video
#             video_content = await self._generate_fallback_video(request)
#             if video_content:
#                 self._generation_stats["fallback_generations"] += 1
#                 return VideoGenerationResult(
#                     success=True,
#                     video_content=video_content,
#                     status=GenerationStatus.COMPLETED,
#                     metadata={"generation_method": "fallback", "quality": request.quality.value}
#                 )
            
#             # All strategies failed
#             return VideoGenerationResult(
#                 success=False,
#                 status=GenerationStatus.FAILED,
#                 error_message="All generation strategies failed"
#             )
            
#         except Exception as e:
#             logger.error(f"Video generation error: {str(e)}")
#             return VideoGenerationResult(
#                 success=False,
#                 status=GenerationStatus.FAILED,
#                 error_message=str(e)
#             )
    
#     async def _generate_from_database(self, request: VideoGenerationRequest) -> Optional[bytes]:
#         """Generate video by combining signs from database"""
#         try:
#             # Parse text into words/phrases
#             words = self._parse_text_for_signs(request.text, request.language_code)
            
#             if not words:
#                 return None
            
#             # Get sign videos from database
#             sign_segments = await self._get_sign_segments(words, request.language_code)
            
#             if not sign_segments or len(sign_segments) == 0:
#                 return None
            
#             # Combine segments into final video
#             combined_video = await self._combine_video_segments(sign_segments, request)
            
#             return combined_video
            
#         except Exception as e:
#             logger.error(f"Database generation error: {str(e)}")
#             return None
    
#     async def _get_sign_segments(self, words: List[str], language_code: str) -> List[SignVideoSegment]:
#         """Retrieve sign video segments from database"""
#         segments = []
        
#         try:
#             async with AsyncSession(get_session().bind) as session:
#                 for word in words:
#                     # Query for sign gesture
#                     statement = select(SignGesture).where(
#                         SignGesture.word.ilike(f"%{word}%"),
#                         SignGesture.language_code == language_code,
#                         SignGesture.is_active == True
#                     )
                    
#                     result = await session.exec(statement)
#                     sign = result.first()
                    
#                     if sign and sign.video_url:
#                         # Download or get cached video segment
#                         video_path = await self._download_sign_video(sign.video_url, word)
                        
#                         segments.append(SignVideoSegment(
#                             word=word,
#                             video_path=video_path,
#                             duration_ms=sign.duration_ms or 2000,
#                             confidence_score=sign.confidence_score or 1.0,
#                             is_generated=False
#                         ))
#                     else:
#                         # Create placeholder or skip
#                         logger.warning(f"No sign found for word: {word}")
            
#             return segments
            
#         except Exception as e:
#             logger.error(f"Error getting sign segments: {str(e)}")
#             return []
    
#     async def _combine_video_segments(
#         self, 
#         segments: List[SignVideoSegment], 
#         request: VideoGenerationRequest
#     ) -> Optional[bytes]:
#         """Combine individual sign video segments into final video"""
#         try:
#             if not segments:
#                 return None
            
#             # Create temporary file for output
#             import uuid
#             output_file = self.temp_dir / f"combined_{uuid.uuid4().hex}.mp4"
            
#             # Use moviepy to combine videos
#             clips = []
            
#             for segment in segments:
#                 if segment.video_path and segment.video_path.exists():
#                     try:
#                         clip = VideoFileClip(str(segment.video_path))
                        
#                         # Adjust speed if needed
#                         if request.speed_multiplier != 1.0:
#                             clip = clip.fx(lambda c: c.speedx(request.speed_multiplier))
                        
#                         clips.append(clip)
                        
#                     except Exception as e:
#                         logger.warning(f"Error loading video segment {segment.video_path}: {str(e)}")
            
#             if not clips:
#                 return None
            
#             # Concatenate all clips
#             final_clip = concatenate_videoclips(clips, method="compose")
            
#             # Add subtitles if requested
#             if request.include_subtitles:
#                 final_clip = await self._add_subtitles(final_clip, request.text)
            
#             # Write final video
#             final_clip.write_videofile(
#                 str(output_file),
#                 fps=self.default_fps,
#                 codec='libx264',
#                 audio=False,
#                 verbose=False,
#                 logger=None
#             )
            
#             # Read final video content
#             async with aiofiles.open(output_file, 'rb') as f:
#                 video_content = await f.read()
            
#             # Cleanup
#             output_file.unlink(missing_ok=True)
#             for clip in clips:
#                 clip.close()
#             final_clip.close()
            
#             return video_content
            
#         except Exception as e:
#             logger.error(f"Error combining video segments: {str(e)}")
#             return None
    
#     async def _generate_fallback_video(self, request: VideoGenerationRequest) -> Optional[bytes]:
#         """Generate fallback video when other methods fail"""
#         try:
#             fallback_files = list(self.fallback_video_dir.glob(f"*{request.language_code}*.mp4"))
            
#             if not fallback_files:
#                 fallback_files = list(self.fallback_video_dir.glob("*.mp4"))
            
#             if fallback_files:
#                 # Use the first available fallback video
#                 fallback_file = fallback_files[0]
                
#                 async with aiofiles.open(fallback_file, 'rb') as f:
#                     content = await f.read()
                
#                 logger.info(f"Using fallback video: {fallback_file.name}")
#                 return content
            
#             # Generate a simple placeholder video if no fallbacks exist
#             return await self._generate_placeholder_video(request)
            
#         except Exception as e:
#             logger.error(f"Error generating fallback video: {str(e)}")
#             return None
    
#     async def _generate_placeholder_video(self, request: VideoGenerationRequest) -> Optional[bytes]:
#         """Generate a simple placeholder video"""
#         try:
#             import uuid
#             output_file = self.temp_dir / f"placeholder_{uuid.uuid4().hex}.mp4"
            
#             # Create a simple video with text
#             duration = min(len(request.text.split()) * 0.5, 10)  # 0.5 seconds per word, max 10 seconds
            
#             # Create a colored background clip
#             color_clip = ImageClip(
#                 size=self.default_resolution,
#                 color=(255, 255, 255),  # White background
#                 duration=duration
#             )
            
#             # Write video
#             color_clip.write_videofile(
#                 str(output_file),
#                 fps=self.default_fps,
#                 codec='libx264',
#                 audio=False,
#                 verbose=False,
#                 logger=None
#             )
            
#             # Read content
#             async with aiofiles.open(output_file, 'rb') as f:
#                 content = await f.read()
            
#             # Cleanup
#             output_file.unlink(missing_ok=True)
#             color_clip.close()
            
#             return content
            
#         except Exception as e:
#             logger.error(f"Error generating placeholder video: {str(e)}")
#             return None
    
#     def _parse_text_for_signs(self, text: str, language_code: str) -> List[str]:
#         """Parse text into words/phrases suitable for sign lookup"""
#         # Simple word-based parsing - can be enhanced with NLP
#         words = text.lower().strip().split()
        
#         # Filter out common stop words or very short words
#         filtered_words = [
#             word.strip('.,!?;:"()[]{}') 
#             for word in words 
#             if len(word.strip('.,!?;:"()[]{}')) > 1
#         ]
        
#         return filtered_words
    
#     async def _download_sign_video(self, video_url: str, cache_key: str) -> Optional[Path]:
#         """Download and cache sign video from URL"""
#         try:
#             cache_file = self.temp_dir / f"sign_{cache_key}_{hash(video_url)}.mp4"
            
#             # Check if already cached
#             if cache_file.exists():
#                 return cache_file
            
#             # Download video
#             async with aiohttp.ClientSession() as session:
#                 async with session.get(video_url) as response:
#                     if response.status == 200:
#                         content = await response.read()
                        
#                         async with aiofiles.open(cache_file, 'wb') as f:
#                             await f.write(content)
                        
#                         return cache_file
            
#             return None
            
#         except Exception as e:
#             logger.error(f"Error downloading sign video {video_url}: {str(e)}")
#             return None
    
#     async def _add_subtitles(self, video_clip, text: str):
#         """Add subtitles to video clip"""
#         try:
#             # This is a simplified subtitle implementation
#             # In production, you might want to use more sophisticated subtitle libraries
#             from moviepy.video.tools.subtitles import SubtitlesClip
            
#             # Create subtitle file content
#             subtitle_content = f"1\n00:00:00,000 --> 00:00:{int(video_clip.duration):02d},000\n{text}\n"
            
#             # For now, return the clip without subtitles
#             # Proper subtitle implementation would require more complex timing
#             return video_clip
            
#         except Exception as e:
#             logger.warning(f"Failed to add subtitles: {str(e)}")
#             return video_clip
    
#     async def _update_generation_stats(self, generation_time_ms: float, status: GenerationStatus):
#         """Update internal generation statistics"""
#         self._generation_stats["total_generations"] += 1
        
#         # Update rolling average
#         current_avg = self._generation_stats["average_generation_time_ms"]
#         total_gens = self._generation_stats["total_generations"]
        
#         self._generation_stats["average_generation_time_ms"] = (
#             (current_avg * (total_gens - 1) + generation_time_ms) / total_gens
#         )
    
#     def get_generation_statistics(self) -> Dict[str, Any]:
#         """Get generation statistics for monitoring"""
#         return {
#             **self._generation_stats,
#             "success_rate": (
#                 (self._generation_stats["total_generations"] - self._generation_stats.get("failed_generations", 0))
#                 / max(self._generation_stats["total_generations"], 1)
#             ),
#             "timestamp": datetime.now().isoformat()
#         }


# # Factory function for dependency injection
# def get_video_service() -> VideoService:
#     """Factory function to get video service instance"""
#     return VideoService()