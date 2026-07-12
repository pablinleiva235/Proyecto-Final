from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtWidgets import QWidget, QLabel, QPushButton, QHBoxLayout

from config_gui.strings import APP_TITLE, EXIT_BUTTON_TEXT


class TopBarWidget(QWidget):
    exit_requested = pyqtSignal()

    def __init__(self):
        super().__init__()

        self.create_widgets()
        self.setup_layout()
        self.connect_signals()

    def create_widgets(self):
        # Crea el título global de la aplicación
        self.title_label = QLabel(APP_TITLE)
        self.title_label.setObjectName("TopBarTitle")
        self.title_label.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)

        # Crea el botón global de salida
        self.exit_button = QPushButton(EXIT_BUTTON_TEXT)
        self.exit_button.setObjectName("ExitButton")

        self.setObjectName("TopBar")

    def setup_layout(self):
        # Organiza los elementos de la barra superior
        layout = QHBoxLayout()
        layout.setContentsMargins(24, 12, 24, 12)
        layout.setSpacing(16)

        layout.addWidget(self.title_label)
        layout.addStretch()
        layout.addWidget(self.exit_button)

        self.setLayout(layout)

    def connect_signals(self):
        # Emite una señal sin cerrar directamente la aplicación
        self.exit_button.clicked.connect(self.exit_requested.emit)