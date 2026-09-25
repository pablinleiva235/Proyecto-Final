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
            self._timer.start()

    def stop_monitoring(self):
        """Detiene el monitoreo de señales analógicas."""

        self._timer.stop()

    def _poll_signals(self):
        """Lee las señales analógicas monitoreadas."""

        for signal_name in self._monitored_signals:
            try:
                value = self._hardware.analog_read(
                    signal_name
                )

                self.signal_value_changed.emit(
                    signal_name,
                    float(value),
                )

            except Exception as error:
                self.signal_error.emit(
                    signal_name,
                    str(error),
                )
                