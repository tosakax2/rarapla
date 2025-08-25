"""Logging utilities for the application.

Provides helpers to configure the Python logging module with sane defaults.
"""

import logging


def setup_logging(level: int = logging.INFO, log_file: str | None = None) -> None:
    """Configure logging for the application.

    Args:
        level: Minimum log level to emit.
        log_file: Optional path of a file to also receive log output.
    """
    handlers: list[logging.Handler] = [logging.StreamHandler()]
    if log_file is not None:
        handlers.append(logging.FileHandler(log_file, encoding="utf-8"))
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s:%(lineno)d: %(message)s",
        handlers=handlers,
        force=True,
    )
    logging.getLogger("aiohttp.access").setLevel(logging.WARNING)
    logging.getLogger("qdarkstyle").setLevel(logging.WARNING)
