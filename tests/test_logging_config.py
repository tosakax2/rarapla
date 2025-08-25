import logging
import re
from pathlib import Path

from rarapla.logging_config import setup_logging


def test_setup_logging_sets_levels() -> None:
    setup_logging(level=logging.DEBUG)
    assert logging.getLogger("qdarkstyle").level == logging.WARNING
    assert logging.getLogger("aiohttp.access").level == logging.WARNING


def test_setup_logging_logs_to_file(tmp_path: Path) -> None:
    log_file = tmp_path / "test.log"
    setup_logging(level=logging.INFO, log_file=str(log_file))
    logger = logging.getLogger("test_logger")
    logger.info("hello")
    contents = log_file.read_text()
    assert "test_logger" in contents
    assert re.search(r"test_logger:\d+: hello", contents) is not None
