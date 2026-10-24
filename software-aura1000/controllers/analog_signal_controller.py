"""
Controlador de monitoreo de señales analógicas.

Responsabilidades:
- Leer periódicamente las señales analógicas configuradas.
- Mantener centralizado el polling de señales analógicas.
- Informar nuevos valores mediante señales Qt.
- Informar errores de lectura.

No modifica widgets ni implementa lógica de secuencias.
"""

from PyQt5.QtCore import QObject, QTimer, pyqtSignal


class AnalogSignalController(QObject):

    # Conversión de voltaje a las unidades que espera la interfaz.
    # Se conserva el escalado del código anterior: 10 V = 10 Torr/SLPM
    # para Baratron y MFC1, y 1 V = 1 SLPM para MFC2.
    ENGINEERING_CONVERSIONS = {
        "BARATRON": (10.0 / 10.0, "Torr"),
        "MFC1_FLOW": (10.0 / 10.0, "SLPM"),
        "MFC2_FLOW": (1.0 / 1.0, "SLPM"),
    }

    signal_value_changed = pyqtSignal(
        str,
        float,
    )

    signal_error = pyqtSignal(
        str,
        str,
    )

    def __init__(
        self,
        hardware,
        monitored_signals,
        poll_interval_ms=100,
        parent=None,
    ):
        super().__init__(parent)

        self._hardware = hardware
        self._monitored_signals = tuple(
            monitored_signals
        )

        self._timer = QTimer(self)
        self._timer.setInterval(
            poll_interval_ms
        )

        self._timer.timeout.connect(
            self._poll_signals
        )

    def start_monitoring(self):
        """Inicia el monitoreo de señales analógicas."""

        if not self._timer.isActive():
            self._poll_signals()
            self._timer.start()

    def stop_monitoring(self):
        """Detiene el monitoreo de señales analógicas."""

        self._timer.stop()

    def _poll_signals(self):
        """Lee las señales analógicas monitoreadas."""

        for signal_name in self._monitored_signals:
            try:
                if signal_name == "CHAMBER_TEMP":
                    value = self._hardware.analog_read_temperature(
                        signal_name
                    )
                else:
                    value = self._hardware.analog_read(signal_name)

                if value is None:
                    raise ValueError("La lectura no está disponible")

                value = float(value)
                if signal_name in self.ENGINEERING_CONVERSIONS:
                    scale, _unit = self.ENGINEERING_CONVERSIONS[signal_name]
                    value = max(0.0, value * scale)

                self.signal_value_changed.emit(
                    signal_name,
                    value,
                )

            except Exception as error:
                self.signal_error.emit(
                    signal_name,
                    str(error),
                )
