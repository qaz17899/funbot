"""Redis caching utilities.

Provides:
- OrjsonSerializer for high-performance JSON serialization
- RedisImageCache for caching PIL images in Redis
"""

from __future__ import annotations

import io
import os
from concurrent.futures import ThreadPoolExecutor
from typing import Any

import orjson
import redis
from loguru import logger

from funbot.config import CONFIG

__all__ = ("OrjsonSerializer", "RedisImageCache", "image_cache")

# Default TTL for cached images (1 hour)
IMAGE_CACHE_TTL = 3600


class OrjsonSerializer:
    """High-performance JSON serializer using orjson.

    Compatible with aiocache serializer interface.
    """

    DEFAULT_ENCODING = "utf-8"

    def dumps(self, value: Any) -> str:
        """Serialize value to JSON string."""
        return orjson.dumps(value).decode()

    def loads(self, value: str | None) -> Any:
        """Deserialize JSON string to value."""
        if value is None:
            return None
        return orjson.loads(value.encode())


class RedisImageCache:
    """Redis cache for PIL images.

    Caches generated images in Redis to avoid regenerating them.
    Uses a background executor for non-blocking cache writes.

    Usage:
        from funbot.cache import image_cache

        # Get cached image
        if image_cache:
            cached = image_cache.get("my_key")
            if cached:
                return cached

        # Generate image...
        image = generate_image()

        # Cache in background
        if image_cache:
            image_cache.set_background("my_key", image)
    """

    def __init__(self, redis_url: str) -> None:
        """Initialize the image cache.

        Args:
            redis_url: Redis connection URL.
        """
        self._redis_url = redis_url
        self._redis: redis.ConnectionPool | None = None
        self._bg_executor: ThreadPoolExecutor | None = None

    @property
    def redis(self) -> redis.ConnectionPool:
        """Get the Redis connection pool."""
        if self._redis is None:
            msg = "Redis connection pool is not initialized. Call connect() first."
            raise RuntimeError(msg)
        return self._redis

    @property
    def bg_executor(self) -> ThreadPoolExecutor:
        """Get the background thread executor."""
        if self._bg_executor is None:
            msg = "Background executor is not initialized. Call connect() first."
            raise RuntimeError(msg)
        return self._bg_executor

    def set(self, key: str, image: Any) -> None:
        """Cache an image synchronously.

        Args:
            key: Cache key.
            image: PIL Image to cache.
        """
        try:
            with redis.Redis(connection_pool=self.redis) as r, io.BytesIO() as output:
                image.save(output, format="PNG")
                r.setex(key, IMAGE_CACHE_TTL, output.getvalue())
        except redis.RedisError as e:
            logger.error(f"Redis error while setting image {key}: {e}")

    def set_background(self, key: str, image: Any) -> None:
        """Cache an image asynchronously in background.

        Args:
            key: Cache key.
            image: PIL Image to cache (will be copied).
        """
        self.bg_executor.submit(self.set, key, image.copy())

    def get(self, key: str) -> Any:
        """Get a cached image.

        Args:
            key: Cache key.

        Returns:
            The cached PIL Image, or None if not found.
        """
        try:
            with redis.Redis(connection_pool=self.redis) as r:
                image_data = r.get(key)
                if image_data is None:
                    return None
        except redis.RedisError as e:
            logger.error(f"Redis error while getting image {key}: {e}")
            return None
        else:
            # Import PIL here to avoid requiring it if not using image cache
            from PIL import Image as PILImage  # pyright: ignore[reportMissingImports]

            return PILImage.open(io.BytesIO(image_data))  # pyright: ignore[reportArgumentType]

    def connect(self) -> None:
        """Initialize the Redis connection pool and background executor."""
        logger.info(f"Image cache in PID {os.getpid()} connecting to Redis")
        self._redis = redis.ConnectionPool.from_url(self._redis_url)
        self._bg_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="RedisCacheWorker")

    def disconnect(self) -> None:
        """Close the connection pool and shutdown executor."""
        self.bg_executor.shutdown(wait=True, cancel_futures=True)
        self.redis.disconnect()
        logger.info(f"Image cache in PID {os.getpid()} disconnected from Redis")


# Global image cache instance (None if Redis not configured)
image_cache: RedisImageCache | None = (
    RedisImageCache(redis_url=CONFIG.redis_url) if CONFIG.redis_url else None
)
