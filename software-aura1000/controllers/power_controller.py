"""
Controlador de monitoreo de las señales físicas
de alimentación del equipo.

Responsabilidades:
- Monitorear las entradas físicas de alimentación.
- Detectar solicitudes de encendido y apagado.
- Emitir eventos hacia el ciclo de vida de la aplicación.

No ejecuta secuencias de startup ni shutdown.
"""

from PyQt5.QtCore import QObject, QTimer, pyqtSignal


POWER_MONITOR_INTERVAL_MS = 100



class PowerController(QObject):

    startup_requested = pyqtSignal()
    shutdown_requested = pyqtSignal()

    def __init__(
        self,
        hardware,
        parent=None,
    ):
        super().__init__(parent)

        self._hardware = hardware

        self._timer = QTimer(self)
        self._timer.setInterval(
            POWER_MONITOR_INTERVAL_MS
        )
        self._timer.timeout.connect(
            self._poll_power_signals
        )

        self._monitor_startup = False
        self._monitor_shutdown = False

    def start_startup_monitoring(self):
        """
        Inicia el monitoreo de la solicitud física
        de encendido.
        """
        self._monitor_startup = True
        self._monitor_shutdown = False

        if not self._timer.isActive():
            self._timer.start()

    def start_shutdown_monitoring(self):
        """
        Inicia el monitoreo de la solicitud física
        de apagado.
        """
        self._monitor_startup = False
        self._monitor_shutdown = True

        if not self._timer.isActive():
            self._timer.start()

    def stop(self):
        # Detiene el monitoreo de alimentación.

        self._timer.stop()

        self._monitor_startup = False
        self._monitor_shutdown = False

    def _poll_power_signals(self):
        if self._monitor_startup:
            self._check_startup_request()

        elif self._monitor_shutdown:
            self._check_shutdown_request()

    def _check_startup_request(self):
        try:
            startup_requested = (
                self._hardware.digital_read(
                    "POWER_ON_SWITCH"
                )
            )

        except Exception as error:
            print(
                "[PowerController] "
                "Error leyendo POWER_ON_SWITCH: {error}"
            )
            return

        if not startup_requested:
            return

        self._timer.stop()
        self._monitor_startup = False
        print(
            "[PowerController] "
            "Solicitud de encendido detectada."
        )
        self.startup_requested.emit()

    def _check_shutdown_request(self):
        try:
            shutdown_requested = (
                self._hardware.digital_read(
                    "SYS_POWER"
                )
            )

        except Exception as error:
            print(
                "[PowerController] "
                "Error leyendo SYS_POWER: {error}"
            )
            return

        if not shutdown_requested:
            return

        self._timer.stop()
        self._monitor_shutdown = False

        self.shutdown_requested.emit()