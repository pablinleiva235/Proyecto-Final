from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtWidgets import QWidget, QLabel, QPushButton, QVBoxLayout

from config.strings import (
    STATISTICS_TITLE,
    STATISTICS_PLACEHOLDER,
    BACK_BUTTON_TEXT,
)


class StatisticsScreen(QWidget):
    back_requested = pyqtSignal()

    def __init__(self):
        super().__init__()

        self.create_widgets()
        self.setup_layout()
        self.connect_signals()

    def create_widgets(self):
        self.title_label = QLabel(STATISTICS_TITLE)
        self.title_label.setObjectName("TitleLabel")
        self.title_label.setAlignment(Qt.AlignCenter)

        self.subtitle_label = QLabel(STATISTICS_PLACEHOLDER)
        self.subtitle_label.setObjectName("SubtitleLabel")
        self.subtitle_label.setAlignment(Qt.AlignCenter)

        self.back_button = QPushButton(BACK_BUTTON_TEXT)

    def setup_layout(self):
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(30)

        layout.addWidget(self.title_label)
        layout.addWidget(self.subtitle_label)
        layout.addSpacing(60)
        layout.addWidget(self.back_button)

        self.setLayout(layout)

    def connect_signals(self):
        self.back_button.clicked.connect(
            self.back_requested.emit
        )