from PySide6.QtCore import QObject, Signal
from rarapla.data.radiko_client import RadikoClient
from rarapla.models.channel import Channel


class ProgramFetchWorker(QObject):
    finished = Signal(object, object)
    error = Signal(str)
    cancelled = Signal()

    def __init__(self, client: RadikoClient, ch: Channel) -> None:
        super().__init__()
        self._client = client
        self._ch = ch
        self._cancelled = False

    def cancel(self) -> None:
        self._cancelled = True

    def run(self) -> None:
        if self._cancelled:
            self.cancelled.emit()
            return
        try:
            program = self._client.fetch_program_detail(self._ch.id)
            if self._cancelled:
                self.cancelled.emit()
            else:
                self.finished.emit(self._ch, program)
        except Exception as e:
            if self._cancelled:
                self.cancelled.emit()
            else:
                self.error.emit(str(e))
