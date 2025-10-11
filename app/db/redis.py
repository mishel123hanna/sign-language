from app.core.settings import settings
from redis.asyncio import Redis
from redis.exceptions import (
    ConnectionError, 
    TimeoutError, 
    RedisError,
    AuthenticationError,
    ResponseError
)
from fastapi.exceptions import HTTPException
# JTI: JWT ID
JTI_EXPIRY = 3600


token_blocklist = Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    password=settings.REDIS_PASSWORD,
    ssl=True,
)


async def add_jti_to_blocklist(jti: str) -> None:
    try:
        await token_blocklist.set(name=jti, value="", ex=JTI_EXPIRY)
    except ConnectionError:
    # سجّل الخطأ أو أرسل رد مناسب
        print("Redis connection error")
        raise HTTPException(status_code=500, detail="Redis connection failed")

async def token_in_blocklist(jti: str) -> bool:
    try:
        jti = await token_blocklist.get(jti)
    except ConnectionError:
    # سجّل الخطأ أو أرسل رد مناسب
        print("Redis connection error")
        raise HTTPException(status_code=500, detail="Redis connection failed")
    return jti is not None


# # with cloud
# import asyncio
# import logging
# from typing import Optional, Union, Any, Dict
# from datetime import datetime, timedelta
# from contextlib import asynccontextmanager
# import json

# import redis.asyncio as redis
# from redis.asyncio.retry import Retry
# from redis.backoff import ExponentialBackoff
# from redis.exceptions import (
#     ConnectionError, 
#     TimeoutError, 
#     RedisError,
#     AuthenticationError,
#     ResponseError
# )
# from tenacity import (
#     retry, 
#     stop_after_attempt, 
#     wait_exponential, 
#     retry_if_exception_type,
#     before_sleep_log
# )

# from app.core.settings import settings

# logger = logging.getLogger(__name__)


# class RedisConnectionError(Exception):
#     """Custom Redis connection error"""
#     pass


# class RedisService:
#     """
#     Robust Redis service with comprehensive error handling,
#     connection pooling, and automatic retry logic.
#     """
    
#     def __init__(self):
#         self.redis_url = settings.REDIS_URL
#         self.pool: Optional[redis.ConnectionPool] = None
#         self.client: Optional[redis.Redis] = None
        
#         # Connection settings
#         self.max_connections = 20
#         self.connection_timeout = 10  # seconds
#         self.socket_timeout = 5  # seconds
#         self.retry_on_timeout = True
#         self.health_check_interval = 30  # seconds
        
#         # Token blocklist settings
#         self.blocklist_prefix = "blocklist:"
#         self.default_token_ttl = 86400  # 24 hours in seconds
        
#         # Monitoring
#         self._connection_stats = {
#             'total_connections': 0,
#             'failed_connections': 0,
#             'successful_operations': 0,
#             'failed_operations': 0,
#             'last_health_check': None,
#             'is_healthy': False
#         }
        
#         # Initialize connection
#         asyncio.create_task(self._initialize_connection())
    
#     async def _initialize_connection(self) -> None:
#         """Initialize Redis connection with retry logic"""
#         try:
#             await self._create_connection_pool()
#             await self._test_connection()
#             logger.info("Redis connection initialized successfully")
#         except Exception as e:
#             logger.error(f"Failed to initialize Redis connection: {str(e)}")
#             # Don't raise here - let individual operations handle retries
    
#     async def _create_connection_pool(self) -> None:
#         """Create Redis connection pool with optimized settings"""
#         try:
#             # Parse Redis URL or use individual components
#             if self.redis_url:
#                 # For Upstash or other cloud Redis services
#                 self.pool = redis.ConnectionPool.from_url(
#                     self.redis_url,
#                     max_connections=self.max_connections,
#                     socket_connect_timeout=self.connection_timeout,
#                     socket_timeout=self.socket_timeout,
#                     retry_on_timeout=self.retry_on_timeout,
#                     health_check_interval=self.health_check_interval,
#                     retry=Retry(ExponentialBackoff(), retries=3),
#                     decode_responses=True,
#                     # SSL settings for secure connections
#                     ssl_cert_reqs=None,
#                     ssl_check_hostname=False,
#                 )
#             else:
#                 # Fallback to individual settings
#                 self.pool = redis.ConnectionPool(
#                     host=getattr(settings, 'REDIS_HOST', 'localhost'),
#                     port=getattr(settings, 'REDIS_PORT', 6379),
#                     password=getattr(settings, 'REDIS_PASSWORD', None),
#                     db=getattr(settings, 'REDIS_DB', 0),
#                     max_connections=self.max_connections,
#                     socket_connect_timeout=self.connection_timeout,
#                     socket_timeout=self.socket_timeout,
#                     retry_on_timeout=self.retry_on_timeout,
#                     health_check_interval=self.health_check_interval,
#                     retry=Retry(ExponentialBackoff(), retries=3),
#                     decode_responses=True,
#                 )
            
