from typing import TYPE_CHECKING, Protocol
from PySide6.QtGui import QWheelEvent
from PySide6.QtWidgets import QAbstractItemView, QListWidget, QWidget

if TYPE_CHECKING:

    class SmoothScrollMixin(Protocol):
        def _smooth_wheel_event(self, e: QWheelEvent) -> None: ...

else:
    from .smooth_scroll_mixin import SmoothScrollMixin


class SmoothListWidget(SmoothScrollMixin, QListWidget):

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)

    def wheelEvent(self, e: QWheelEvent) -> None:
        self._smooth_wheel_event(e)
