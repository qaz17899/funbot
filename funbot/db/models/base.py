"""Base model classes for database models.

Provides:
- BaseModel: Enhanced repr for all models
- CachedModel: Automatic Redis caching for get/save/delete operations
"""

from __future__ import annotations

import asyncio
import hashlib
from typing import Any, ClassVar, Self

import orjson
import redis.asyncio as redis
from loguru import logger
from tortoise.models import Model

from funbot.config import CONFIG

__all__ = ("BaseModel", "CachedModel")


class BaseModel(Model):
    """Enhanced base model with better repr.

    All models should inherit from this class for consistent behavior.
    """

    def __str__(self) -> str:
        return repr(self)

    def __repr__(self) -> str:
        fields = ", ".join(
            f"{field}={getattr(self, field)!r}"
            for field in self._meta.db_fields
            if hasattr(self, field)
        )
        return f"{self.__class__.__name__}({fields})"

    class Meta:
        abstract = True


class CachedModel(BaseModel):
    """Base model with automatic Redis caching.

    Subclasses must define `_pks` tuple with the primary key field names
    used for cache key generation.

    Usage:
        class User(CachedModel):
            _pks = ("id",)
            _cache_ttl = 3600  # Optional, default is 1 hour

            id = fields.BigIntField(pk=True)
            username = fields.CharField(max_length=100)

        # Now get/get_or_none/save/delete will automatically use Redis cache
        user = await User.get(id=12345)
    """

    _redis_pool: ClassVar[redis.ConnectionPool | None] = None
    _cache_ttl: ClassVar[int] = 3600  # 1 hour default
    _pks: ClassVar[tuple[str, ...]] = ()

    class Meta:
        abstract = True

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        if not self._pks:
            msg = f"{self.__class__.__name__} has no primary keys defined for caching"
            raise ValueError(msg)
        super().__init__(*args, **kwargs)

    @classmethod
    async def _get_redis(cls) -> redis.Redis | None:
        """Get async Redis connection from pool."""
        if not CONFIG.redis_url:
            return None

        if cls._redis_pool is None:
            try:
                cls._redis_pool = redis.ConnectionPool.from_url(
                    CONFIG.redis_url,
                    decode_responses=True,
                    retry_on_timeout=True,
                    socket_keepalive=True,
                )
            except Exception as e:
                logger.error(f"Failed to create Redis connection pool: {e}")
                return None

        try:
            return redis.Redis(connection_pool=cls._redis_pool)
        except Exception as e:
            logger.error(f"Failed to get Redis connection: {e}")
            return None

    @classmethod
    def _get_cache_key(cls, **kwargs: Any) -> str:
        """Generate cache key from primary key values."""
        strings = (f"{pk}={kwargs.get(pk)}" for pk in cls._pks)
        joined = "\0".join(strings)
        hash_obj = hashlib.sha256(joined.encode())
        return f"{cls.__name__}:{hash_obj.hexdigest()}"

    def serialize(self) -> dict[str, Any]:
        """Serialize model instance for caching."""
        return {
            field: getattr(self, field) for field in self._meta.db_fields if hasattr(self, field)
        }

    @classmethod
    def _deserialize(cls, data: dict[str, Any]) -> dict[str, Any]:
        """Deserialize cached data for model creation.

        Override in subclass to handle special field types.
        """
        return data

    async def _cache_set(self) -> None:
        """Cache this instance in Redis."""
        redis_conn = await self._get_redis()
        if not redis_conn:
            return

        try:
            kwargs = {pk: getattr(self, pk) for pk in self._pks}
            cache_key = self._get_cache_key(**kwargs)
            serialized_data = self.serialize()
            json_data = orjson.dumps(serialized_data).decode("utf-8")
            await redis_conn.setex(cache_key, self._cache_ttl, json_data)
        except Exception:
            logger.exception(f"Failed to cache {self.__class__.__name__} instance")
        finally:
            await redis_conn.aclose()

    async def _cache_delete(self) -> None:
        """Delete this instance from Redis cache."""
        redis_conn = await self._get_redis()
        if not redis_conn:
            return

        try:
            kwargs = {pk: getattr(self, pk) for pk in self._pks}
            cache_key = self._get_cache_key(**kwargs)
            await redis_conn.delete(cache_key)
        except Exception:
            logger.exception(f"Failed to delete cache for {self.__class__.__name__}")
        finally:
            await redis_conn.aclose()

    @classmethod
    async def _cache_get(cls, **kwargs: Any) -> dict[str, Any] | None:
        """Get cached data from Redis."""
        redis_conn = await cls._get_redis()
        if not redis_conn:
            return None

        try:
            cache_key = cls._get_cache_key(**kwargs)
            cached_data = await redis_conn.get(cache_key)

            if cached_data is None:
                return None

            return orjson.loads(cached_data)  # type: ignore[arg-type]
        except Exception:
            logger.exception(f"Failed to get cache for {cls.__name__}")
            return None
        finally:
            await redis_conn.aclose()

    @classmethod
    async def get(cls, *args: Any, **kwargs: Any) -> Self:
        """Get model instance, checking Redis cache first."""
        # Try cache first
        cached_data = await cls._cache_get(**kwargs)
        if cached_data is not None:
            try:
                deserialized_data = cls._deserialize(cached_data)
                return cls._init_from_db(**deserialized_data)
            except Exception as e:
                logger.error(f"Failed to deserialize cached {cls.__name__}: {e}")

        # Fallback to database
        instance = await super().get(*args, **kwargs)
        asyncio.create_task(instance._cache_set())
        return instance

    @classmethod
    async def get_or_none(cls, *args: Any, **kwargs: Any) -> Self | None:
        """Get model instance or None, checking Redis cache first."""
        # Try cache first
        cached_data = await cls._cache_get(**kwargs)
        if cached_data is not None:
            try:
                deserialized_data = cls._deserialize(cached_data)
                return cls._init_from_db(**deserialized_data)
            except Exception as e:
                logger.error(f"Failed to deserialize cached {cls.__name__}: {e}")

        # Fallback to database
        instance = await super().get_or_none(*args, **kwargs)
        if instance is not None:
            asyncio.create_task(instance._cache_set())
        return instance

    async def save(self, *args: Any, **kwargs: Any) -> None:
        """Save model instance and update Redis cache."""
        await super().save(*args, **kwargs)
        asyncio.create_task(self._cache_set())

    async def delete(self) -> None:
        """Delete model instance and remove from Redis cache."""
        await self._cache_delete()
        await super().delete()

    @classmethod
    async def close_redis_pool(cls) -> None:
        """Close the Redis connection pool."""
        if cls._redis_pool is not None:
            await cls._redis_pool.aclose()
            cls._redis_pool = None
            logger.info("Redis connection pool closed")
