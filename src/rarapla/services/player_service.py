from PySide6.QtCore import QUrl
from PySide6.QtMultimedia import QAudioDevice, QAudioOutput, QMediaPlayer
from rarapla.config import AUDIO_MAX_VOLUME, AUDIO_MIN_VOLUME


class PlayerService:

    def __init__(self) -> None:
        self.audio: QAudioOutput = QAudioOutput()
        self.player: QMediaPlayer = QMediaPlayer()
        self.player.setAudioOutput(self.audio)
        self._last_url: str | None = None

    def set_volume(self, vol: int) -> None:
        v = min(max(vol, AUDIO_MIN_VOLUME), AUDIO_MAX_VOLUME)
        self.audio.setVolume(v / AUDIO_MAX_VOLUME)

    def set_media(self, url: str) -> None:
        self._last_url = url
        self.player.setSource(QUrl(url))

    def play(self) -> None:
        if self.player.playbackState() == QMediaPlayer.PlaybackState.StoppedState:
            if self._last_url:
                self.player.setSource(QUrl(self._last_url))
        self.player.play()

    def stop(self) -> None:
        self.player.stop()

    def set_output_device(self, device: QAudioDevice) -> None:
        self.audio.setDevice(device)

    def clear_source(self) -> None:
        self.player.stop()
        self.player.setSource(QUrl())
