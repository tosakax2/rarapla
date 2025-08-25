from PySide6.QtCore import QByteArray, QSize, QUrl, Qt
from PySide6.QtGui import QPixmap
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)
import re
from rarapla.config import CARD_HEIGHT, USER_AGENT
from rarapla.models.channel import Channel

_ZWSP = "\u200b"


def _soft_wrap_english(text: str, chunk: int = 8) -> str:
    if not text:
        return ""
    pattern = re.compile("[A-Za-z0-9#%&=+@,;:!?\\.\\-_/]{{{n},}}".format(n=chunk))

    def repl(m: re.Match[str]) -> str:
        s = m.group(0)
        parts = [s[i : i + chunk] for i in range(0, len(s), chunk)]
        return _ZWSP.join(parts)

    return pattern.sub(repl, text)


class ChannelCard(QFrame):

    def __init__(self, ch: Channel) -> None:
        super().__init__()
        self._ch: Channel = ch
        self._nam: QNetworkAccessManager = QNetworkAccessManager(self)
        self.setObjectName("ChannelCard")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setFrameShape(QFrame.Shape.StyledPanel)
        root = QHBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        self.icon = QLabel("●")
        self.icon.setObjectName("ChannelIcon")
        self.icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon.setFixedSize(QSize(64, 64))
        self.icon.setSizePolicy(
            QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed
        )
        text_box = QVBoxLayout()
        name = _soft_wrap_english(ch.name or "")
        title = _soft_wrap_english(ch.program_title or "")
        self.name_label = QLabel(name)
        self.name_label.setObjectName("ChannelName")
        self.name_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextBrowserInteraction
        )
        self.name_label.setStyleSheet("font-weight: 600;")
        self.name_label.setText(self._elide(name, 216))
        self.title_label = QLabel(title)
        self.title_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextBrowserInteraction
        )
        self.title_label.setText(self._elide(title, 340))
        self.title_label.setContentsMargins(4, 0, 0, 0)
        text_box.addWidget(self.name_label)
        text_box.addWidget(self.title_label)
        root.addWidget(self.icon)
        root.addLayout(text_box)
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        if ch.logo_url:
            self._load_logo(ch.logo_url)
        for child in self.findChildren(QLabel):
            child.setAttribute(
                Qt.WidgetAttribute.WA_TransparentForMouseEvents, True
            )
        self.setAttribute(
            Qt.WidgetAttribute.WA_TransparentForMouseEvents, False
        )
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        for w in self.findChildren(QWidget):
            w.setCursor(Qt.CursorShape.PointingHandCursor)

    def _load_logo(self, url: str) -> None:
        req = QNetworkRequest()
        req.setUrl(QUrl(url))
        req.setRawHeader(b"User-Agent", USER_AGENT.encode("utf-8"))
        reply = self._nam.get(req)
        reply.finished.connect(lambda: self._on_logo_loaded(reply))

    def _on_logo_loaded(self, reply: QNetworkReply) -> None:
        data = reply.readAll()
        b = data.data() if isinstance(data, QByteArray) else data
        pix = QPixmap()
        if pix.loadFromData(b):
            self.icon.setPixmap(
                pix.scaled(
                    self.icon.size(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
        reply.deleteLater()

    def _elide(self, text: str, width_limit: int = 320) -> str:
        fm = self.fontMetrics()
        return fm.elidedText(text, Qt.TextElideMode.ElideRight, width_limit)

    def update_content(self, ch: Channel) -> None:
        new_name = self._elide(_soft_wrap_english(ch.name or ""), 216)
        new_title = self._elide(_soft_wrap_english(ch.program_title or ""), 340)
        if self.name_label.text() != new_name:
            self.name_label.setText(new_name)
        if self.title_label.text() != new_title:
            self.title_label.setText(new_title)
        old_logo = self._ch.logo_url or "" if self._ch else ""
        new_logo = ch.logo_url or ""
        if new_logo and new_logo != old_logo:
            self._load_logo(new_logo)
        self._ch = ch

    def sizeHint(self) -> QSize:
        s = super().sizeHint()
        return QSize(s.width(), CARD_HEIGHT)
