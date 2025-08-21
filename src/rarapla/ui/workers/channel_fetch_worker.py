from PySide6.QtCore import QObject, Signal
from rarapla.data.radiko_client import RadikoClient

class ChannelFetchWorker(QObject):
    finished = Signal(list)
    error = Signal(str)

    def __init__(self, client: RadikoClient) -> None:
        super().__init__()
        self._client = client

    def run(self) -> None:
        try:
            area = self._client.get_area_id()
            channels = self._client.fetch_now_programs(area)
            self.finished.emit(channels)
        except Exception as e:
            self.error.emit(str(e))
