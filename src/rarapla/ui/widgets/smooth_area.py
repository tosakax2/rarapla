from typing import TYPE_CHECKING
from PySide6.QtGui import QWheelEvent
from PySide6.QtWidgets import QScrollArea, QWidget

if TYPE_CHECKING:

    class SmoothScrollMixin:
        def _smooth_wheel_event(self, e: QWheelEvent) -> None: ...

else:
    from .smooth_scroll_mixin import SmoothScrollMixin


class SmoothScrollArea(SmoothScrollMixin, QScrollArea):

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWidgetResizable(True)

    def wheelEvent(self, e: QWheelEvent) -> None:
        bar = self.verticalScrollBar()
        if bar.maximum() <= bar.minimum():
            super().wheelEvent(e)
        else:
            self._smooth_wheel_event(e)
