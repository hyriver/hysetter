"""Utility functions for the Hysetter package."""
import logging
from rich.logging import RichHandler
from logging import Logger

__all__ = ["get_logger"]

def get_logger()->Logger:
    """Set up Rich Logger and return it."""
    logging.basicConfig(
        level="INFO", format="%(message)s", datefmt="[%X]", handlers=[RichHandler(rich_tracebacks=True)]
    )

    return logging.getLogger("hysetter")
