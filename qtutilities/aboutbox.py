import sys
from asyncio import QueueEmpty
from collections import namedtuple

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QWidget, QApplication
)
from PySide6.QtCore import  Qt
from PySide6.QtGui import QPixmap, QDesktopServices, QFont

AboutParams = namedtuple('AboutParams', 'icon title version repo_url repo_text')

DEFAULT_PARAMS = AboutParams('', 'Application', '1.0', '', '')

class AboutBox(QDialog):
    def __init__(self, parent: QWidget | None = None,
                 app_params: AboutParams = DEFAULT_PARAMS,
                 size: tuple[int, int] = (400, 300)):
        super().__init__(parent)
        self.setWindowTitle("About")
        self.setFixedSize(*size)

        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.addWidget(self.add_icon(app_params.icon))
        layout.addWidget(self.add_title(app_params.title))
        layout.addWidget(self.add_version(app_params.version))
        layout.addWidget(self.add_repo_link(app_params.repo_url, app_params.repo_text))
        layout.addStretch()
        layout.addLayout(self.set_close_btn())
        self.setLayout(layout)

    def set_close_btn(self) -> QHBoxLayout:
        btn_layout = QHBoxLayout()
        close_btn = QPushButton("Close")
        close_btn.setFixedWidth(100)
        close_btn.clicked.connect(self.accept)
        btn_layout.addStretch()
        btn_layout.addWidget(close_btn)
        btn_layout.addStretch()
        return btn_layout

    def add_icon(self, icon_path: str) -> QWidget:
        icon_label = QLabel()
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pixmap = QPixmap(icon_path)
        if not pixmap.isNull():
            icon_label.setPixmap(
                pixmap.scaled(
                    80, 80, Qt.KeepAspectRatio, Qt.SmoothTransformation
                )
            )
        else:
            icon_label.setText("📱")
            icon_label.setStyleSheet("font-size: 64px;")
        return icon_label

    def add_title(self, title: str) -> QWidget:
        title_lbl = QLabel(title)
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        return title_lbl

    def add_version(self, version: str) -> QWidget:
        version_lbl = QLabel(version)
        version_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        version_lbl.setStyleSheet("color: #667;")
        return version_lbl

    def add_repo_link(self, repo_link: str, repo_text: str | None = None) -> QLabel:
        ghurl = f"<a href='{repo_link}'>{repo_text or repo_link}</a>"
        gh_lbl = QLabel(ghurl)
        gh_lbl.setOpenExternalLinks(True)
        gh_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        gh_lbl.setTextFormat(Qt.RichText)
        gh_lbl.setTextInteractionFlags(Qt.TextBrowserInteraction)
        return gh_lbl

if __name__ == '__main__':
    APP_NAME = "Flac to Mp3 Converter"
    APP_VERSION = '1.0'
    REPO_URL = 'https://github.com/robertopauletto/soundconverter'
    ICON_PATH = '../soundconverter.png'

    app_params = AboutParams(ICON_PATH, APP_NAME, APP_VERSION, REPO_URL, 'GitHub repo')
    app = QApplication([])
    d = AboutBox(None, app_params)
    d.exec()
    app.exit(-1)