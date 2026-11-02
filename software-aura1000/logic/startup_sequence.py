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
        self._throttle_controller = None

        self._elapsed_ms = 0
        self._running = False
        self._preheat_complete = False
        self._throttle_homing_complete = False

        self._timer = QTimer(self)
        self._timer.setInterval(
            self.TIMER_INTERVAL_MS
        )

        self._timer.timeout.connect(
            self._update_progress
        )

    def set_throttle_controller(self, throttle_controller):
        """Attach the throttle controller after MainWindow creates it."""
        if self._running:
            raise RuntimeError("No se puede cambiar el throttle durante el startup.")
        if self._throttle_controller is throttle_controller:
            return
        if self._throttle_controller is not None:
            self._throttle_controller.startup_homing_completed.disconnect(
                self._handle_throttle_homing_completed
            )
            self._throttle_controller.startup_homing_failed.disconnect(
                self._handle_throttle_homing_failed
            )
        self._throttle_controller = throttle_controller
        if throttle_controller is not None:
            throttle_controller.startup_homing_completed.connect(
                self._handle_throttle_homing_completed
            )
            throttle_controller.startup_homing_failed.connect(
                self._handle_throttle_homing_failed
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
            self._preheat_complete = False
            self._throttle_homing_complete = False

            self.startup_started.emit()
            self.progress_changed.emit(0)

            # Activa la retención de encendido del equipo.
            self._hardware.digital_set(
                "POWER_ON",
                ACTIVE,
            )

            if not self._hardware.digital_read("POWER_ON"):
                raise RuntimeError("POWER_ON no confirmÃ³ su activaciÃ³n.")

            self._hardware.digital_set("FILAMENT_ENABLE", ACTIVE)
            if not self._hardware.digital_read("FILAMENT_ENABLE"):
                raise RuntimeError("FILAMENT_ENABLE no confirmÃ³ su activaciÃ³n.")

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

            if self._throttle_controller is None:
                raise RuntimeError("No se configurÃ³ el controlador de throttle.")
            self._throttle_controller.home_on_startup()

            # Comienza la temporización del precalentamiento.
            self._timer.start()

        except Exception as error:
            self._handle_error(error)

    def stop(self):
        """Detiene la secuencia de pre-encendido."""

        if self._running:
            self._handle_error(RuntimeError("La secuencia de startup fue detenida."))

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
            self._preheat_complete = True
            self._timer.stop()
            self._try_complete_startup()

    def _handle_throttle_homing_completed(self):
        if not self._running:
            return
        self._throttle_homing_complete = True
        self._try_complete_startup()

    def _handle_throttle_homing_failed(self, message):
        if self._running:
            self._handle_error(RuntimeError(f"Fallo el homing del throttle: {message}"))

    def _try_complete_startup(self):
        if self._running and self._preheat_complete and self._throttle_homing_complete:
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
        if self._throttle_controller is not None:
            try:
                cleanup_error = self._throttle_controller.stop_startup_homing()
                if cleanup_error:
                    message += (
                        f" No se pudo dejar el driver de throttle inactivo: {cleanup_error}"
                    )
            except Exception as throttle_error:
                message += f" No se pudo detener el throttle: {throttle_error}"
        for signal_name in ("POWER_ON", "FILAMENT_ENABLE"):
            try:
                self._hardware.digital_set(signal_name, INACTIVE)
            except Exception as safe_error:
                message += f" No se pudo desactivar {signal_name}: {safe_error}"

        self.startup_error.emit(
            message
        )
