"""Startup utilities for the bot."""

from __future__ import annotations

import asyncio
import sys

__all__ = ("setup_async_event_loop",)


def setup_async_event_loop() -> None:
    """Configure the async event loop for the current platform.

    On Windows, this sets the appropriate event loop policy.
    """
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
