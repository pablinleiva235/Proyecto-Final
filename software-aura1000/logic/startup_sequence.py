"""
Secuencia física de pre-encendido del Plasma Asher.

Este módulo contiene únicamente la lógica asociada al arranque físico
del equipo.

Responsabilidades:
- Activar las señales necesarias para iniciar el equipo.
- Inicializar el hardware analógico.
- Controlar el tiempo mínimo de precalentamiento.
- Informar el progreso de la secuencia.
- Informar cuándo la secuencia finaliza correctamente.
- Informar errores ocurridos durante el proceso.

Este módulo no:
- Modifica widgets.
- Cambia pantallas.
- Conoce MainWindow.
- Decide qué texto mostrar al usuario.
"""

from PyQt5.QtCore import QObject, QTimer, pyqtSignal

from config.digital_signals import ACTIVE, INACTIVE


class StartupSequence(QObject):
    """Gestiona la secuencia física de pre-encendido."""

    # Informa que la secuencia física comenzó.
    startup_started = pyqtSignal()

    # Informa el porcentaje de avance de la secuencia.
    progress_changed = pyqtSignal(int)

    # Informa que el pre-encendido terminó correctamente.
    startup_completed = pyqtSignal()

    # Informa un error ocurrido durante la secuencia.
    startup_error = pyqtSignal(str)

    # Tiempo requerido para completar el precalentamiento.
    STARTUP_DURATION_MS =  3_000     #30_000

    # Intervalo utilizado para actualizar el progreso.
    TIMER_INTERVAL_MS = 100

    def __init__(
        self,
        hardware,
        parent=None,
        initialize_analog=False,
    ):
        super().__init__(parent)

        self._hardware = hardware
        self._initialize_analog = bool(initialize_analog)

        self._elapsed_ms = 0
        self._running = False

        self._timer = QTimer(self)
        self._timer.setInterval(
            self.TIMER_INTERVAL_MS
        )

        self._timer.timeout.connect(
            self._update_progress
        )

    # =========================================================================
    # Interfaz pública
    # =========================================================================

    def start(self):
        """Inicia la secuencia física de pre-encendido."""

        if self._running:
            return

        try:
            self._running = True
            self._elapsed_ms = 0

            self.startup_started.emit()
            self.progress_changed.emit(0)

            # Activa la retención de encendido del equipo.
            self._hardware.digital_set(
                "POWER_ON",
                ACTIVE,
            )

            # digital_read devuelve el estado lógico normalizado según
            # active_state, por lo que también funciona con señales activas en bajo.
            if not self._hardware.digital_read("POWER_ON"):
                raise RuntimeError(
                    "La salida POWER_ON no confirmó su activación."
                )

            # La placa analógica física se inicializa al comenzar el arranque.
            # En modo mock, MockHardware gestiona su propio estado inicial.
            if self._initialize_analog:
                self._hardware.initialize_AD()

            # Comienza la temporización del precalentamiento.
            self._timer.start()

        except Exception as error:
            self._handle_error(error)

    def stop(self):
        """Detiene la secuencia de pre-encendido."""

        self._timer.stop()
        self._running = False

    @property
    def is_running(self):
        """Indica si la secuencia se encuentra actualmente en ejecución."""

        return self._running

    # =========================================================================
    # Temporización
    # =========================================================================

    def _update_progress(self):
        """Actualiza el porcentaje según el tiempo transcurrido."""

        self._elapsed_ms += self.TIMER_INTERVAL_MS

        progress = int(
            min(
                100,
                (
                    self._elapsed_ms
                    / self.STARTUP_DURATION_MS
                )
                * 100,
            )
        )

        self.progress_changed.emit(
            progress
        )

        if self._elapsed_ms >= self.STARTUP_DURATION_MS:
            self._complete_startup()

    # =========================================================================
    # Finalización
    # =========================================================================

    def _complete_startup(self):
        """Finaliza correctamente la secuencia de pre-encendido."""

        try:
            self._timer.stop()

            # El contactor ya se encuentra autoretenido.
            # Se libera la salida POWER_ON.
            self._hardware.digital_set(
                "POWER_ON",
                INACTIVE,
            )

            self._running = False

            self.progress_changed.emit(100)
            self.startup_completed.emit()

        except Exception as error:
            self._handle_error(error)

    # =========================================================================
    # Manejo de errores
    # =========================================================================

    def _handle_error(
        self,
        error,
    ):
        """Detiene la secuencia, libera POWER_ON e informa el error."""

        self._timer.stop()
        self._running = False

        message = str(error)
        try:
            self._hardware.digital_set(
                "POWER_ON",
                INACTIVE,
            )
        except Exception as safe_error:
            message = (
                f"{message} No se pudo liberar POWER_ON: {safe_error}"
            )

        self.startup_error.emit(
            message
        )
