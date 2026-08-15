"""
Prueba aislada de SignalController utilizando MockHardware.

Permite verificar:

- Polling periódico.
- Lectura de señales.
- Solicitudes de toggle.
- Estado PROCESSING.
- Confirmación posterior de la salida.
"""

import sys

from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QApplication

from config_gui.maintainer_signals import MAINTAINER_SIGNALS
from controllers.signal_controller import SignalController
from tests.mockScripts.mock_hardware import MockHardware


OUTPUT_SIGNALS = (
    "POWER_ON",
    "DRIVER_ENABLE",
)


class SignalControllerTest:
    """Conecta las señales del controlador con mensajes de consola."""

    def __init__(self):
        self.hardware = MockHardware()

        self.controller = SignalController(
            hardware=self.hardware,
            monitored_signals=MAINTAINER_SIGNALS,
            output_signals=OUTPUT_SIGNALS,
            poll_interval_ms=1000,
        )

        self.connect_signals()

    def connect_signals(self):
        self.controller.signal_state_changed.connect(
            self.on_state_changed
        )

        self.controller.signal_processing.connect(
            self.on_processing
        )

        self.controller.signal_error.connect(
            self.on_error
        )

    def start(self):
        print("\n")
        print("=== Iniciando monitoreo ===")
        print("\n")

        self.controller.start_monitoring()

        # Después de 2 segundos se solicita activar POWER_ON.
        QTimer.singleShot(
            2000,
            self.toggle_power_on,
        )

        # Después de 4 segundos se solicita activar DRIVER_ENABLE.
        QTimer.singleShot(
            4000,
            self.toggle_driver_enable,
        )

        # Después de 6 segundos se solicita nuevamente POWER_ON.
        QTimer.singleShot(
            6000,
            self.toggle_power_on,
        )

    def toggle_power_on(self):
        print()
        print(">>> Toggle solicitado: POWER_ON")

        self.controller.request_toggle(
            "POWER_ON"
        )

    def toggle_driver_enable(self):
        print()
        print(">>> Toggle solicitado: DRIVER_ENABLE")

        self.controller.request_toggle(
            "DRIVER_ENABLE"
        )

    def on_state_changed(
        self,
        signal_name,
        active,
    ):
        print(
            f"[SignalController] STATE "
            f"{signal_name}: {active}"
        )

    def on_processing(
        self,
        signal_name,
    ):
        print(
            f"[SignalController] PROCESSING "
            f"{signal_name}"
        )

    def on_error(
        self,
        signal_name,
        message,
    ):
        print(
            f"[SignalController] ERROR "
            f"{signal_name}: {message}"
        )


def main():
    app = QApplication(sys.argv)

    test = SignalControllerTest()
    test.start()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()