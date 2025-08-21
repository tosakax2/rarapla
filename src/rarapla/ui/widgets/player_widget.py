from PySide6.QtCore import Qt, Signal
from PySide6.QtMultimedia import QAudioDevice, QMediaDevices, QMediaPlayer
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)
from rarapla.services.player_service import PlayerService
from rarapla.config import AUDIO_DEFAULT_VOLUME, AUDIO_MAX_VOLUME, AUDIO_MIN_VOLUME


class PlayerWidget(QWidget):
    toggled = Signal(bool)
    volumeChanged = Signal(int)

    def __init__(self) -> None:
        super().__init__()
        self.svc: PlayerService = PlayerService()
        layout = QVBoxLayout(self)
        self._media_devices = QMediaDevices(self)
        self.dev_label = QLabel("Output:")
        self.dev_combo = QComboBox()
        self.dev_combo.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        dev_row = QHBoxLayout()
        dev_row.addWidget(self.dev_label)
        dev_row.addWidget(self.dev_combo, 1)
        self.vol_label = QLabel("Volume:")
        self.vol = QSlider(Qt.Horizontal)
        self.vol.setRange(AUDIO_MIN_VOLUME, AUDIO_MAX_VOLUME)
        self.vol.setValue(AUDIO_DEFAULT_VOLUME)
        self.svc.set_volume(AUDIO_DEFAULT_VOLUME)
        vol_row = QHBoxLayout()
        vol_row.addWidget(self.vol_label)
        vol_row.addWidget(self.vol, 1)
        ctl = QHBoxLayout()
        self.toggle_btn = QPushButton("Play")
        self.toggle_btn.setCheckable(True)
        ctl.addWidget(self.toggle_btn)
        layout.addLayout(dev_row)
        layout.addLayout(vol_row)
        layout.addSpacing(12)
        layout.addLayout(ctl)
        self.toggle_btn.toggled.connect(self._on_toggled)
        self.vol.valueChanged.connect(self._on_volume)
        self.svc.player.playbackStateChanged.connect(self._on_state)
        self.dev_combo.currentIndexChanged.connect(self._on_device_changed)
        self._media_devices.audioOutputsChanged.connect(self._on_audio_outputs_changed)
        self._refresh_devices(select_current=False)

    def set_media(self, url: str) -> None:
        want_play = self.toggle_btn.isChecked()
        self.svc.set_media(url)
        if want_play:
            self.svc.play()
            self._sync_toggle_to_state(True)
        else:
            self._sync_toggle_to_state(False)

    def _device_id(self, dev: QAudioDevice) -> bytes:
        return bytes(dev.id())

    def _refresh_devices(self, select_current: bool) -> None:
        devs = self._media_devices.audioOutputs()
        self.dev_combo.blockSignals(True)
        self.dev_combo.clear()
        if select_current:
            current = self.svc.audio.device()
        else:
            current = self._media_devices.defaultAudioOutput()
        cur_id = self._device_id(current)
        sel = 0
        for i, d in enumerate(devs):
            self.dev_combo.addItem(d.description(), d)
            if self._device_id(d) == cur_id:
                sel = i
        self.dev_combo.setEnabled(len(devs) > 0)
        self.dev_combo.setCurrentIndex(sel)
        self.dev_combo.blockSignals(False)
        dev = self.dev_combo.currentData()
        if isinstance(dev, QAudioDevice):
            self.svc.set_output_device(dev)

    def _on_device_changed(self, index: int) -> None:
        dev = self.dev_combo.itemData(index)
        if not isinstance(dev, QAudioDevice):
            return
        was_playing = (
            self.svc.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState
        )
        self.svc.set_output_device(dev)
        if was_playing:
            self.svc.play()

    def _on_audio_outputs_changed(self) -> None:
        self._refresh_devices(select_current=True)

    def _on_toggled(self, checked: bool) -> None:
        if not checked:
            self.svc.stop()
        self.toggled.emit(checked)

    def _on_volume(self, v: int) -> None:
        self.svc.set_volume(v)
        self.volumeChanged.emit(v)

    def _on_state(self, state: QMediaPlayer.PlaybackState) -> None:
        if state == QMediaPlayer.PlaybackState.PlayingState:
            self._sync_toggle_to_state(True)
        elif state == QMediaPlayer.PlaybackState.PausedState:
            self._sync_toggle_to_state(True)
        elif state == QMediaPlayer.PlaybackState.StoppedState:
            if not self.toggle_btn.isChecked():
                self._sync_toggle_to_state(False)

    def _sync_toggle_to_state(self, playing: bool) -> None:
        self.toggle_btn.blockSignals(True)
        self.toggle_btn.setChecked(playing)
        self.toggle_btn.setText("Stop" if playing else "Play")
        self.toggle_btn.blockSignals(False)
