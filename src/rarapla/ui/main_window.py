import json
import os
from PySide6.QtCore import QThread, QTimer, Qt
from PySide6.QtGui import QShowEvent
from PySide6.QtWidgets import QComboBox, QGroupBox, QHBoxLayout, QListWidgetItem, QMainWindow, QMessageBox, QVBoxLayout, QWidget
from rarapla.data.radiko_client import RadikoClient
from rarapla.data.radio_browser_client import RadioBrowserClient
from rarapla.models.channel import Channel
from rarapla.ui.controllers.now_refresher import NowRefresher
from rarapla.ui.controllers.playback_controller import PlaybackController
from rarapla.ui.widgets.channel_card import ChannelCard
from rarapla.ui.widgets.detail_panel import DetailPanel
from rarapla.ui.widgets.player_widget import PlayerWidget
from rarapla.ui.widgets.smooth_list import SmoothListWidget
from rarapla.ui.workers.channel_fetch_worker import ChannelFetchWorker
from rarapla.ui.workers.program_fetch_worker import ProgramFetchWorker
from rarapla.ui.workers.rb_search_worker import RBSearchWorker
_DEFAULT_RB_PRESETS: list[dict] = [{'label': 'Japan', 'mode': 'jp'}, {'label': 'J-POP', 'mode': 'tag', 'query': 'jpop'}, {'label': 'Jazz', 'mode': 'tag', 'query': 'jazz'}, {'label': 'Vocaloid', 'mode': 'tag', 'query': 'vocaloid'}]
_PRESET_FILE = 'rb_presets.json'

