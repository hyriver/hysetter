"""Utility functions for the Hysetter package."""

from __future__ import annotations

import logging
from logging import Logger

from rich.logging import RichHandler

__all__ = ["get_logger"]


def get_logger() -> Logger:
    """Set up Rich Logger and return it."""
    logging.basicConfig(
        level="INFO",
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(rich_tracebacks=True)],
    )

    return logging.getLogger("hysetter")
