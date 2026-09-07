"""
Barra superior persistente de la aplicación.

TopBarWidget muestra información global disponible desde cualquier pantalla.

Responsabilidades:
- Mostrar el nombre de la aplicación.
- Mostrar la fecha actual.
- Mostrar la hora actual.
- Emitir una solicitud para abrir la configuración.
- Emitir una solicitud para cerrar la aplicación.

TopBarWidget no:
- Abre directamente SettingsDialog.
- Cierra directamente la aplicación.
- Controla la navegación.
"""

from PyQt5.QtCore import QDateTime, QTimer, Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QWidget,
)

from config_gui.strings import (
    APP_TITLE,
    EXIT_BUTTON_TEXT,
)


class TopBarWidget(QWidget):
    """Barra superior global de la aplicación."""

    exit_requested = pyqtSignal()
    settings_requested = pyqtSignal()

    DATE_FORMAT = "dd/MM/yyyy"
    TIME_FORMAT = "HH:mm"
    CLOCK_UPDATE_INTERVAL_MS = 1000

    def __init__(self, parent=None):
        super().__init__(parent)

        self.create_widgets()
        self.setup_layout()
        self.connect_signals()

        self._update_datetime()
        self._start_clock()


    def create_widgets(self):
        """Crea los componentes visuales de la barra superior."""

        self.title_label = QLabel(APP_TITLE)
        self.title_label.setObjectName("TopBarTitle")
        self.title_label.setAlignment(
            Qt.AlignVCenter | Qt.AlignLeft
        )

        self.date_label = QLabel()
        self.date_label.setObjectName("TopBarDate")
        self.date_label.setAlignment(Qt.AlignCenter)

        self.time_label = QLabel()
        self.time_label.setObjectName("TopBarTime")
        self.time_label.setAlignment(Qt.AlignCenter)

        self.settings_button = QPushButton("⚙")
        self.settings_button.setObjectName(
            "SettingsButton"
        )
        self.settings_button.setToolTip(
            "Configuración"
        )

        self.exit_button = QPushButton(
            EXIT_BUTTON_TEXT
        )
        self.exit_button.setObjectName(
            "ExitButton"
        )

        self._clock_timer = QTimer(self)
        self._clock_timer.setInterval(
            self.CLOCK_UPDATE_INTERVAL_MS
        )

        self.setObjectName("TopBar")

    def setup_layout(self):
        """Organiza los componentes dentro de la barra superior."""

        layout = QHBoxLayout()
        layout.setContentsMargins(
            24,
            12,
            24,
            12,
        )
        layout.setSpacing(18)

        layout.addWidget(self.title_label)

        layout.addStretch()

        layout.addWidget(self.date_label)
        layout.addWidget(self.time_label)

        layout.addSpacing(10)

        layout.addWidget(
            self.settings_button
        )
        layout.addWidget(
            self.exit_button
        )

        self.setLayout(layout)

    def connect_signals(self):
        """Conecta los eventos internos de la barra superior."""

        self.exit_button.clicked.connect(
            self.exit_requested.emit
        )

        self.settings_button.clicked.connect(
            self.settings_requested.emit
        )

        self._clock_timer.timeout.connect(
            self._update_datetime
        )

    # =========================================================================
    # Fecha y hora
    # =========================================================================

    def _start_clock(self):
        """Inicia la actualización periódica de fecha y hora."""

        if not self._clock_timer.isActive():
            self._clock_timer.start()

    def _update_datetime(self):
        """Actualiza la fecha y hora utilizando el reloj del sistema."""

        current_datetime = QDateTime.currentDateTime()

        self.date_label.setText(
            current_datetime.toString(
                self.DATE_FORMAT
            )
        )

        self.time_label.setText(
            current_datetime.toString(
                self.TIME_FORMAT
            )
        )