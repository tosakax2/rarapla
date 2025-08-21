"""Logging utilities for the application.

Provides helpers to configure the Python logging module with sane defaults.
"""

import logging


def setup_logging(level: int = logging.INFO) -> None:
    """Configure logging for the application.

    Args:
        level: Minimum log level to emit.
    """
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    logging.getLogger("aiohttp.access").setLevel(logging.WARNING)
    logging.getLogger("qdarkstyle").setLevel(logging.WARNING)
