from PySide6.QtCore import QEasingCurve, QElapsedTimer, QPropertyAnimation, Qt
from PySide6.QtGui import QWheelEvent
from PySide6.QtWidgets import QScrollArea, QScroller, QScrollerProperties, QWidget

class SmoothScrollArea(QScrollArea):

    def __init__(self, parent: QWidget | None=None) -> None:
        super().__init__(parent)
        self.setWidgetResizable(True)
        QScroller.grabGesture(self.viewport(), QScroller.LeftMouseButtonGesture)
        props = QScroller.scroller(self.viewport()).scrollerProperties()
        p = QScrollerProperties(props)
        p.setScrollMetric(QScrollerProperties.DecelerationFactor, 0.1)
        p.setScrollMetric(QScrollerProperties.OvershootDragResistanceFactor, 0.15)
        p.setScrollMetric(QScrollerProperties.OvershootScrollDistanceFactor, 0.15)
        p.setScrollMetric(QScrollerProperties.FrameRate, QScrollerProperties.Fps60)
        QScroller.scroller(self.viewport()).setScrollerProperties(p)
        self._anim = QPropertyAnimation(self.verticalScrollBar(), b'value', self)
        self._anim.setEasingCurve(QEasingCurve.OutCubic)
        self._anim.setDuration(140)
        self._pixel_step = 1.0
        self._base_speed = 1.6
        self._min_notch_px = 40
        self._max_notch_px = 320
        self._viewport_ratio = 0.07
        self._accel_timer = QElapsedTimer()
        self._accel_streak = 0
        self._accel_window_ms = 170

    def set_wheel_speed(self, speed: float) -> None:
        self._base_speed = max(0.1, float(speed))

    def set_notch_range(self, min_px: int, max_px: int) -> None:
        self._min_notch_px = max(1, int(min_px))
        self._max_notch_px = max(self._min_notch_px, int(max_px))

    def set_viewport_ratio(self, ratio: float) -> None:
        self._viewport_ratio = max(0.02, min(0.5, float(ratio)))

    def wheelEvent(self, e: QWheelEvent) -> None:
        bar = self.verticalScrollBar()
        if bar.maximum() <= bar.minimum():
            return super().wheelEvent(e)
        cur = bar.value()
        boost = 1.0
        if e.modifiers() & Qt.ShiftModifier:
            boost *= 2.0
        if e.modifiers() & Qt.AltModifier:
            boost *= 3.0
        if self._accel_timer.isValid() and self._accel_timer.elapsed() < self._accel_window_ms:
            self._accel_streak = min(self._accel_streak + 1, 6)
        else:
            self._accel_streak = 0
        self._accel_timer.restart()
        accel_factor = 1.0 + 0.35 * self._accel_streak
        vh = max(1, self.viewport().height())
        notch_px = int(vh * self._viewport_ratio)
        notch_px = max(self._min_notch_px, min(self._max_notch_px, notch_px))
        pd = e.pixelDelta()
        if not pd.isNull():
            delta = -pd.y() * self._pixel_step * self._base_speed * boost * accel_factor
        else:
            steps = e.angleDelta().y() / 120.0
            delta = -steps * notch_px * self._base_speed * boost * accel_factor
        target = int(cur + delta)
        target = max(bar.minimum(), min(bar.maximum(), target))
        dyn_dur = max(60, int(160 / (boost * (1.0 + 0.15 * self._accel_streak))))
        self._anim.stop()
        self._anim.setDuration(dyn_dur)
        self._anim.setStartValue(cur)
        self._anim.setEndValue(target)
        self._anim.start()
        e.accept()
