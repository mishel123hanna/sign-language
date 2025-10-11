import os
import asyncio
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from contextlib import asynccontextmanager

from supabase import create_client, Client
from supabase.lib.client_options import ClientOptions
from tenacity import (
    retry, 
    stop_after_attempt, 
    wait_exponential, 
    retry_if_exception_type,
    before_sleep_log
)
import aiofiles
import aiohttp
from urllib.parse import urlparse

from app.core.settings import settings
from app.utils.exceptions import StorageError, StorageConnectionError

logger = logging.getLogger(__name__)


@dataclass
class UploadResult:
    """Result of a storage upload operation"""
    success: bool
    url: Optional[str] = None
    path: Optional[str] = None
    size_bytes: Optional[int] = None
    error: Optional[str] = None
    upload_time_ms: Optional[int] = None


@dataclass
class StorageStats:
    """Storage statistics for monitoring"""
    total_files: int
    total_size_bytes: int
    user_file_count: int
    user_size_bytes: int
    oldest_file_date: Optional[datetime] = None
    newest_file_date: Optional[datetime] = None


class StorageService:
    """
    Enhanced Supabase Storage service with comprehensive error handling,
    retry logic, and monitoring capabilities.
    """
    
    def __init__(self):
        self.supabase_url = settings.SUPABASE_PROJECT_URL
        self.supabase_key = settings.SUPABASE_API_KEY
        self.video_bucket = "signs-generated-by-ai"
        
        # Initialize Supabase client with optimized settings
        self.client = self._create_supabase_client()
        
        # Configuration
        self.max_file_size = 100 * 1024 * 1024  # 100MB
        self.allowed_mime_types = {
            'video/mp4', 'video/mpeg', 'video/quicktime', 
            'video/x-msvideo', 'video/webm'
        }
        self.chunk_size = 8192  # For streaming uploads
        
        # Retry configuration (since ClientOptions doesn't support storage-specific retries)
        self.storage_retry_attempts = 3
        self.storage_retry_delay = 1.0
        
        # Monitoring
        self._upload_stats = {
            'total_uploads': 0,
            'failed_uploads': 0,
            'total_bytes_uploaded': 0,
            'average_upload_time_ms': 0
        }
    
    def _create_supabase_client(self) -> Client:
        """Create Supabase client with optimized configuration"""
        try:
            # Only use valid ClientOptions parameters
            client_options = ClientOptions(
                auto_refresh_token=True,
                persist_session=True,
                # Remove unsupported storage retry options
            )
            
            return create_client(
                self.supabase_url, 
                self.supabase_key,
                options=client_options
            )
        except Exception as e:
            logger.error(f"Failed to create Supabase client: {str(e)}")
            raise StorageConnectionError(f"Unable to connect to storage: {str(e)}")
    
    async def health_check(self) -> bool:
        """Check if storage service is healthy"""
        try:
            # Try to list files in the bucket (should be fast)
            result = self.client.storage.from_(self.video_bucket).list(
                path="", 
                limit=1,
                offset=0
            )
            return not ("error" in result and result["error"])
        except Exception as e:
            logger.error(f"Storage health check failed: {str(e)}")
            return False
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((ConnectionError, TimeoutError, StorageError)),
        before_sleep=before_sleep_log(logger, logging.WARNING)
    )
    async def upload_video(
        self, 
        file_path: Path, 
        destination_path: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Upload video file to Supabase Storage with comprehensive error handling
        
        Args:
            file_path: Local path to the video file
            destination_path: Remote path in storage bucket
            metadata: Optional metadata to attach to the file
        
        Returns:
            Public URL of the uploaded file
            
        Raises:
            StorageError: If upload fails after retries
        """
        start_time = datetime.now()
        
        try:
            # Validate file before upload
            await self._validate_file(file_path)
            
            # Read file content
            file_content = await self._read_file_async(file_path)
            file_size = len(file_content)
            
            # Prepare upload options
            upload_options = {
                "content-type": self._get_content_type(file_path),
                "cache-control": "3600",  # 1 hour cache
            }
            
            # Add metadata if provided
            if metadata:
                upload_options.update(metadata)
            
            # Perform upload with custom retry logic
            logger.info(f"Uploading {file_size} bytes to {destination_path}")
            
            result = await self._upload_with_retry(
                destination_path, 
                file_content, 
                upload_options
            )
            
            # Check for upload errors
            if isinstance(result, dict) and "error" in result:
                error_msg = result.get("error", {}).get("message", "Unknown upload error")
                raise StorageError(f"Upload failed: {error_msg}")
            
            # Get public URL
            public_url = self.client.storage.from_(self.video_bucket).get_public_url(destination_path)
            
            # Update statistics
            upload_time = (datetime.now() - start_time).total_seconds() * 1000
            await self._update_upload_stats(file_size, upload_time, success=True)
            
            logger.info(f"Successfully uploaded {destination_path} in {upload_time:.2f}ms")
            
            return public_url
            
        except Exception as e:
            # Update failure statistics
            upload_time = (datetime.now() - start_time).total_seconds() * 1000
            await self._update_upload_stats(0, upload_time, success=False)
            
            logger.error(f"Failed to upload {destination_path}: {str(e)}")
            raise StorageError(f"Upload failed: {str(e)}")
    
    async def _upload_with_retry(
        self, 
        destination_path: str, 
        file_content: bytes, 
        upload_options: Dict[str, Any]
    ) -> Any:
        """
        Perform upload with custom retry logic since ClientOptions doesn't support storage retries
        """
        last_exception = None
        
        for attempt in range(self.storage_retry_attempts):
            try:
                result = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: self.client.storage.from_(self.video_bucket).upload(
                        path=destination_path,
                        file=file_content,
                        file_options=upload_options
                    )
                )
                return result
                
            except Exception as e:
                last_exception = e
                if attempt < self.storage_retry_attempts - 1:
                    wait_time = self.storage_retry_delay * (2 ** attempt)  # Exponential backoff
                    logger.warning(f"Upload attempt {attempt + 1} failed, retrying in {wait_time}s: {str(e)}")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"All {self.storage_retry_attempts} upload attempts failed")
                    break
        
        # If we get here, all retries failed
        raise last_exception or StorageError("Upload failed after all retries")
    
    async def upload_video_stream(
        self,
        file_stream,
        destination_path: str,
        file_size: int,
        content_type: str = "video/mp4"
    ) -> str:
        """
        Upload video from stream for large files
        
        Args:
            file_stream: Async file stream
            destination_path: Remote path in storage bucket
            file_size: Size of the file in bytes
            content_type: MIME type of the file
        
        Returns:
            Public URL of the uploaded file
        """
        try:
            # Validate file size
            if file_size > self.max_file_size:
                raise StorageError(f"File size {file_size} exceeds maximum {self.max_file_size}")
            
            # Read stream in chunks
            chunks = []
            async for chunk in self._read_stream_chunks(file_stream):
                chunks.append(chunk)
            
            file_content = b''.join(chunks)
            
            # Use regular upload method
            temp_path = Path(f"/tmp/stream_upload_{datetime.now().timestamp()}")
            async with aiofiles.open(temp_path, 'wb') as f:
                await f.write(file_content)
            
            try:
                url = await self.upload_video(temp_path, destination_path)
                return url
            finally:
                # Clean up temp file
                if temp_path.exists():
                    temp_path.unlink(missing_ok=True)
                    
        except Exception as e:
            logger.error(f"Stream upload failed for {destination_path}: {str(e)}")
            raise StorageError(f"Stream upload failed: {str(e)}")
    
    async def delete_file(self, file_path: str) -> bool:
        """
        Delete a file from storage
        
        Args:
            file_path: Path of the file to delete
            
        Returns:
            True if deletion was successful
        """
        try:
            result = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.client.storage.from_(self.video_bucket).remove([file_path])
            )
            
            if isinstance(result, dict) and "error" in result:
                logger.error(f"Failed to delete {file_path}: {result['error']}")
                return False
            
            logger.info(f"Successfully deleted {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting {file_path}: {str(e)}")
            return False
    
    async def delete_files_batch(self, file_paths: List[str], batch_size: int = 50) -> Dict[str, int]:
        """
        Delete multiple files in batches
        
        Args:
            file_paths: List of file paths to delete
            batch_size: Number of files to delete per batch
            
        Returns:
            Dictionary with success and failure counts
        """
        results = {"success": 0, "failed": 0}
        
        # Process in batches to avoid API limits
        for i in range(0, len(file_paths), batch_size):
            batch = file_paths[i:i + batch_size]
            
            try:
                result = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: self.client.storage.from_(self.video_bucket).remove(batch)
                )
                
                if isinstance(result, list):
                    # Count successful deletions
                    results["success"] += len([r for r in result if not r.get("error")])
                    results["failed"] += len([r for r in result if r.get("error")])
                else:
                    results["failed"] += len(batch)
                    
            except Exception as e:
                logger.error(f"Batch deletion failed for batch {i//batch_size + 1}: {str(e)}")
                results["failed"] += len(batch)
            
            # Small delay between batches to be respectful to the API
            await asyncio.sleep(0.1)
        
        logger.info(f"Batch deletion completed: {results['success']} success, {results['failed']} failed")
        return results
    
    async def list_user_files(
        self, 
        user_prefix: str, 
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        List files for a specific user
        
        Args:
            user_prefix: User folder prefix (e.g., "user_123")
            limit: Maximum number of files to return
            offset: Number of files to skip
            
        Returns:
            List of file metadata dictionaries
        """
        try:
            result = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.client.storage.from_(self.video_bucket).list(
                    path=user_prefix,
                    limit=limit,
                    offset=offset,
                    sortBy={"column": "created_at", "order": "desc"}
                )
            )
            
            if isinstance(result, dict) and "error" in result:
                logger.error(f"Failed to list files for {user_prefix}: {result['error']}")
                return []
            
            return result if isinstance(result, list) else []
            
        except Exception as e:
            logger.error(f"Error listing files for {user_prefix}: {str(e)}")
            return []
    
    async def cleanup_old_videos(
        self, 
        user_prefix: str, 
        days_old: int,
        batch_size: int = 100
    ) -> Dict[str, int]:
        """
        Clean up old videos for a user with improved batch processing
        
        Args:
            user_prefix: User folder prefix
            days_old: Delete files older than this many days
            batch_size: Number of files to process per batch
            
        Returns:
            Cleanup statistics
        """
        stats = {"total_found": 0, "deleted": 0, "failed": 0, "size_freed_bytes": 0}
        cutoff_date = datetime.now() - timedelta(days=days_old)
        
        try:
            # Get all files for user
            all_files = await self.list_user_files(user_prefix, limit=1000)
            stats["total_found"] = len(all_files)
            
            # Filter old files
            old_files = []
            for file_info in all_files:
                try:
                    # Parse filename to extract date
                    filename = file_info.get("name", "")
                    if self._is_file_old(filename, cutoff_date):
                        old_files.append({
                            "path": f"{user_prefix}/{filename}",
                            "size": file_info.get("metadata", {}).get("size", 0)
                        })
                except Exception as e:
                    logger.warning(f"Could not parse date from filename {filename}: {str(e)}")
            
            if not old_files:
                logger.info(f"No old files found for {user_prefix}")
                return stats
            
            # Delete in batches
            file_paths = [f["path"] for f in old_files]
            total_size = sum(f["size"] for f in old_files)
            
            deletion_results = await self.delete_files_batch(file_paths, batch_size)
            
            stats.update({
                "deleted": deletion_results["success"],
                "failed": deletion_results["failed"],
                "size_freed_bytes": total_size if deletion_results["success"] > 0 else 0
            })
            
            logger.info(f"Cleanup completed for {user_prefix}: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"Cleanup failed for {user_prefix}: {str(e)}")
            stats["failed"] = stats["total_found"]
            return stats
    
    async def get_storage_stats(self, user_prefix: Optional[str] = None) -> StorageStats:
        """
        Get storage statistics for monitoring
        
        Args:
            user_prefix: Optional user prefix to get user-specific stats
            
        Returns:
            Storage statistics
        """
        try:
            if user_prefix:
                files = await self.list_user_files(user_prefix, limit=1000)
            else:
                # Get global stats (this might be expensive for large buckets)
                files = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: self.client.storage.from_(self.video_bucket).list("", limit=1000)
                )
            
            if not files:
                return StorageStats(
                    total_files=0,
                    total_size_bytes=0,
                    user_file_count=0,
                    user_size_bytes=0
                )
            
            total_size = 0
            dates = []
            
            for file_info in files:
                size = file_info.get("metadata", {}).get("size", 0)
                total_size += size
                
                # Try to extract date from filename or metadata
                created_at = file_info.get("created_at")
                if created_at:
                    try:
                        date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                        dates.append(date)
                    except:
                        pass
            
            return StorageStats(
                total_files=len(files),
                total_size_bytes=total_size,
                user_file_count=len(files),
                user_size_bytes=total_size,
                oldest_file_date=min(dates) if dates else None,
                newest_file_date=max(dates) if dates else None
            )
            
        except Exception as e:
            logger.error(f"Failed to get storage stats: {str(e)}")
            return StorageStats(total_files=0, total_size_bytes=0, user_file_count=0, user_size_bytes=0)
    
    def get_upload_statistics(self) -> Dict[str, Any]:
        """Get upload statistics for monitoring"""
        return {
            **self._upload_stats,
            "success_rate": (
                (self._upload_stats["total_uploads"] - self._upload_stats["failed_uploads"]) 
                / max(self._upload_stats["total_uploads"], 1)
            ),
            "timestamp": datetime.now().isoformat()
        }
    
    # Private helper methods
    
    async def _validate_file(self, file_path: Path) -> None:
        """Validate file before upload"""
        if not file_path.exists():
            raise StorageError(f"File does not exist: {file_path}")
        
        file_size = file_path.stat().st_size
        if file_size > self.max_file_size:
            raise StorageError(f"File size {file_size} exceeds maximum {self.max_file_size}")
        
        if file_size == 0:
            raise StorageError("File is empty")
        
        # Validate content type
        content_type = self._get_content_type(file_path)
        if content_type not in self.allowed_mime_types:
            raise StorageError(f"Unsupported file type: {content_type}")
    
    async def _read_file_async(self, file_path: Path) -> bytes:
        """Read file content asynchronously"""
        try:
            async with aiofiles.open(file_path, 'rb') as f:
                return await f.read()
        except Exception as e:
            raise StorageError(f"Failed to read file {file_path}: {str(e)}")
    
    async def _read_stream_chunks(self, stream, chunk_size: int = None):
        """Read stream in chunks"""
        chunk_size = chunk_size or self.chunk_size
        while True:
            chunk = await stream.read(chunk_size)
            if not chunk:
                break
            yield chunk
    
    def _get_content_type(self, file_path: Path) -> str:
        """Determine content type from file extension"""
        extension = file_path.suffix.lower()
        content_type_map = {
            '.mp4': 'video/mp4',
            '.mpeg': 'video/mpeg',
            '.mpg': 'video/mpeg',
            '.mov': 'video/quicktime',
            '.avi': 'video/x-msvideo',
            '.webm': 'video/webm'
        }
        return content_type_map.get(extension, 'video/mp4')
    
    def _is_file_old(self, filename: str, cutoff_date: datetime) -> bool:
        """Check if file is older than cutoff date based on filename"""
        try:
            # Extract timestamp from filename (format: YYYYMMDD_HHMMSS_hash.mp4)
            parts = filename.split('_')
            if len(parts) >= 2:
                date_str = parts[0]  # YYYYMMDD
                time_str = parts[1]  # HHMMSS
                
                file_date = datetime.strptime(f"{date_str}_{time_str}", "%Y%m%d_%H%M%S")
                return file_date < cutoff_date
        except Exception:
            # If we can't parse the date, consider it old to be safe
            logger.warning(f"Could not parse date from filename: {filename}")
            return True
        
        return False
    
    async def _update_upload_stats(self, file_size: int, upload_time_ms: float, success: bool):
        """Update internal upload statistics"""
        self._upload_stats["total_uploads"] += 1
        
        if success:
            self._upload_stats["total_bytes_uploaded"] += file_size
            # Update rolling average
            current_avg = self._upload_stats["average_upload_time_ms"]
            total_uploads = self._upload_stats["total_uploads"]
            self._upload_stats["average_upload_time_ms"] = (
                (current_avg * (total_uploads - 1) + upload_time_ms) / total_uploads
            )
        else:
            self._upload_stats["failed_uploads"] += 1


# Factory function for dependency injection
def get_storage_service() -> StorageService:
    """Factory function to get storage service instance"""
    return StorageService()