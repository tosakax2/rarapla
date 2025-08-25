from collections.abc import Callable
from PySide6.QtCore import QByteArray, QObject, QUrl
from PySide6.QtGui import QPixmap
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest
from rarapla.config import USER_AGENT


class ImageLoader(QObject):

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._nam: QNetworkAccessManager = QNetworkAccessManager(self)
        self._reply: QNetworkReply | None = None

    def load(
        self,
        url: str,
        on_done: Callable[[QPixmap], None],
        on_error: Callable[[], None] | None = None,
        scale_to_width: int | None = None,
    ) -> None:
        self._cleanup_reply()
        req = QNetworkRequest()
        req.setUrl(QUrl(url))
        req.setRawHeader(b"User-Agent", USER_AGENT.encode("utf-8"))
        self._reply = self._nam.get(req)

        def _finished() -> None:
            reply = self._reply
            self._reply = None
            if not isinstance(reply, QNetworkReply):
                if on_error:
                    on_error()
                return
            data = reply.readAll()
            b = data.data() if isinstance(data, QByteArray) else data
            reply.deleteLater()
            pix = QPixmap()
            if not pix.loadFromData(b) or pix.isNull():
                if on_error:
                    on_error()
                return
            if scale_to_width and scale_to_width > 0:
                pix = pix.scaledToWidth(scale_to_width)
            on_done(pix)

        self._reply.finished.connect(_finished)

    def cancel(self) -> None:
        self._cleanup_reply()

    def _cleanup_reply(self) -> None:
        reply = self._reply
        if reply is not None:
            try:
                reply.finished.disconnect()
            except Exception:
                pass
            reply.abort()
            reply.deleteLater()
            self._reply = None
