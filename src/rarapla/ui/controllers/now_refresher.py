from PySide6.QtCore import QObject, QThread, QTimer, Signal
from rarapla.data.radiko_client import RadikoClient
from rarapla.ui.workers.channel_fetch_worker import ChannelFetchWorker


class NowRefresher(QObject):
    updated = Signal(list)
    error = Signal(str)

    def __init__(self, client: RadikoClient, interval_ms: int = 5000) -> None:
        super().__init__()
        self._client = client
        self._timer = QTimer(self)
        self._timer.setInterval(interval_ms)
        self._timer.timeout.connect(self._tick)
        self._thread: QThread | None = None
        self._worker: ChannelFetchWorker | None = None
        self._busy = False

    def start(self) -> None:
        self._timer.start()

    def stop(self) -> None:
        self._timer.stop()

    def _tick(self) -> None:
        if self._busy or self._thread is not None:
            return
        self._busy = True
        self._worker = ChannelFetchWorker(self._client)
        self._thread = QThread()
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)

        def _done(chs: list) -> None:
            self.updated.emit(chs)
            self._thread.quit()

        def _err(msg: str) -> None:
            self.error.emit(msg)
            self._thread.quit()

        self._worker.finished.connect(_done)
        self._worker.error.connect(_err)

        def _cleanup() -> None:
            try:
                if self._worker is not None:
                    self._worker.deleteLater()
            finally:
                self._worker = None
                t = self._thread
                self._thread = None
                self._busy = False
                if t is not None:
                    t.deleteLater()

        self._thread.finished.connect(_cleanup)
        self._thread.start()
