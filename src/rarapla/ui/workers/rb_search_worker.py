from PySide6.QtCore import QObject, Signal
from rarapla.data.radio_browser_client import RadioBrowserClient

class RBSearchWorker(QObject):
    finished = Signal(list)
    error = Signal(str)

    def __init__(self, client: RadioBrowserClient, mode: str='jp', query: str | None=None, limit: int=100) -> None:
        super().__init__()
        self._cli = client
        self._mode = mode
        self._query = query
        self._limit = limit

    def run(self) -> None:
        try:
            if self._mode == 'tag':
                tag = (self._query or '').strip()
                chs = self._cli.search_by_tag(tag or 'vocaloid', self._limit)
            else:
                chs = self._cli.search_japan(self._limit)
            self.finished.emit(chs)
        except Exception as e:
            self.error.emit(str(e))
