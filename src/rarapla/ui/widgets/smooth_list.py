from PySide6.QtGui import QWheelEvent
from PySide6.QtWidgets import QAbstractItemView, QListWidget, QWidget

from .smooth_scroll_mixin import SmoothScrollMixin


class SmoothListWidget(SmoothScrollMixin, QListWidget):

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)

    def wheelEvent(self, e: QWheelEvent) -> None:
        self._smooth_wheel_event(e)
