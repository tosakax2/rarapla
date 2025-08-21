import os
import sys
from PySide6.QtCore import QLoggingCategory, QMessageLogContext, QtMsgType, qInstallMessageHandler
from PySide6.QtGui import QColor, QFont, QIcon, QPalette
from PySide6.QtWidgets import QApplication
from rarapla.config import PROXY_HOST, PROXY_PORT
from rarapla.logging_config import setup_logging
from rarapla.proxy.radiko_proxy import RadikoProxyServer
from rarapla.ui.main_window import MainWindow
os.environ['QT_LOGGING_RULES'] = ';'.join(['qt.multimedia.debug=false', 'qt.multimedia.info=false', 'qt.multimedia.warning=false', 'qt.multimedia.ffmpeg.debug=false', 'qt.multimedia.ffmpeg.info=false', 'qt.multimedia.ffmpeg.warning=false'])

def _qt_msg_filter(_msg_type: QtMsgType, _context: QMessageLogContext, message: str) -> None:
    if message.startswith('[hls @') or message.startswith('[http @'):
        return
    if 'qt.multimedia.ffmpeg' in message:
        return

def main() -> None:
    setup_logging()
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon('icon.ico'))
    font = QFont('Meiryo UI', 10)
    app.setFont(font)
    QLoggingCategory.setFilterRules('qt.multimedia.debug=false\nqt.multimedia.info=false\nqt.multimedia.warning=false\nqt.multimedia.ffmpeg.debug=false\nqt.multimedia.ffmpeg.info=false\nqt.multimedia.ffmpeg.warning=false\n')
    qInstallMessageHandler(_qt_msg_filter)
    try:
        import qdarkstyle
        base = qdarkstyle.load_stylesheet()
        app.setStyleSheet(base + '\n            /* QListWidget のデフォルト矩形ハイライトを消す */\n            QListWidget::item:selected {\n                background: transparent;\n            }\n\n            /* 通常は枠のみ（完全透明） */\n            #ChannelCard {\n                border: 1px solid rgba(255,255,255,0.18);\n                border-radius: 4px;\n                background: transparent;\n            }\n\n            /* hover */\n            #ChannelCard:hover {\n                border-color: rgba(255,255,255,0.30);\n                background: rgba(255,255,255,0.04);\n            }\n\n            /* ダイナミックプロパティ selected=true のときだけ色を付ける */\n            #ChannelCard[selected="true"] {\n                border-color: #3daee9;\n                background: rgba(61,174,233,0.2);\n            }\n\n            /* ラベルは透過（ロゴ・文字の四角防止） */\n            #ChannelCard QLabel {\n                background: transparent;\n            }\n\n            #ChannelCard QLabel#ChannelIcon {\n                background: white;\n                border-radius: 4px;\n            }\n\n            /* タイトルを太字・大きめ */\n            #ChannelCard #ChannelName {\n                font-weight: bold;\n                font-size: 14pt;\n            }\n            #DetailTitle {\n                font-weight: bold;\n                font-size: 14pt;\n            }\n            ')
    except Exception:
        pass
    pal = app.palette()
    pal.setColor(QPalette.ColorRole.Link, QColor('#5CC9F5'))
    pal.setColor(QPalette.ColorRole.LinkVisited, QColor('#3DAEE9'))
    app.setPalette(pal)
    proxy = RadikoProxyServer(host=PROXY_HOST, port=PROXY_PORT)
    proxy.start_in_thread()
    w = MainWindow(proxy_host=PROXY_HOST, proxy_port=PROXY_PORT)
    w.show()
    code = app.exec()
    proxy.stop()
    sys.exit(code)
