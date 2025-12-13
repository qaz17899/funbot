"""Pytest fixtures for FunBot tests."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest


@pytest.fixture
def mock_pool() -> MagicMock:
    """Create a mock asyncpg pool."""
    pool = MagicMock()
    pool.acquire = AsyncMock()
    pool.release = AsyncMock()
    pool.close = AsyncMock()
    return pool


@pytest.fixture
def mock_redis() -> MagicMock:
    """Create a mock Redis client."""
    redis = MagicMock()
    redis.get = AsyncMock(return_value=None)
    redis.set = AsyncMock(return_value=True)
    redis.delete = AsyncMock(return_value=1)
    redis.close = AsyncMock()
    return redis


@pytest.fixture
def mock_config() -> MagicMock:
    """Create a mock configuration."""
    config = MagicMock()
    config.discord_token = "test_token"
    config.db_url = "postgresql://test:test@localhost:5432/test"
    config.redis_url = "redis://localhost:6379/0"
    config.env = "test"
    config.is_dev = False
    config.is_prod = False
    return config
