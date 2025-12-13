"""Redis caching utilities.

Provides:
- OrjsonSerializer for high-performance JSON serialization
- RedisImageCache for caching PIL images in Redis
"""

from __future__ import annotations

import io
import os
from typing import TYPE_CHECKING, Any

import orjson
import redis.asyncio as redis
from loguru import logger

from funbot.config import CONFIG

if TYPE_CHECKING:
    from PIL import Image  # pyright: ignore[reportMissingImports]

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
    """Async Redis cache for PIL images.

    Caches generated images in Redis to avoid regenerating them.

    Usage:
        from funbot.cache import image_cache

        # Get cached image (async)
        if image_cache:
            cached = await image_cache.get("my_key")
            if cached:
                return cached

        # Generate image...
        image = generate_image()

        # Cache (async)
        if image_cache:
            await image_cache.set("my_key", image)
    """

    def __init__(self, redis_url: str) -> None:
        """Initialize the image cache.

        Args:
            redis_url: Redis connection URL.
        """
        self._redis_url = redis_url
        self._redis: redis.ConnectionPool | None = None

    @property
    def redis(self) -> redis.ConnectionPool:
        """Get the Redis connection pool."""
        if self._redis is None:
            msg = "Redis connection pool is not initialized. Call connect() first."
            raise RuntimeError(msg)
        return self._redis

    async def set(self, key: str, image: Image.Image) -> None:
        """Cache an image asynchronously.

        Args:
            key: Cache key.
            image: PIL Image to cache.
        """
        try:
            async with redis.Redis(connection_pool=self.redis) as r:
                with io.BytesIO() as output:
                    image.save(output, format="PNG")
                    await r.setex(key, IMAGE_CACHE_TTL, output.getvalue())
        except redis.RedisError as e:
            logger.error(f"Redis error while setting image {key}: {e}")

    async def get(self, key: str) -> Image.Image | None:
        """Get a cached image asynchronously.

        Args:
            key: Cache key.

        Returns:
            The cached PIL Image, or None if not found.
        """
        try:
            async with redis.Redis(connection_pool=self.redis) as r:
                image_data = await r.get(key)
                if image_data is None:
                    return None
        except redis.RedisError as e:
            logger.error(f"Redis error while getting image {key}: {e}")
            return None
        else:
            # Import PIL here to avoid requiring it if not using image cache
            from PIL import Image as PILImage  # pyright: ignore[reportMissingImports]

            return PILImage.open(io.BytesIO(image_data))

    def connect(self) -> None:
        """Initialize the Redis connection pool."""
        logger.info(f"Image cache in PID {os.getpid()} connecting to Redis")
        self._redis = redis.ConnectionPool.from_url(self._redis_url)

    async def disconnect(self) -> None:
        """Close the connection pool."""
        if self._redis is not None:
            await self._redis.aclose()
            logger.info(f"Image cache in PID {os.getpid()} disconnected from Redis")


# Global image cache instance (None if Redis not configured)
image_cache: RedisImageCache | None = (
    RedisImageCache(redis_url=CONFIG.redis_url) if CONFIG.redis_url else None
)
