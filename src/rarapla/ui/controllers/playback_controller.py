from PySide6.QtCore import QObject, QTimer, Signal
from PySide6.QtMultimedia import QMediaPlayer, QMediaMetaData
from rarapla.config import USER_AGENT
from rarapla.ui.widgets.player_widget import PlayerWidget
from rarapla.services.icy_watcher import IcyWatcher


class PlaybackController(QObject):
    streamTitleChanged = Signal(str, object)
    playbackError = Signal(str)

    def __init__(self, player: PlayerWidget, proxy_base: str) -> None:
        super().__init__(player)
        self.player = player
        self.proxy_base: str = proxy_base
        self._current_station: str | None = None
        self._current_direct_url: str | None = None
        self._icy: IcyWatcher | None = None
        self._refresh_timer = QTimer(self)
        self._refresh_timer.setInterval(4 * 60 * 1000)
        self._refresh_timer.timeout.connect(self._refresh_stream)
        self.player.svc.player.metaDataChanged.connect(self._on_meta_changed)
        self.player.svc.player.errorOccurred.connect(self._on_player_error)

    def set_current_station(self, station_id: str | None) -> None:
        self._current_station = station_id
        if station_id is not None:
            self._current_direct_url = None
            self._stop_icy_watch()

    def prepare_media(self, station_id: str) -> None:
        self.set_current_station(station_id)
        self._clear_proxy_cache(station_id)
        url = self._build_local_m3u8(station_id, force=True)
        self.player.set_media(url)
        self._refresh_timer.start()

    def prepare_direct(self, url: str) -> None:
        self._current_station = None
        self._current_direct_url = url
        self._refresh_timer.stop()
        self._start_icy_watch(url)
        self.player.set_media(url)

    def handle_user_toggled(self, playing: bool) -> None:
        if not playing:
            return
        if self._current_station:
            sid = self._current_station
            self._clear_proxy_cache(sid)
            self.player.svc.clear_source()
            url = self._build_local_m3u8(sid, force=True)
            self.player.set_media(url)
            self.player.svc.play()
            return
        if self._current_direct_url:
            self.player.svc.clear_source()
            self.player.set_media(self._current_direct_url)
            self.player.svc.play()

    def shutdown(self) -> None:
        self._refresh_timer.stop()
        self._stop_icy_watch()
        try:
            self.player.svc.stop()
            self.player.svc.clear_source()
        except Exception:
            pass

    def _build_local_m3u8(self, station_id: str, force: bool = False) -> str:
        base = f"{self.proxy_base}/live/{station_id}.m3u8"
        if force:
            import time

            return f"{base}?t={int(time.time() * 1000)}"
        return base

    def _refresh_stream(self) -> None:
        if not self._current_station:
            return
        if (
            self.player.svc.player.playbackState()
            != QMediaPlayer.PlaybackState.PlayingState
        ):
            return
        try:
            import requests

            requests.post(
                f"{self.proxy_base}/clear_cache",
                json={"station": self._current_station},
                timeout=2,
            )
        except Exception:
            pass

    def _on_meta_changed(self) -> None:
        if self._current_direct_url is not None:
            return
        md = self.player.svc.player.metaData()
        if md.isEmpty():
            return
        title = self._first_non_empty(
            md.stringValue(QMediaMetaData.Title),
            md.stringValue(QMediaMetaData.Description),
            md.stringValue(QMediaMetaData.Comment),
        ).strip()

        def _val(name: str) -> str | None:
            key = getattr(QMediaMetaData, name, None)
            if key is None:
                return None
            try:
                s = md.stringValue(key)
            except Exception:
                s = None
            if s:
                s = s.strip()
            return s or None

        pairs: list[tuple[str, str]] = []

        def add(label: str, name: str) -> None:
            v = _val(name)
            if v:
                pairs.append((label, v))

        add("Title", "Title")
        add("Artist", "Author")
        add("Album", "AlbumTitle")
        add("AlbumArtist", "AlbumArtist")
        add("Genre", "Genre")
        add("Comment", "Comment")
        add("Description", "Description")
        add("Publisher", "Publisher")
        add("Language", "Language")
        add("Track", "TrackNumber")
        add("Date", "Date")
        meta_map: dict[str, str] = {k: v for k, v in pairs}
        if title or meta_map:
            self.streamTitleChanged.emit(title, meta_map)

    def _start_icy_watch(self, url: str) -> None:
        self._stop_icy_watch()
        self._icy = IcyWatcher(url=url, user_agent=USER_AGENT)
        self._icy.metaUpdated.connect(self._on_icy_meta)
        self._icy.notSupported.connect(self._on_icy_not_supported)
        self._icy.networkError.connect(self._on_icy_error)
        self._icy.start()

    def _stop_icy_watch(self) -> None:
        if self._icy is None:
            return
        try:
            self._icy.metaUpdated.disconnect(self._on_icy_meta)
            self._icy.notSupported.disconnect(self._on_icy_not_supported)
            self._icy.networkError.disconnect(self._on_icy_error)
        except Exception:
            pass
        self._icy.stop()
        self._icy.wait(3000)
        self._icy = None

    def _on_icy_meta(self, title: str, meta: dict) -> None:
        self.streamTitleChanged.emit(title, meta)

    def _on_icy_not_supported(self, reason: str) -> None:
        pass

    def _on_icy_error(self, message: str) -> None:
        pass

    def _on_player_error(self, err: QMediaPlayer.Error, text: str) -> None:
        if err == QMediaPlayer.NoError:
            return
        msg = text or "再生できませんでした"
        self.playbackError.emit(msg)

    def _first_non_empty(self, *values: str | None) -> str:
        for v in values:
            if v and v.strip():
                return v
        return ""

    def _clear_proxy_cache(self, station_id: str) -> None:
        import requests

        try:
            requests.post(
                f"{self.proxy_base}/clear_cache",
                json={"station": station_id},
                timeout=2,
            )
        except Exception:
            pass
