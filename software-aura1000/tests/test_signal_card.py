"""
Prueba visual de SignalWidget.

Este archivo permite validar de forma aislada el funcionamiento del widget
antes de integrarlo con MaintainerScreen y SignalController.

Verifica:

- Estados ACTIVE, INACTIVE y PROCESSING.
- Widgets interactivos y de solo lectura.
- Emisión de toggle_requested.
- Aplicación del APP_STYLE.
"""

import sys

from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
)

from config_gui.theme import APP_STYLE
from gui.widgets.signal_widget import SignalWidget


class SignalWidgetTestWindow(QWidget):
    """Ventana temporal para probar SignalWidget."""

    def __init__(self):
        super().__init__()

        self._click_counter = 0

        self.create_widgets()
        self.setup_layout()
        self.connect_signals()

        self.setWindowTitle("SignalWidget Test")
        self.resize(900, 500)

    
    def create_widgets(self):
        """Crea los widgets de prueba."""

        self.output_widget = SignalWidget(
            signal_name="POWER_ON",
            interactive=True,
        )

        self.input_widget = SignalWidget(
            signal_name="SYS_POWER",
            interactive=False,
        )

        self.info_label = QLabel(
            "Esperando interacción..."
        )

        self.active_button = QPushButton("ACTIVE")
        self.inactive_button = QPushButton("INACTIVE")
        self.processing_button = QPushButton("PROCESSING")

    def setup_layout(self):
        """Organiza los widgets."""

        signal_layout = QHBoxLayout()

        signal_layout.addWidget(self.output_widget)
        signal_layout.addWidget(self.input_widget)

        buttons_layout = QHBoxLayout()

        buttons_layout.addWidget(self.active_button)
        buttons_layout.addWidget(self.inactive_button)
        buttons_layout.addWidget(self.processing_button)

        main_layout = QVBoxLayout(self)

        main_layout.addLayout(signal_layout)
        main_layout.addSpacing(20)
        main_layout.addWidget(self.info_label)
        main_layout.addSpacing(20)
        main_layout.addLayout(buttons_layout)

    def connect_signals(self):
        """Conecta señales."""

        self.output_widget.toggle_requested.connect(
            self.on_toggle_requested
        )

        self.input_widget.toggle_requested.connect(
            self.on_toggle_requested
        )

        self.active_button.clicked.connect(
            self.set_active_state
        )

        self.inactive_button.clicked.connect(
            self.set_inactive_state
        )

        self.processing_button.clicked.connect(
            self.set_processing_state
        )

    # ==========================================================
    # Slots
    # ==========================================================

    def on_toggle_requested(self, signal_name):
        """Recibe la solicitud emitida por SignalWidget."""

        self._click_counter += 1

        self.info_label.setText(
            f"Solicitud #{self._click_counter}: {signal_name}"
        )

    def set_active_state(self):
        """Muestra ambos widgets en ACTIVE."""

        self.output_widget.set_active(True)
        self.input_widget.set_active(True)

    def set_inactive_state(self):
        """Muestra ambos widgets en INACTIVE."""

        self.output_widget.set_active(False)
        self.input_widget.set_active(False)

    def set_processing_state(self):
        """Muestra ambos widgets en PROCESSING."""

        self.output_widget.set_processing()
        self.input_widget.set_processing()


def main():
    app = QApplication(sys.argv)

    app.setStyleSheet(APP_STYLE)

    window = SignalWidgetTestWindow()
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()