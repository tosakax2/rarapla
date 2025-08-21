import os
import sys
from textwrap import dedent

from PySide6.QtCore import (
    QLoggingCategory,
    QMessageLogContext,
    QtMsgType,
    qInstallMessageHandler,
)
from PySide6.QtGui import QColor, QFont, QIcon, QPalette
from PySide6.QtWidgets import QApplication
from rarapla.config import PROXY_HOST, PROXY_PORT
from rarapla.logging_config import setup_logging
from rarapla.proxy.radiko_proxy import RadikoProxyServer
from rarapla.ui.main_window import MainWindow

os.environ["QT_LOGGING_RULES"] = ";".join(
    [
        "qt.multimedia.debug=false",
        "qt.multimedia.info=false",
        "qt.multimedia.warning=false",
        "qt.multimedia.ffmpeg.debug=false",
        "qt.multimedia.ffmpeg.info=false",
        "qt.multimedia.ffmpeg.warning=false",
    ]
)


def _qt_msg_filter(
    _msg_type: QtMsgType, _context: QMessageLogContext, message: str
) -> None:
    if message.startswith("[hls @") or message.startswith("[http @"):
        return
    if "qt.multimedia.ffmpeg" in message:
        return


def main() -> None:
    print("=== __main__ started ===")
    setup_logging()
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon("icon.ico"))
    font = QFont("Meiryo UI", 10)
    app.setFont(font)
    QLoggingCategory.setFilterRules(
        "\n".join(
            [
                "qt.multimedia.debug=false",
                "qt.multimedia.info=false",
                "qt.multimedia.warning=false",
                "qt.multimedia.ffmpeg.debug=false",
                "qt.multimedia.ffmpeg.info=false",
                "qt.multimedia.ffmpeg.warning=false",
            ]
        )
    )
    qInstallMessageHandler(_qt_msg_filter)
    try:
        import qdarkstyle

        base = qdarkstyle.load_stylesheet()
        app.setStyleSheet(
            base
            + dedent(
                """
                /* QListWidget のデフォルト矩形ハイライトを消す */
                QListWidget::item:selected {
                    background: transparent;
                }

                /* 通常は枠のみ（完全透明） */
                #ChannelCard {
                    border: 1px solid rgba(255,255,255,0.18);
                    border-radius: 4px;
                    background: transparent;
                }

                /* hover */
                #ChannelCard:hover {
                    border-color: rgba(255,255,255,0.30);
                    background: rgba(255,255,255,0.04);
                }

                /* ダイナミックプロパティ selected=true のときだけ色を付ける */
                #ChannelCard[selected="true"] {
                    border-color: #3daee9;
                    background: rgba(61,174,233,0.2);
                }

                /* ラベルは透過（ロゴ・文字の四角防止） */
                #ChannelCard QLabel {
                    background: transparent;
                }

                #ChannelCard QLabel#ChannelIcon {
                    background: white;
                    border-radius: 4px;
                }

                /* タイトルを太字・大きめ */
                #ChannelCard #ChannelName {
                    font-weight: bold;
                    font-size: 14pt;
                }
                #DetailTitle {
                    font-weight: bold;
                    font-size: 14pt;
                }
                """
            )
        )
    except Exception:
        pass
    pal = app.palette()
    pal.setColor(QPalette.ColorRole.Link, QColor("#5CC9F5"))
    pal.setColor(QPalette.ColorRole.LinkVisited, QColor("#3DAEE9"))
    app.setPalette(pal)
    proxy = RadikoProxyServer(host=PROXY_HOST, port=PROXY_PORT)
    proxy.start_in_thread()
    w = MainWindow(proxy_host=PROXY_HOST, proxy_port=PROXY_PORT)
    w.show()
    code = app.exec()
    proxy.stop()
    sys.exit(code)


if __name__ == "__main__":
    main()
