import logging
from rarapla.logging_config import setup_logging

def test_setup_logging_sets_levels() -> None:
    setup_logging(level=logging.DEBUG)
    assert logging.getLogger('qdarkstyle').level == logging.WARNING
    assert logging.getLogger('aiohttp.access').level == logging.WARNING
