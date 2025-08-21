from PySide6.QtCore import Qt
from PySide6.QtWidgets import QGroupBox, QLabel, QVBoxLayout, QWidget
from rarapla.ui.utils.image_loader import ImageLoader
from rarapla.ui.widgets.smooth_area import SmoothScrollArea

class DetailPanel(QGroupBox):

    def __init__(self, parent: QWidget | None=None) -> None:
        super().__init__('Detail', parent)
        self._img_loader = ImageLoader(self)
        self.title = QLabel('')
        self.title.setObjectName('DetailTitle')
        self.title.setWordWrap(True)
        self.title.setTextInteractionFlags(Qt.TextBrowserInteraction)
        self.image = QLabel()
        self.image.setAlignment(Qt.AlignCenter)
        self.image.setMinimumHeight(180)
        self.image.setVisible(False)
        self.desc = QLabel('')
        self.desc.setWordWrap(True)
        self.desc.setTextFormat(Qt.RichText)
        self.desc.setTextInteractionFlags(Qt.TextBrowserInteraction)
        self.desc.setOpenExternalLinks(True)
        scroll_body = QWidget()
        body_layout = QVBoxLayout(scroll_body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(8)
        body_layout.addWidget(self.image)
        body_layout.addWidget(self.desc)
        body_layout.addStretch()
        self.scroll = SmoothScrollArea(self)
        self.scroll.setWidget(scroll_body)
        box = QVBoxLayout(self)
        box.setContentsMargins(8, 12, 8, 8)
        box.setSpacing(8)
        box.addWidget(self.title)
        box.addWidget(self.scroll, 1)

    def set_loading(self, title_text: str) -> None:
        self.title.setText(title_text or '')
        self.desc.setText('読み込み中...')
        self._clear_image()

    def set_program(self, title_text: str, desc_html: str | None, image_url: str | None) -> None:
        self.title.setText(title_text or '')
        self.desc.setText(desc_html or '')
        if image_url:
            self._load_image(image_url)
        else:
            self._clear_image()

    def _clear_image(self) -> None:
        self.image.clear()
        self.image.setVisible(False)

    def _load_image(self, url: str) -> None:

        def _done(pix):
            fixed = 340
            scaled = pix if pix.width() == fixed else pix.scaledToWidth(fixed, Qt.SmoothTransformation)
            self.image.setPixmap(scaled)
            self.image.setFixedSize(fixed, scaled.height())
            self.image.setVisible(True)

        def _err():
            self._clear_image()
        self._img_loader.load(url, on_done=_done, on_error=_err, scale_to_width=340)
