from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtWidgets import (
    QWidget,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QMessageBox,
)

from config_gui.strings import (
    WELCOME_TITLE,
    APP_SUBTITLE,
    NORMAL_OPERATION_BUTTON_TEXT,
    MAINTAINER_BUTTON_TEXT,
    STATISTICS_BUTTON_TEXT,
    NORMAL_OPERATION_NOT_IMPLEMENTED_TITLE,
    NORMAL_OPERATION_NOT_IMPLEMENTED_MESSAGE,
)


class WelcomeScreen(QWidget):
    maintainer_requested = pyqtSignal()
    statistics_requested = pyqtSignal()

    def __init__(self):
        super().__init__()

        self.create_widgets()
        self.setup_layout()
        self.connect_signals()

    def create_widgets(self):
        self.title_label = QLabel(WELCOME_TITLE)
        self.title_label.setObjectName("TitleLabel")
        self.title_label.setAlignment(Qt.AlignCenter)

        self.subtitle_label = QLabel(APP_SUBTITLE)
        self.subtitle_label.setObjectName("SubtitleLabel")
        self.subtitle_label.setAlignment(Qt.AlignCenter)

        self.normal_button = QPushButton(
            NORMAL_OPERATION_BUTTON_TEXT
        )
        self.maintainer_button = QPushButton(
            MAINTAINER_BUTTON_TEXT
        )
        self.statistics_button = QPushButton(
            STATISTICS_BUTTON_TEXT
        )

    def setup_layout(self):
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(30)

        layout.addWidget(self.title_label)
        layout.addWidget(self.subtitle_label)
        layout.addSpacing(60)
        layout.addWidget(self.normal_button)
        layout.addWidget(self.maintainer_button)
        layout.addWidget(self.statistics_button)

        self.setLayout(layout)

    def connect_signals(self):
        self.normal_button.clicked.connect(
            self._show_not_implemented_message
        )
        self.maintainer_button.clicked.connect(
            self.maintainer_requested.emit
        )
        self.statistics_button.clicked.connect(
            self.statistics_requested.emit
        )

    def _show_not_implemented_message(self):
        QMessageBox.information(
            self,
            NORMAL_OPERATION_NOT_IMPLEMENTED_TITLE,
            NORMAL_OPERATION_NOT_IMPLEMENTED_MESSAGE,
        )