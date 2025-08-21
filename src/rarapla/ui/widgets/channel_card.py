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
from rarapla.config import USER_AGENT
from rarapla.models.channel import Channel

_ZWSP = "\u200b"


def _soft_wrap_english(text: str, chunk: int = 8) -> str:
    if not text:
        return ""
    pattern = re.compile("[A-Za-z0-9#%&=+@,;:!?\\.\\-_/]{{{n},}}".format(n=chunk))

    def repl(m: re.Match) -> str:
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
        self.setFrameShape(QFrame.StyledPanel)
        root = QHBoxLayout(self)
        root.setContentsMargins(12, 10, 12, 10)
        root.setSpacing(10)
        self.icon = QLabel("●")
        self.icon.setObjectName("ChannelIcon")
        self.icon.setAlignment(Qt.AlignCenter)
        self.icon.setFixedSize(QSize(64, 64))
        self.icon.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        text_box = QVBoxLayout()
        text_box.setContentsMargins(0, 0, 0, 0)
        text_box.setSpacing(4)
        name = _soft_wrap_english(ch.name or "")
        title = _soft_wrap_english(ch.program_title or "")
        self.name_label = QLabel(name)
        self.name_label.setObjectName("ChannelName")
        self.name_label.setTextInteractionFlags(Qt.TextBrowserInteraction)
        self.name_label.setStyleSheet("font-weight: 600;")
        self.name_label.setWordWrap(True)
        self.title_label = QLabel(title)
        self.title_label.setWordWrap(True)
        self.title_label.setTextInteractionFlags(Qt.TextBrowserInteraction)
        text_box.addWidget(self.name_label)
        text_box.addWidget(self.title_label)
        root.addWidget(self.icon)
        root.addLayout(text_box)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        if ch.logo_url:
            self._load_logo(ch.logo_url)
        for child in self.findChildren(QLabel):
            child.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        self.setCursor(Qt.PointingHandCursor)
        for w in self.findChildren(QWidget):
            w.setCursor(Qt.PointingHandCursor)

    def _load_logo(self, url: str) -> None:
        req = QNetworkRequest()
        req.setUrl(QUrl(url))
        req.setRawHeader(b"User-Agent", USER_AGENT.encode("utf-8"))
        reply = self._nam.get(req)
        reply.finished.connect(lambda: self._on_logo_loaded(reply))

    def _on_logo_loaded(self, reply: QNetworkReply) -> None:
        data = reply.readAll()
        b = bytes(data) if isinstance(data, QByteArray) else data
        pix = QPixmap()
        if pix.loadFromData(b):
            self.icon.setPixmap(
                pix.scaled(
                    self.icon.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
                )
            )
        reply.deleteLater()

    def update_content(self, ch: Channel) -> None:
        new_name = _soft_wrap_english(ch.name or "")
        new_title = _soft_wrap_english(ch.program_title or "")
        if self.name_label.text() != new_name:
            self.name_label.setText(new_name)
        if self.title_label.text() != new_title:
            self.title_label.setText(new_title)
        old_logo = self._ch.logo_url or "" if self._ch else ""
        new_logo = ch.logo_url or ""
        if new_logo and new_logo != old_logo:
            self._load_logo(new_logo)
        self._ch = ch
