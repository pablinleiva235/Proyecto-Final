"""
Pantalla visual utilizada durante el inicio del Plasma Asher.

StartupScreen representa el estado de la secuencia de pre-encendido.

Responsabilidades:
- Informar al usuario que debe presionar el botón de encendido.
- Mostrar que la secuencia de inicio está en ejecución.
- Mostrar el progreso de la secuencia.
- Mostrar un error de inicio cuando corresponda.

StartupScreen no:
- Accede al hardware.
- Inicia ni controla la secuencia de encendido.
- Decide cuándo mostrar MainWindow.
- Modifica señales físicas del equipo.

Los cambios visuales son solicitados desde una capa externa mediante
los métodos públicos de esta clase.
"""

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QLabel,
    QProgressBar,
    QVBoxLayout,
    QWidget,
)

from config_gui.strings import (
    STARTUP_ERROR_MESSAGE,
    STARTUP_RUNNING_MESSAGE,
    STARTUP_TITLE,
    STARTUP_WAITING_MESSAGE,
)


class StartupScreen(QWidget):
    """Pantalla mostrada durante la secuencia de inicio del equipo."""

    def __init__(self, parent=None):
        super().__init__(parent)

        self.create_widgets()
        self.setup_layout()
        self.connect_signals()

        self.show_waiting_for_power()

    def create_widgets(self):
        """Crea los elementos visuales de la pantalla."""

        self.title_label = QLabel(STARTUP_TITLE)
        self.title_label.setObjectName("StartupTitleLabel")
        self.title_label.setAlignment(Qt.AlignCenter)

        self.message_label = QLabel()
        self.message_label.setObjectName("StartupMessageLabel")
        self.message_label.setAlignment(Qt.AlignCenter)
        self.message_label.setWordWrap(True)

        self.progress_bar = QProgressBar()
        self.progress_bar.setObjectName("StartupProgressBar")
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)

        self.error_label = QLabel()
        self.error_label.setObjectName("StartupErrorLabel")
        self.error_label.setAlignment(Qt.AlignCenter)
        self.error_label.setWordWrap(True)
        self.error_label.hide()

    def setup_layout(self):
        """Organiza los elementos dentro de la pantalla."""

        layout = QVBoxLayout(self)

        layout.setContentsMargins(
            120,
            80,
            120,
            80,
        )

        layout.setSpacing(30)

        layout.addStretch()

        layout.addWidget(self.title_label)

        layout.addSpacing(40)

        layout.addWidget(self.message_label)

        layout.addSpacing(20)

        layout.addWidget(self.progress_bar)

        layout.addWidget(self.error_label)

        layout.addStretch()

    def connect_signals(self):
        """Conecta señales internas.

        StartupScreen actualmente no genera eventos propios.
        """

        pass

    # =========================================================================
    # Interfaz pública
    # =========================================================================

    def show_waiting_for_power(self):
        """Muestra el estado inicial de espera del botón de encendido."""

        self.message_label.setText(
            STARTUP_WAITING_MESSAGE
        )

        self.progress_bar.setValue(0)
        self.progress_bar.hide()

        self.error_label.hide()

    def show_starting(self):
        """Muestra que la secuencia de inicio comenzó."""

        self.message_label.setText(
            STARTUP_RUNNING_MESSAGE
        )

        self.progress_bar.setValue(0)
        self.progress_bar.show()

        self.error_label.hide()

    def set_progress(self, progress):
        """Actualiza el porcentaje mostrado en la barra de progreso."""

        if not isinstance(progress, int):
            raise TypeError(
                "'progress' debe ser un valor entero."
            )

        if not 0 <= progress <= 100:
            raise ValueError(
                "'progress' debe estar entre 0 y 100."
            )

        self.progress_bar.setValue(progress)

    def show_error(self, message=None):
        """Muestra un error ocurrido durante la secuencia de inicio."""

        if message:
            error_text = (
                f"{STARTUP_ERROR_MESSAGE}\n{message}"
            )
        else:
            error_text = STARTUP_ERROR_MESSAGE

        self.error_label.setText(error_text)
        self.error_label.show()

        self.progress_bar.hide()