class MainWindow(QMainWindow):

    def _load_rb_presets(self) -> list[dict]:
        path = os.path.join(os.getcwd(), _PRESET_FILE)
        if not os.path.isfile(path):
            presets = _DEFAULT_RB_PRESETS.copy()
            try:
                with open(path, 'w', encoding='utf-8') as f:
                    json.dump(presets, f, ensure_ascii=False, indent=2)
            except Exception:
                pass
            return presets
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f) or []
        except Exception:
            return _DEFAULT_RB_PRESETS.copy()
        out: list[dict] = []
        for it in data:
            if isinstance(it, dict) and isinstance(it.get('label'), str) and (it.get('mode') in ('jp', 'tag')):
                out.append({'label': it['label'].strip(), 'mode': it['mode'], 'query': (it.get('query') or '').strip() or None})
        return out or _DEFAULT_RB_PRESETS[:1]

    def __init__(self, proxy_host: str, proxy_port: int) -> None:
        super().__init__()
        self.setWindowTitle('RaRaPla')
        self.proxy_base = f'http://{proxy_host}:{proxy_port}'
        self.client = RadikoClient()
        self.rb = RadioBrowserClient()
        self._rb_presets = self._load_rb_presets()
        self._prog_thread: QThread | None = None
        self._prog_worker: ProgramFetchWorker | None = None
        self._populate_thread: QThread | None = None
        self._populate_worker: ChannelFetchWorker | None = None
        self._rb_thread: QThread | None = None
        self._rb_worker: RBSearchWorker | None = None
        self._item_by_id: dict[str, QListWidgetItem] = {}
        self._pending_channel = None
        self._current_channel = None
        self._build_ui()
        self._connect_signals()
        self.playback = PlaybackController(self.player, self.proxy_base)
        self.now = NowRefresher(self.client, interval_ms=5000)
        self.now.updated.connect(self._apply_now_diff)
        self.now.error.connect(self._on_channel_refresh_error)
        self.now.start()
        self.playback.streamTitleChanged.connect(self._on_rb_stream_title)
        self.playback.playbackError.connect(self._on_playback_error)
        self._switch_timer = QTimer(self)
        self._switch_timer.setSingleShot(True)
        self._switch_timer.timeout.connect(self._delayed_channel_switch)
        self._switch_delay_ms = 300
        self._populate()
        QTimer.singleShot(0, self._fix_initial_size)

    def _build_ui(self) -> None:
        root = QWidget()
        self.setCentralWidget(root)
        layout = QHBoxLayout(root)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(12)
        self.detail = DetailPanel(self)
        self.player = PlayerWidget()
        left_col = QVBoxLayout()
        left_col.setContentsMargins(0, 0, 0, 0)
        left_col.setSpacing(12)
        left_col.addWidget(self.detail, 1)
        player_box = QGroupBox('Player')
        pb = QVBoxLayout(player_box)
        pb.setContentsMargins(8, 12, 8, 8)
        pb.addWidget(self.player)
        left_col.addWidget(player_box, 0)
        left_container = QWidget()
        left_container.setLayout(left_col)
        left_container.setFixedWidth(480)
        self.list = SmoothListWidget()
        self.list.setSpacing(8)
        self.source_combo = QComboBox()
        self.source_combo.addItem('radiko (area)')
        for p in self._rb_presets:
            self.source_combo.addItem(f"RB: {p['label']}")
        head = QHBoxLayout()
        head.addWidget(self.source_combo)
        list_box = QGroupBox('Channel')
        lb = QVBoxLayout(list_box)
        lb.setContentsMargins(8, 12, 8, 8)
        lb.addLayout(head)
        lb.addWidget(self.list)
        list_box.setFixedWidth(512)
        layout.addWidget(left_container, 1)
        layout.addWidget(list_box, 1)

    def _connect_signals(self) -> None:
        self.list.currentItemChanged.connect(self._on_select)
        self.player.toggled.connect(self._on_player_toggled)
        self.source_combo.currentIndexChanged.connect(self._on_source_changed)

    def _fix_initial_size(self) -> None:
        from rarapla.config import WINDOW_DEFAULT_HEIGHT, WINDOW_MIN_HEIGHT
        self.setFixedWidth(self.width())
        self.resize(self.width(), WINDOW_DEFAULT_HEIGHT)
        if self.minimumHeight() < WINDOW_MIN_HEIGHT:
            self.setMinimumHeight(WINDOW_MIN_HEIGHT)

    def _on_source_changed(self, idx: int) -> None:
        if idx == 0:
            self._clear_list()
            self._populate()
            self.now.start()
            return
        preset = self._rb_presets[idx - 1]
        self.now.stop()
        self._clear_list()
        self._start_rb_search(mode=preset['mode'], query=preset.get('query'))

    def _populate(self) -> None:
        if self._populate_thread is not None:
            return
        self.statusBar().showMessage('Loading channels...')
        self._populate_worker = ChannelFetchWorker(self.client)
        self._populate_thread = QThread(self)
        w = self._populate_worker
        t = self._populate_thread
        w.moveToThread(t)
        t.started.connect(w.run)
        w.finished.connect(self._on_channels_loaded)
        w.error.connect(self._on_channel_error)
        w.finished.connect(t.quit)
        w.error.connect(t.quit)
        w.finished.connect(w.deleteLater)
        w.error.connect(w.deleteLater)
        t.finished.connect(self._on_populate_thread_finished)
        t.start()

    def _on_populate_thread_finished(self) -> None:
        t = self._populate_thread
        self._populate_thread = None
        self._populate_worker = None
        if t is not None:
            t.deleteLater()

    def _on_channels_loaded(self, channels: list) -> None:
        for ch in channels:
            item = QListWidgetItem(self.list)
            card = ChannelCard(ch)
            item.setSizeHint(card.sizeHint())
            item.setData(Qt.UserRole, ch)
            self.list.addItem(item)
            self.list.setItemWidget(item, card)
            card.setProperty('selected', False)
            self._item_by_id[ch.id] = item
        self.statusBar().showMessage('Channels loaded', 5000)

    def _on_channel_error(self, msg: str) -> None:
        QMessageBox.warning(self, 'Error', msg)
        self.statusBar().showMessage('Failed to load channels', 5000)

    def _clear_list(self) -> None:
        self.list.clear()
        self._item_by_id.clear()

    def _start_rb_search(self, mode: str, query: str | None) -> None:
        if self._rb_thread is not None:
            return
        self.statusBar().showMessage('Loading stations (Radio Browser)...')
        w = RBSearchWorker(self.rb, mode=mode, query=query, limit=100)
        t = QThread(self)
        w.moveToThread(t)
        t.started.connect(w.run)
        w.finished.connect(self._on_rb_loaded)
        w.error.connect(self._on_rb_error)
        w.finished.connect(t.quit)
        w.error.connect(t.quit)
        w.finished.connect(w.deleteLater)
        w.error.connect(w.deleteLater)

        def _cleanup() -> None:
            nonlocal t
            self._rb_thread = None
            self._rb_worker = None
            t.deleteLater()
        t.finished.connect(_cleanup)
        self._rb_thread = t
        self._rb_worker = w
        t.start()

    def _on_rb_loaded(self, channels: list) -> None:
        for ch in channels:
            item = QListWidgetItem(self.list)
            card = ChannelCard(ch)
            item.setSizeHint(card.sizeHint())
            item.setData(Qt.UserRole, ch)
            self.list.addItem(item)
            self.list.setItemWidget(item, card)
            card.setProperty('selected', False)
            self._item_by_id[ch.id] = item
        self.statusBar().showMessage(f'RB: {len(channels)} stations', 5000)

    def _on_rb_error(self, msg: str) -> None:
        QMessageBox.warning(self, 'RB Error', msg)
        self.statusBar().showMessage('Radio Browser request failed', 5000)

    def _on_select(self, cur: QListWidgetItem | None, prev: QListWidgetItem | None) -> None:
        if prev:
            card = self.list.itemWidget(prev)
            if card:
                card.setProperty('selected', False)
                card.style().unpolish(card)
                card.style().polish(card)
                card.update()
        if not cur:
            return
        card = self.list.itemWidget(cur)
        if card:
            card.setProperty('selected', True)
            card.style().unpolish(card)
            card.style().polish(card)
            card.update()
        ch = cur.data(Qt.UserRole)
        self._pending_channel = ch
        self._switch_timer.stop()
        self._switch_timer.start(self._switch_delay_ms)
        if getattr(ch, 'stream_url', None):
            self.detail.set_loading(ch.name)
        else:
            self.detail.set_loading(ch.program_title or '')

    def _delayed_channel_switch(self) -> None:
        ch = self._pending_channel
        if not ch:
            return
        self._current_channel = ch
        if getattr(ch, 'stream_url', None):
            url = ch.stream_url or ''
            if url:
                self.playback.prepare_direct(url)
                try:
                    if ch.id.startswith('rb:'):
                        self.rb.notify_click(ch.id[3:])
                except Exception:
                    pass
                self.detail.set_program(ch.name, '', None)
                self.statusBar().showMessage('Station loaded', 3000)
            return
        self.playback.set_current_station(ch.id)
        if self._prog_worker:
            self._prog_worker.cancel()
        worker = ProgramFetchWorker(self.client, ch)
        thread = QThread(self)
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.finished.connect(self._on_program_loaded)
        worker.error.connect(self._on_program_error)
        worker.cancelled.connect(self._on_program_cancelled)
        worker.finished.connect(thread.quit)
        worker.error.connect(thread.quit)
        worker.cancelled.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)
        worker.error.connect(worker.deleteLater)
        worker.cancelled.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        thread.start()
        self._prog_thread = thread
        self._prog_worker = worker
        QTimer.singleShot(100, lambda: self.playback.prepare_media(ch.id))

    def _on_program_loaded(self, ch, program) -> None:
        cur_item = self.list.currentItem()
        if not cur_item:
            return
        current = cur_item.data(Qt.UserRole)
        if current.id != ch.id:
            return
        title = program.title if program and program.title else ch.program_title
        pieces: list[str] = []
        if program and program.pfm:
            pieces.append(f'<b>出演:</b> {program.pfm}<br><br>')
        if program and program.desc:
            pieces.append(program.desc)
        desc_html = ''.join(pieces) if pieces else ''
        img_url = None
        if program and program.image:
            img_url = program.image
        elif ch.program_image:
            img_url = ch.program_image
        self.detail.set_program(title or '', desc_html, img_url)
        self.statusBar().showMessage('Program loaded', 5000)

    def _on_program_error(self, msg: str) -> None:
        self.detail.set_program('', None, None)
        self.statusBar().showMessage(f'Failed to load program: {msg}', 5000)

    def _on_program_cancelled(self) -> None:
        self.statusBar().showMessage('Program loading cancelled', 2000)

    def _on_channel_refresh_error(self, msg: str) -> None:
        self.statusBar().showMessage(f'Channel refresh failed: {msg}', 3000)

    def _apply_now_diff(self, channels: list) -> None:
        new_map: dict[str, object] = {ch.id: ch for ch in channels}
        cur_item = self.list.currentItem()
        cur_id = cur_item.data(Qt.UserRole).id if cur_item else None
        cur_title_before = cur_item.data(Qt.UserRole).program_title or '' if cur_item else None
        for sid, item in self._item_by_id.items():
            new_ch = new_map.get(sid)
            if not new_ch:
                continue
            old_ch = item.data(Qt.UserRole)
            if old_ch.name != new_ch.name or old_ch.program_title != new_ch.program_title or old_ch.logo_url != new_ch.logo_url:
                item.setData(Qt.UserRole, new_ch)
                card = self.list.itemWidget(item)
                if isinstance(card, ChannelCard):
                    card.update_content(new_ch)
        if cur_item and cur_id:
            updated = self._item_by_id.get(cur_id)
            if updated:
                ch_after = updated.data(Qt.UserRole)
                cur_title_after = ch_after.program_title or ''
                if cur_title_before != cur_title_after:
                    self.detail.set_loading(cur_title_after)
                    self._request_program_detail(ch_after)

    def _request_program_detail(self, ch) -> None:
        if self._prog_worker:
            self._prog_worker.cancel()
        worker = ProgramFetchWorker(self.client, ch)
        thread = QThread(self)
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.finished.connect(self._on_program_loaded)
        worker.error.connect(self._on_program_error)
        worker.cancelled.connect(self._on_program_cancelled)
        worker.finished.connect(thread.quit)
        worker.error.connect(thread.quit)
        worker.cancelled.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)
        worker.error.connect(worker.deleteLater)
        worker.cancelled.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        thread.start()
        self._prog_thread = thread
        self._prog_worker = worker

    def _on_rb_stream_title(self, title: str, meta: object) -> None:
        cur_item = self.list.currentItem()
        if not cur_item:
            return
        ch = cur_item.data(Qt.UserRole)
        if not getattr(ch, 'stream_url', None):
            return
        prog_title = (title or '').strip()
        updated = Channel(id=ch.id, name=ch.name, logo_url=ch.logo_url, program_title=prog_title, program_image=ch.program_image, stream_url=ch.stream_url)
        cur_item.setData(Qt.UserRole, updated)
        card = self.list.itemWidget(cur_item)
        if isinstance(card, ChannelCard):
            card.update_content(updated)
        desc_html = self._format_rb_meta(meta)
        panel_title = prog_title or ch.name
        self.detail.set_program(panel_title, desc_html, None)

    def _format_rb_meta(self, meta: object) -> str:
        try:
            items = dict(meta).items()
        except Exception:
            return ''
        rows: list[str] = []
        for k, v in items:
            ks = str(k).strip()
            vs = str(v).strip()
            if not ks or not vs:
                continue
            ks = ks.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            vs = vs.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            rows.append(f"<tr><td><b>{ks}</b></td><td style='padding-left:8px'>{vs}</td></tr>")
        if not rows:
            return ''
        return "<table cellspacing='0' cellpadding='0'>" + ''.join(rows) + '</table>'

    def _on_player_toggled(self, playing: bool) -> None:
        self.playback.handle_user_toggled(playing)

    def _on_playback_error(self, msg: str) -> None:
        html = f"<span style='color:#e57373; font-weight:bold;'>⚠ 再生できませんでした: {msg}</span>"
        self.detail.set_program(self.detail.title.text(), html, None)
        self.statusBar().showMessage(f'Playback error: {msg}', 7000)

    def showEvent(self, e: QShowEvent) -> None:
        super().showEvent(e)
        if self.minimumHeight() < 512:
            self.setMinimumHeight(512)
