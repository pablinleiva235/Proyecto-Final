"""
Controlador de la secuencia de arranque del Plasma Asher.

StartupController supervisa el estado de encendido del equipo y coordina
la ejecución de StartupSequence.

Responsabilidades:
- Esperar la activación física de POWER_ON_SWITCH.
- Iniciar StartupSequence cuando corresponda.
- Reenviar el progreso de la secuencia hacia la interfaz.
- Informar cuándo el arranque finalizó correctamente.
- Informar errores ocurridos durante la espera o durante la secuencia.

StartupController no:
- Modifica widgets.
- Abre MainWindow.
- Ejecuta directamente la secuencia física de encendido.
- Conoce puertos, bits o polaridades eléctricas.
- Accede directamente al driver.

La interacción con el hardware se realiza mediante Hardware.digital_read().
"""

from enum import Enum
from typing import Optional

from PyQt5.QtCore import QObject, QTimer, pyqtSignal


class StartupState(Enum):
    """Estados posibles durante el arranque de la aplicación."""

    WAITING_POWER = "waiting_power"
    STARTING = "starting"
    READY = "ready"
    ERROR = "error"


class StartupController(QObject):
    """Supervisa y coordina la secuencia de arranque del equipo."""

    # Informa cambios en el estado general del arranque.
    state_changed = pyqtSignal(object)

    # Reenvía el progreso generado por StartupSequence.
    progress_changed = pyqtSignal(int)

    # Informa que el equipo terminó correctamente la secuencia de inicio.
    startup_ready = pyqtSignal()

    # Informa un error durante la secuencia.
    startup_error = pyqtSignal(str)

    POWER_SWITCH_SIGNAL = "POWER_ON_SWITCH"
    POWER_POLL_INTERVAL_MS = 100

    def __init__(
        self,
        hardware,
        startup_sequence,
        parent: Optional[QObject] = None,
    ) -> None:
        super().__init__(parent)

        self._hardware = hardware
        self._startup_sequence = startup_sequence

        self._state = StartupState.WAITING_POWER
        self._running = False

        self._power_timer = QTimer(self)
        self._power_timer.setInterval(
            self.POWER_POLL_INTERVAL_MS
        )

        self._connect_signals()

    # =========================================================================
    # Interfaz pública
    # =========================================================================

    def start(self) -> None:
        """Inicia la supervisión del arranque.

        El controlador comienza esperando la activación física de
        POWER_ON_SWITCH.
        """

        if self._running:
            return

        self._running = True

        self._set_state(
            StartupState.WAITING_POWER
        )

        self.progress_changed.emit(0)

        self._power_timer.start()

    def stop(self) -> None:
        """Detiene la supervisión y la secuencia de arranque."""

        self._power_timer.stop()

        if self._startup_sequence.is_running:
            self._startup_sequence.stop()

        self._running = False

    def reset(self) -> None:
        """Reinicia el controlador al estado inicial."""

        self.stop()

        self._set_state(
            StartupState.WAITING_POWER
        )

        self.progress_changed.emit(0)

    @property
    def state(self) -> StartupState:
        """Devuelve el estado actual del arranque."""

        return self._state

    @property
    def is_running(self) -> bool:
        """Indica si el controlador está supervisando el arranque."""

        return self._running

    # =========================================================================
    # Conexiones internas
    # =========================================================================

    def _connect_signals(self) -> None:
        """Conecta temporizadores y eventos de StartupSequence."""

        self._power_timer.timeout.connect(
            self._check_power_switch
        )

        self._startup_sequence.progress_changed.connect(
            self._handle_progress_changed
        )

        self._startup_sequence.startup_completed.connect(
            self._handle_startup_completed
        )

        self._startup_sequence.startup_error.connect(
            self._handle_startup_error
        )

    # =========================================================================
    # Supervisión de POWER_ON_SWITCH
    # =========================================================================

    def _check_power_switch(self) -> None:
        """Lee POWER_ON_SWITCH mientras se espera el encendido."""

        if self._state != StartupState.WAITING_POWER:
            return

        try:
            power_switch_active = self._hardware.digital_read(
                self.POWER_SWITCH_SIGNAL
            )

        except Exception as error:
            self._handle_startup_error(
                self._format_error(
                    "No fue posible leer POWER_ON_SWITCH",
                    error,
                )
            )
            return

        if power_switch_active:
            self._begin_startup_sequence()

    def _begin_startup_sequence(self) -> None:
        """Detiene la espera y comienza la secuencia física."""

        if self._state != StartupState.WAITING_POWER:
            return

        self._power_timer.stop()

        self._set_state(
            StartupState.STARTING
        )

        try:
            self._startup_sequence.start()

        except Exception as error:
            self._handle_startup_error(
                self._format_error(
                    "No fue posible iniciar la secuencia de encendido",
                    error,
                )
            )

    # =========================================================================
    # Eventos provenientes de StartupSequence
    # =========================================================================

    def _handle_progress_changed(
        self,
        progress: int,
    ) -> None:
        """Reenvía el progreso de la secuencia hacia la GUI."""

        if self._state != StartupState.STARTING:
            return

        self.progress_changed.emit(progress)

    def _handle_startup_completed(self) -> None:
        """Finaliza correctamente la supervisión del arranque."""

        self._running = False

        self._set_state(
            StartupState.READY
        )

        self.progress_changed.emit(100)

        self.startup_ready.emit()

    def _handle_startup_error(
        self,
        message: str,
    ) -> None:
        """Gestiona un error ocurrido durante el arranque."""

        self._power_timer.stop()

        if self._startup_sequence.is_running:
            self._startup_sequence.stop()

        self._running = False

        self._set_state(
            StartupState.ERROR
        )

        self.startup_error.emit(message)

    # =========================================================================
    # Gestión de estado
    # =========================================================================

    def _set_state(
        self,
        state: StartupState,
    ) -> None:
        """Actualiza y comunica el estado general del arranque."""

        if self._state == state:
            return

        self._state = state

        self.state_changed.emit(state)

    # =========================================================================
    # Utilidades
    # =========================================================================

    @staticmethod
    def _format_error(
        context: str,
        error: Exception,
    ) -> str:
        """Construye un mensaje legible a partir de una excepción."""

        detail = str(error).strip()

        if detail:
            return f"{context}: {detail}"

        return context