#             self.client = redis.Redis(connection_pool=self.pool)
            
#         except Exception as e:
#             logger.error(f"Failed to create Redis connection pool: {str(e)}")
#             raise RedisConnectionError(f"Unable to create Redis connection: {str(e)}")
    
#     async def _test_connection(self) -> None:
#         """Test Redis connection"""
#         if not self.client:
#             raise RedisConnectionError("Redis client not initialized")
        
#         try:
#             await self.client.ping()
#             self._connection_stats['is_healthy'] = True
#             self._connection_stats['last_health_check'] = datetime.now()
#             logger.info("Redis connection test successful")
#         except Exception as e:
#             self._connection_stats['is_healthy'] = False
#             logger.error(f"Redis connection test failed: {str(e)}")
#             raise RedisConnectionError(f"Redis connection test failed: {str(e)}")
    
#     @retry(
#         stop=stop_after_attempt(3),
#         wait=wait_exponential(multiplier=1, min=2, max=10),
#         retry=retry_if_exception_type((ConnectionError, TimeoutError, RedisError)),
#         before_sleep=before_sleep_log(logger, logging.WARNING)
#     )
#     async def _execute_with_retry(self, operation_name: str, operation_func, *args, **kwargs):
#         """Execute Redis operation with retry logic"""
#         try:
#             # Ensure connection is available
#             if not self.client or not self._connection_stats['is_healthy']:
#                 await self._ensure_connection()
            
#             result = await operation_func(*args, **kwargs)
#             self._connection_stats['successful_operations'] += 1
#             return result
            
#         except (ConnectionError, TimeoutError) as e:
#             self._connection_stats['failed_operations'] += 1
#             logger.error(f"Redis {operation_name} failed with connection error: {str(e)}")
            
#             # Try to reconnect
#             try:
#                 await self._ensure_connection()
#             except Exception as reconnect_error:
#                 logger.error(f"Failed to reconnect to Redis: {str(reconnect_error)}")
            
#             raise
            
#         except RedisError as e:
#             self._connection_stats['failed_operations'] += 1
#             logger.error(f"Redis {operation_name} failed with Redis error: {str(e)}")
#             raise
            
#         except Exception as e:
#             self._connection_stats['failed_operations'] += 1
#             logger.error(f"Redis {operation_name} failed with unexpected error: {str(e)}")
#             raise
    
#     async def _ensure_connection(self) -> None:
#         """Ensure Redis connection is available"""
#         try:
#             if not self.client:
#                 await self._create_connection_pool()
            
#             # Test connection
#             await self.client.ping()
#             self._connection_stats['is_healthy'] = True
#             self._connection_stats['last_health_check'] = datetime.now()
            
#         except Exception as e:
#             self._connection_stats['is_healthy'] = False
#             logger.error(f"Failed to ensure Redis connection: {str(e)}")
            
#             # Try to recreate connection
#             try:
#                 await self._create_connection_pool()
#                 await self.client.ping()
#                 self._connection_stats['is_healthy'] = True
#                 logger.info("Successfully recreated Redis connection")
#             except Exception as recreate_error:
#                 logger.error(f"Failed to recreate Redis connection: {str(recreate_error)}")
#                 raise RedisConnectionError(f"Unable to establish Redis connection: {str(recreate_error)}")
    
#     async def health_check(self) -> Dict[str, Any]:
#         """Perform health check and return status"""
#         try:
#             if not self.client:
#                 return {
#                     'healthy': False,
#                     'error': 'Redis client not initialized',
#                     'stats': self._connection_stats
#                 }
            
#             start_time = datetime.now()
#             await self.client.ping()
#             response_time = (datetime.now() - start_time).total_seconds() * 1000
            
#             self._connection_stats['is_healthy'] = True
#             self._connection_stats['last_health_check'] = datetime.now()
            
