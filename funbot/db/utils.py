"""Database utilities for common operations.

Provides:
- Query Builder with Tortoise Q
- Raw SQL execution helpers
- Common database utilities
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from tortoise.expressions import Q

if TYPE_CHECKING:
    import asyncpg

__all__ = (
    "build_exclude_query",
    "build_query",
    "execute_raw",
    "fetch_all",
    "fetch_one",
    "fetch_val",
)


def build_query(**kwargs: Any) -> Q:
    """Build a Tortoise Q object from keyword arguments.

    Supports various filter suffixes:
    - __in: Field in list
    - __gt, __gte, __lt, __lte: Comparisons
    - __contains, __icontains: String matching
    - __isnull: Null check

    Args:
        **kwargs: Field filters. Use field__suffix=value for special filters.

    Returns:
        A combined Tortoise Q object.

    Example:
        query = build_query(
            user_id=123,
            status__in=["active", "pending"],
            created_at__gte=datetime(2024, 1, 1),
        )
        results = await Model.filter(query).all()
    """
    return Q(**kwargs)


def build_exclude_query(**kwargs: Any) -> Q:
    """Build an inverted Tortoise Q object (NOT conditions).

    Args:
        **kwargs: Field filters to exclude.

    Returns:
        An inverted Q object.

    Example:
        query = build_exclude_query(status="deleted")
        results = await Model.filter(query).all()  # Excludes deleted
    """
    return ~Q(**kwargs)


# ============================================================================
# Raw SQL Helpers (for performance-critical operations)
# ============================================================================


async def execute_raw(pool: asyncpg.Pool, sql: str, *args: Any) -> str:
    """Execute raw SQL (INSERT, UPDATE, DELETE).

    Args:
        pool: The asyncpg connection pool.
        sql: The SQL query string.
        *args: Query parameters.

    Returns:
        The status string from asyncpg.
    """
    async with pool.acquire() as conn:
        return await conn.execute(sql, *args)


async def fetch_one(pool: asyncpg.Pool, sql: str, *args: Any) -> asyncpg.Record | None:
    """Fetch a single row from the database.

    Args:
        pool: The asyncpg connection pool.
        sql: The SQL query string.
        *args: Query parameters.

    Returns:
        A single record or None.
    """
    async with pool.acquire() as conn:
        return await conn.fetchrow(sql, *args)


async def fetch_all(pool: asyncpg.Pool, sql: str, *args: Any) -> list[asyncpg.Record]:
    """Fetch all matching rows from the database.

    Args:
        pool: The asyncpg connection pool.
        sql: The SQL query string.
        *args: Query parameters.

    Returns:
        A list of records.
    """
    async with pool.acquire() as conn:
        return await conn.fetch(sql, *args)


async def fetch_val(pool: asyncpg.Pool, sql: str, *args: Any, column: int = 0) -> Any:
    """Fetch a single value from the database.

    Args:
        pool: The asyncpg connection pool.
        sql: The SQL query string.
        *args: Query parameters.
        column: The column index to return (default: 0).

    Returns:
        The value from the specified column.
    """
    async with pool.acquire() as conn:
        return await conn.fetchval(sql, *args, column=column)
