import logging

def setup_logging(level: int=logging.INFO) -> None:
    logging.basicConfig(level=level, format='%(asctime)s %(levelname)s %(name)s: %(message)s')
    logging.getLogger('aiohttp.access').setLevel(logging.WARNING)
    logging.getLogger('qdarkstyle').setLevel(logging.WARNING)