#             return {
#                 'healthy': True,
#                 'response_time_ms': response_time,
#                 'stats': self._connection_stats
#             }
            
#         except Exception as e:
#             self._connection_stats['is_healthy'] = False
#             return {
#                 'healthy': False,
#                 'error': str(e),
#                 'stats': self._connection_stats
#             }
    
#     # Token blocklist operations
    
#     async def token_in_blocklist(self, jti: str) -> bool:
#         """
#         Check if a token JTI is in the blocklist
        
#         Args:
#             jti: JWT Token Identifier
            
#         Returns:
#             True if token is blocklisted, False otherwise
#         """
#         try:
#             key = f"{self.blocklist_prefix}{jti}"
#             result = await self._execute_with_retry(
#                 "token_in_blocklist",
#                 self.client.get,
#                 key
#             )
#             return result is not None
            
#         except Exception as e:
#             logger.error(f"Error checking token blocklist for JTI {jti}: {str(e)}")
#             # In case of error, assume token is not blocklisted (fail open)
#             # You might want to change this behavior based on your security requirements
#             return False
    
#     async def add_token_to_blocklist(
#         self, 
#         jti: str, 
#         ttl: Optional[int] = None,
#         user_id: Optional[str] = None
#     ) -> bool:
#         """
#         Add a token to the blocklist
        
#         Args:
#             jti: JWT Token Identifier
#             ttl: Time to live in seconds (defaults to default_token_ttl)
#             user_id: Optional user ID for metadata
            
#         Returns:
#             True if successfully added, False otherwise
#         """
#         try:
#             key = f"{self.blocklist_prefix}{jti}"
#             ttl = ttl or self.default_token_ttl
            
#             # Store with metadata
#             value = {
#                 'blocked_at': datetime.now().isoformat(),
#                 'user_id': user_id,
#                 'ttl': ttl
#             }
            
#             result = await self._execute_with_retry(
#                 "add_token_to_blocklist",
#                 self.client.setex,
#                 key,
#                 ttl,
#                 json.dumps(value)
#             )
            
#             logger.info(f"Added token {jti} to blocklist with TTL {ttl}s")
#             return result is True
            
#         except Exception as e:
#             logger.error(f"Error adding token {jti} to blocklist: {str(e)}")
#             return False
    
#     async def remove_token_from_blocklist(self, jti: str) -> bool:
#         """
#         Remove a token from the blocklist
        
#         Args:
#             jti: JWT Token Identifier
            
#         Returns:
#             True if successfully removed, False otherwise
#         """
#         try:
#             key = f"{self.blocklist_prefix}{jti}"
#             result = await self._execute_with_retry(
#                 "remove_token_from_blocklist",
#                 self.client.delete,
#                 key
#             )
            
#             logger.info(f"Removed token {jti} from blocklist")
#             return result > 0
            
#         except Exception as e:
#             logger.error(f"Error removing token {jti} from blocklist: {str(e)}")
#             return False
    
#     # General Redis operations
    
#     async def set(
#         self, 
#         key: str, 
#         value: Union[str, bytes, int, float], 
#         ttl: Optional[int] = None
#     ) -> bool:
#         """Set a key-value pair with optional TTL"""
#         try:
#             if ttl:
#                 result = await self._execute_with_retry(
#                     "set_with_ttl",
#                     self.client.setex,
#                     key,
#                     ttl,
#                     value
#                 )
#             else:
#                 result = await self._execute_with_retry(
#                     "set",
#                     self.client.set,
#                     key,
#                     value
#                 )
#             return result is True
            
#         except Exception as e:
#             logger.error(f"Error setting key {key}: {str(e)}")
#             return False
    
#     async def get(self, key: str) -> Optional[str]:
#         """Get value by key"""
#         try:
#             result = await self._execute_with_retry(
#                 "get",
#                 self.client.get,
#                 key
#             )
#             return result
            
#         except Exception as e:
#             logger.error(f"Error getting key {key}: {str(e)}")
#             return None
    
#     async def delete(self, key: str) -> bool:
#         """Delete a key"""
#         try:
#             result = await self._execute_with_retry(
#                 "delete",
#                 self.client.delete,
#                 key
#             )
#             return result > 0
            
#         except Exception as e:
#             logger.error(f"Error deleting key {key}: {str(e)}")
#             return False
    
