"""Custom exceptions for the bot."""

from __future__ import annotations


class FunBotError(Exception):
    """Base exception for FunBot errors."""

    def __init__(self, message: str = "An error occurred") -> None:
        self.message = message
        super().__init__(self.message)


class ConfigurationError(FunBotError):
    """Raised when there's a configuration issue."""


class DatabaseError(FunBotError):
    """Raised when there's a database operation error."""


class CacheError(FunBotError):
    """Raised when there's a cache operation error."""


class UserNotFoundError(FunBotError):
    """Raised when a user is not found in the database."""

    def __init__(self, user_id: int) -> None:
        super().__init__(f"User with ID {user_id} not found")
        self.user_id = user_id


class CogLoadError(FunBotError):
    """Raised when a cog fails to load."""

    def __init__(self, cog_name: str, reason: str) -> None:
        super().__init__(f"Failed to load cog '{cog_name}': {reason}")
        self.cog_name = cog_name
        self.reason = reason
