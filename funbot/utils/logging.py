"""Logging configuration with loguru."""

from __future__ import annotations

import inspect
import logging
import sys

from loguru import logger

from funbot.config import CONFIG

__all__ = ("InterceptHandler", "setup_logging")


class InterceptHandler(logging.Handler):
    """Redirect standard logging to loguru.

    This allows all libraries using standard logging to be captured by loguru.
    """

    def emit(self, record: logging.LogRecord) -> None:
        """Intercept log records and forward to loguru."""
        # Get corresponding Loguru level if it exists
        level: str | int
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where originated the logged message
        frame, depth = inspect.currentframe(), 0
        while frame and (depth == 0 or frame.f_code.co_filename == logging.__file__):
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


def setup_logging(log_file: str = "logs/funbot.log") -> None:
    """Configure loguru with console and file logging.

    Args:
        log_file: Path to the log file.
    """
    # Remove default handler
    logger.remove()

    # Add console handler
    log_level = "DEBUG" if CONFIG.is_dev else "INFO"
    logger.add(
        sys.stderr,
        level=log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    )

    # Add file handler with rotation
    logger.add(log_file, rotation="2 hours", retention="1 week", level="DEBUG", compression="gz")

    # Redirect standard logging to loguru
    logging.basicConfig(handlers=[InterceptHandler()], level=logging.INFO, force=True)

    # Suppress noisy loggers
    for logger_name in ("discord", "discord.http", "discord.gateway"):
        logging.getLogger(logger_name).setLevel(logging.WARNING)

    logger.info(f"Logging initialized (level: {log_level})")