#     async def exists(self, key: str) -> bool:
#         """Check if key exists"""
#         try:
#             result = await self._execute_with_retry(
#                 "exists",
#                 self.client.exists,
#                 key
#             )
#             return result > 0
            
#         except Exception as e:
#             logger.error(f"Error checking existence of key {key}: {str(e)}")
#             return False
    
#     async def ttl(self, key: str) -> int:
#         """Get TTL of a key"""
#         try:
#             result = await self._execute_with_retry(
#                 "ttl",
#                 self.client.ttl,
#                 key
#             )
#             return result
            
#         except Exception as e:
#             logger.error(f"Error getting TTL for key {key}: {str(e)}")
#             return -1
    
#     # Batch operations
    
#     async def mget(self, keys: list) -> list:
#         """Get multiple keys at once"""
#         try:
#             result = await self._execute_with_retry(
#                 "mget",
#                 self.client.mget,
#                 keys
#             )
#             return result or []
            
#         except Exception as e:
#             logger.error(f"Error getting multiple keys: {str(e)}")
#             return []
    
#     async def mset(self, mapping: dict) -> bool:
#         """Set multiple key-value pairs at once"""
#         try:
#             result = await self._execute_with_retry(
#                 "mset",
#                 self.client.mset,
#                 mapping
#             )
#             return result is True
            
#         except Exception as e:
#             logger.error(f"Error setting multiple keys: {str(e)}")
#             return False
    
#     # Context manager for transactions
    
#     @asynccontextmanager
#     async def pipeline(self):
#         """Context manager for Redis pipeline operations"""
#         if not self.client:
#             await self._ensure_connection()
        
#         pipe = self.client.pipeline()
#         try:
#             yield pipe
#             await pipe.execute()
#         except Exception as e:
#             logger.error(f"Pipeline execution failed: {str(e)}")
#             raise
#         finally:
#             await pipe.reset()
    
#     # Cleanup
    
#     async def close(self) -> None:
#         """Close Redis connection"""
#         try:
#             if self.client:
#                 await self.client.close()
#                 logger.info("Redis connection closed")
#         except Exception as e:
#             logger.error(f"Error closing Redis connection: {str(e)}")
#         finally:
#             self.client = None
#             self.pool = None
    
#     def get_stats(self) -> Dict[str, Any]:
#         """Get connection statistics"""
#         return {
#             **self._connection_stats,
#             'pool_info': {
#                 'max_connections': self.max_connections,
#                 'created_connections': self.pool.created_connections if self.pool else 0,
#                 'available_connections': len(self.pool._available_connections) if self.pool else 0,
#                 'in_use_connections': len(self.pool._in_use_connections) if self.pool else 0,
#             } if self.pool else None
#         }


# # Global instance
# redis_service = RedisService()

# # Convenience functions for backward compatibility
# async def token_in_blocklist(jti: str) -> bool:
#     """Check if token is in blocklist"""
#     return await redis_service.token_in_blocklist(jti)

# async def add_token_to_blocklist(jti: str, ttl: Optional[int] = None, user_id: Optional[str] = None) -> bool:
#     """Add token to blocklist"""
#     return await redis_service.add_token_to_blocklist(jti, ttl, user_id)

# async def remove_token_from_blocklist(jti: str) -> bool:
#     """Remove token from blocklist"""
#     return await redis_service.remove_token_from_blocklist(jti)

# # Dependency for FastAPI
# def get_redis_service() -> RedisService:
#     """Get Redis service instance"""
#     return redis_service


# @asynccontextmanager
# async def lifespan():
#     """
#     FastAPI lifespan handler for Redis connection management
    
#     Usage:
#         app = FastAPI(lifespan=lifespan)
#     """
#     # Startup
#     logger.info("Starting Redis service...")
#     try:
#         # Test the connection
#         health = await redis_service.health_check()
#         if health['healthy']:
#             logger.info("Redis service started successfully")
#         else:
#             logger.warning(f"Redis service started but health check failed: {health.get('error')}")
#     except Exception as e:
#         logger.error(f"Failed to start Redis service: {str(e)}")
#         # Don't fail startup - let individual operations handle retries
    
#     yield
    
#     # Shutdown
#     logger.info("Shutting down Redis service...")
#     try:
#         await redis_service.close()
#         logger.info("Redis service shut down successfully")
#     except Exception as e:
#         logger.error(f"Error during Redis shutdown: {str(e)}")
