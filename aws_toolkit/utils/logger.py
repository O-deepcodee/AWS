"""
Logging utilities for AWS Toolkit.
"""

import logging
import sys
from typing import Optional


def get_logger(name: str, level: Optional[str] = None) -> logging.Logger:
    """Get a configured logger.

    Args:
        name: Logger name
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)

    # Set level
    if level:
        logger.setLevel(getattr(logging, level.upper()))
    elif not logger.handlers:
        logger.setLevel(logging.INFO)

    # Add handler if none exists
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


def setup_logging(level: str = "INFO", format_string: Optional[str] = None):
    """Setup global logging configuration.

    Args:
        level: Global logging level
        format_string: Custom format string
    """
    if format_string is None:
        format_string = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    logging.basicConfig(
        level=getattr(logging, level.upper()), format=format_string, stream=sys.stdout
    )
